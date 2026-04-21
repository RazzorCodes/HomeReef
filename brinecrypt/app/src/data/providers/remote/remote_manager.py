"""
RemoteManager - HTTP-based resource fetching with periodic sync

This manager fetches resources from remote HTTP endpoints and syncs them
to the database on a timer. It handles HTTP errors appropriately and
provides retry logic for transient failures.
"""

import threading
from datetime import datetime
from typing import Callable, Optional

import requests
from requests.exceptions import RequestException

from data.model.data_object import DataObjectSync
from misc.logger import logger


class RemoteResource:
    """Represents a remote resource being monitored"""

    def __init__(
        self,
        url: str,
        tags: list[str],
        interval: int = 300,
        name: Optional[str] = None,
    ):
        """
        Initialize a remote resource.

        Args:
            url: HTTP(S) URL to fetch
            tags: Tags to associate with this resource
            interval: Sync interval in seconds (default: 300 = 5 minutes)
            name: Optional name for the resource (defaults to URL hash)
        """
        self.url = url
        self.tags = tags.copy()
        self.interval = interval
        self.name = name or self._hash_url(url)
        self.last_sync = datetime.fromtimestamp(0)
        self.last_data: Optional[str] = None
        self.last_error: Optional[str] = None
        self.consecutive_failures = 0
        self.active = True

    @staticmethod
    def _hash_url(url: str) -> str:
        """Generate unique identifier from URL"""
        import hashlib

        return hashlib.md5(url.encode("utf-8")).hexdigest()


class RemoteManager:
    """
    Manages remote HTTP resources with periodic syncing.

    Fetches resources from HTTP endpoints on a timer and syncs changes
    to the database via callback mechanism.
    """

    def __init__(
        self,
        on_data_change: Optional[Callable[[str, DataObjectSync], None]] = None,
        default_interval: int = 300,
        request_timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize RemoteManager.

        Args:
            on_data_change: Callback invoked when resource data changes.
                           Receives (url, DataObject) as arguments.
            default_interval: Default sync interval in seconds (default: 300)
            request_timeout: HTTP request timeout in seconds (default: 30)
            max_retries: Maximum consecutive failures before marking inactive (default: 3)
        """
        logger.trace("Initializing RemoteManager")

        self.on_data_change = on_data_change
        self.default_interval = default_interval
        self.request_timeout = request_timeout
        self.max_retries = max_retries

        self._resources: dict[str, RemoteResource] = {}
        self._sync_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        # Start sync thread
        self._start_sync_thread()

        logger.info("RemoteManager initialized and started")

    def watch(
        self, name: str, url: str, tags: list[str], interval: Optional[int] = None
    ) -> Optional[str]:
        """
        Start watching a remote resource.

        Args:
            url: HTTP(S) URL to fetch
            tags: Tags to associate with this resource
            interval: Sync interval in seconds (None = use default)

        Returns:
            Resource identifier if successful, None if invalid URL
        """
        logger.trace(f"New watch request: {url}")

        # Validate URL
        if not url or not url.startswith(("http://", "https://")):
            logger.warning(f"Invalid URL: {url}")
            return None

        # Create resource
        resource = RemoteResource(
            url=url,
            tags=tags,
            interval=interval or self.default_interval,
        )

        with self._lock:
            self._resources[resource.name] = resource

        logger.info(f"Added remote resource: {url} (interval: {resource.interval}s)")

        # Perform initial sync
        self._sync_resource(resource)

        return resource.name

    def unwatch(self, resource_id: str) -> bool:
        """
        Stop watching a remote resource.

        Args:
            resource_id: Resource identifier

        Returns:
            True if resource was removed, False if not found
        """
        with self._lock:
            if resource_id in self._resources:
                self._resources[resource_id].active = False
                del self._resources[resource_id]
                logger.info(f"Removed remote resource: {resource_id}")
                return True
            return False

    def _sync_resource(self, resource: RemoteResource) -> bool:
        """
        Sync a single resource from its remote URL.

        Args:
            resource: RemoteResource to sync

        Returns:
            True if sync successful, False otherwise
        """
        logger.debug(f"Syncing remote resource: {resource.url}")

        try:
            # Perform HTTP GET
            response = requests.get(resource.url, timeout=self.request_timeout)

            # Handle HTTP status codes
            if response.status_code == 200:
                # Success
                data = response.text
                resource.last_sync = datetime.now()
                resource.consecutive_failures = 0
                resource.last_error = None

                # Check if data changed
                if data != resource.last_data:
                    logger.info(f"Remote resource changed: {resource.url}")
                    resource.last_data = data

                    # Create DataObject
                    data_obj = DataObjectSync(
                        name=resource.name,
                        tags=resource.tags + ["remote", "http"],
                        data=data,
                        created_at=datetime.now(),
                        path=resource.url,
                        sync=True,
                        last_update=datetime.now(),
                    )

                    # Trigger callback
                    if self.on_data_change:
                        try:
                            self.on_data_change(resource.url, data_obj)
                        except Exception as e:
                            logger.error(f"Callback failed for {resource.url}: {e}")
                else:
                    logger.trace(f"Remote resource unchanged: {resource.url}")

                return True

            elif 400 <= response.status_code < 500:
                # Client error - don't retry aggressively
                error_msg = f"Client error {response.status_code} for {resource.url}"
                logger.warning(error_msg)
                resource.last_error = error_msg
                resource.consecutive_failures += 1

                if response.status_code == 404:
                    logger.error(f"Resource not found (404): {resource.url}")
                elif response.status_code == 401 or response.status_code == 403:
                    logger.error(f"Authentication/authorization error: {resource.url}")

                return False

            elif 500 <= response.status_code < 600:
                # Server error - retry with backoff
                error_msg = f"Server error {response.status_code} for {resource.url}"
                logger.warning(error_msg)
                resource.last_error = error_msg
                resource.consecutive_failures += 1
                return False

            else:
                # Unexpected status code
                error_msg = (
                    f"Unexpected status {response.status_code} for {resource.url}"
                )
                logger.warning(error_msg)
                resource.last_error = error_msg
                resource.consecutive_failures += 1
                return False

        except RequestException as e:
            # Network/timeout error
            error_msg = f"Request failed for {resource.url}: {e}"
            logger.warning(error_msg)
            resource.last_error = error_msg
            resource.consecutive_failures += 1
            return False

        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error syncing {resource.url}: {e}"
            logger.error(error_msg)
            resource.last_error = error_msg
            resource.consecutive_failures += 1
            return False

    def _sync_loop(self):
        """Background thread that syncs resources on their intervals"""
        logger.debug("RemoteManager sync thread started")

        while not self._stop_event.is_set():
            try:
                current_time = datetime.now()

                with self._lock:
                    resources_to_sync = list(self._resources.values())

                for resource in resources_to_sync:
                    if not resource.active:
                        continue

                    # Check if it's time to sync
                    time_since_last = (
                        current_time - resource.last_sync
                    ).total_seconds()

                    if time_since_last >= resource.interval:
                        # Check if resource has too many consecutive failures
                        if resource.consecutive_failures >= self.max_retries:
                            logger.error(
                                f"Resource {resource.url} exceeded max retries ({self.max_retries}), "
                                f"marking inactive"
                            )
                            resource.active = False
                            continue

                        # Sync the resource
                        self._sync_resource(resource)

                # Sleep for a bit before next check (check every 10 seconds)
                self._stop_event.wait(10)

            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                self._stop_event.wait(10)

        logger.debug("RemoteManager sync thread stopped")

    def _start_sync_thread(self):
        """Start the background sync thread"""
        if self._sync_thread is None or not self._sync_thread.is_alive():
            self._stop_event.clear()
            self._sync_thread = threading.Thread(
                target=self._sync_loop, daemon=True, name="RemoteManager-SyncThread"
            )
            self._sync_thread.start()
            logger.debug("Started RemoteManager sync thread")

    def stop(self):
        """Stop the remote manager and cleanup resources"""
        logger.info("Stopping RemoteManager")
        self._stop_event.set()

        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=5)

        with self._lock:
            self._resources.clear()

        logger.info("RemoteManager stopped")

    def get_resource_status(self, resource_id: str) -> Optional[dict]:
        """
        Get status information for a resource.

        Args:
            resource_id: Resource identifier

        Returns:
            Dictionary with status information, or None if not found
        """
        with self._lock:
            resource = self._resources.get(resource_id)
            if not resource:
                return None

            return {
                "url": resource.url,
                "name": resource.name,
                "tags": resource.tags,
                "interval": resource.interval,
                "last_sync": resource.last_sync.isoformat()
                if resource.last_sync
                else None,
                "last_error": resource.last_error,
                "consecutive_failures": resource.consecutive_failures,
                "active": resource.active,
            }

    def get_all_resources(self) -> list[dict]:
        """
        Get status for all watched resources.

        Returns:
            List of resource status dictionaries
        """
        with self._lock:
            resource_ids = list(self._resources.keys())

        # Get status outside the lock to avoid deadlock
        return [self.get_resource_status(res_id) for res_id in resource_ids]
