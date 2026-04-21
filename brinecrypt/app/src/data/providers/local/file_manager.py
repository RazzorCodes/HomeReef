import hashlib
import os
from datetime import datetime
from typing import Callable, Optional

from watchdog.events import DirModifiedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from data.model.data_object import DataObjectSync
from misc.logger import logger


# --------------------------
# File Watchdog
# --------------------------
class FileManager(FileSystemEventHandler):
    __data_objects: dict[str, DataObjectSync] = dict()

    def __init__(
        self,
        on_file_change: Optional[Callable[[DataObjectSync], None]] = None,
    ):
        """
        Initialize FileManager with optional callback for file changes.

        Args:
            files_to_watch: List of file paths to watch initially
            on_file_change: Optional callback function invoked when a file changes.
                           Receives the updated DataObjectSync as argument.
        """
        super().__init__()
        logger.trace("Initializing file watchdog")

        self.on_file_change = on_file_change
        self.observer = Observer()
        self.observer.start()

        logger.info("File watchdog initialized and started")

    def watch(self, name: str, path: str, tags: list[str]) -> DataObjectSync | None:
        """
        Start watching a file for changes.

        Args:
            path: File path to watch
            tags: Tags to associate with this file

        Returns:
            DataObjectSync if successful, None if path invalid
        """
        logger.trace(f"New watch request: {path}")

        # Check if path is empty or contains null bytes
        if not path or "\x00" in path:
            logger.warning(f"Requested path invalid (empty or null bytes): {path}")
            return None

        # Check if path exists
        if not os.path.exists(path):
            logger.warning(f"Requested path invalid (does not exist): {path}")
            return None

        # Get absolute path
        path = os.path.abspath(path)

        # Check if it's a directory (we only watch files)
        if os.path.isdir(path):
            logger.warning(f"Requested path invalid (is a directory): {path}")
            return None
        contents = self.retrieve_from_file(path)
        uuid = self._hash_path(path)
        object_tags = tags.copy()  # Make a copy to avoid mutating the input
        object_tags.append("file")

        data_object = DataObjectSync(
            name=name,
            tags=object_tags,
            data=contents,
            created_at=datetime.now(),
            last_update=datetime.now(),
            sync=True,
            path=path,
        )

        self.__data_objects[uuid] = data_object
        logger.debug(f"Added object: {data_object}")
        logger.trace(f"Watching {path}")

        # Trigger callback for initial sync
        if self.on_file_change:
            logger.trace(f"Triggering initial sync callback for {path}")
            self.on_file_change(data_object)

        self.observer.schedule(self, path=path, recursive=True)

        return data_object

    def on_modified(self, event: FileModifiedEvent | DirModifiedEvent) -> None:
        """
        Watchdog event handler for file modifications.

        Args:
            event: File system event from watchdog
        """
        if event.is_directory:
            return

        event_path = str(os.path.abspath(event.src_path))
        reference = next(
            (f for f in self.__data_objects.values() if f.path == event_path), None
        )

        if reference:
            logger.trace(f"File changed: {event.src_path}/{event_path}")
            contents = self.retrieve_from_file(event_path)
            reference.data = contents
            reference.last_update = datetime.now()

            if contents is not None:
                logger.trace(f"Updated DataObject with path {reference.path}")

                # Trigger callback to sync to database
                if self.on_file_change:
                    logger.trace(f"Triggering change callback for {reference.path}")
                    self.on_file_change(reference)

    def stop(self):
        self.observer.stop()
        self.observer.join()

    @staticmethod
    def retrieve_from_file(filepath: str) -> Optional[str]:
        if not os.path.exists(filepath):
            return None
        if os.path.islink(filepath):
            filepath = os.readlink(filepath)
        try:
            with open(filepath, "r") as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            return None

    @staticmethod
    def _hash_path(path: str) -> str:
        return hashlib.md5(path.encode("utf-8")).hexdigest()
