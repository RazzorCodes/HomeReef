from dataclasses import dataclass
from pathlib import Path

import engine.classifier as classifier
import engine.hash as hasher
import engine.probe as prober
from activities.activity import Activity
from data.db import Database
from data.db_op import upsert_list_item
from engine.list import list_path
from misc.logger import logger
from models.models import ListItem
from models.orm import WorkItemStatus

SCAN_FILES_EXTENSIONS = [".mkv", ".mp4", ".avi"]


@dataclass
class ScanActivity(Activity):
    db: Database | None = None
    _path: Path | None = None
    _probe: bool = False

    @property
    def valid(self) -> bool:
        return bool(self._path and self._path.exists() and self.db is not None)

    def setup(self, db: Database, path: Path, probe: bool = False) -> None:
        self.db = db
        self._path = path
        self._probe = probe

        if not path.exists():
            logger.warning(f"Scan activity set up with inexistent path: {self._path}")

        # Check the prober executable once during setup, not during the file loop
        if self._probe and not prober.check_executable():
            logger.error("Probe was requested, but ffprobe executable was not found.")
            self._probe = False  # Disable probing to prevent loop crashes

    def run(self) -> None:
        if not self.valid:
            logger.error("Scan activity invalid: Missing path or database")
            return

        # Bind to local variable so type-checkers know it's not None inside the callback
        database = self.db

        def on_file_found(file_path: Path) -> None:
            path_str = str(file_path)

            record = ListItem(
                path=path_str,
                hash=hasher.compute_hash(path_str),
                status=WorkItemStatus.UNKNOWN,
                name=classifier.clean_filename(path_str),
                size=file_path.stat().st_size,
            )

            if self._probe:
                record = prober.inspect(record)

            if upsert_list_item(database, record):
                logger.debug(f"Upserted DB record for: {file_path.name}")
            else:
                logger.error(f"Failed to upsert DB record for: {file_path.name}")

        logger.info(f"Starting scan on {self._path}")

        files = list_path(
            path=self._path, ext_wl=SCAN_FILES_EXTENSIONS, on_item=on_file_found
        )

        logger.info(f"Scan complete. Found and processed {len(files)} files.")

    def cancel(self) -> None:
        raise NotImplementedError
