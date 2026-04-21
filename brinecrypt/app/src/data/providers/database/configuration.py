import os
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from misc.logger import logger

# check if server configuration is set to TEST or to DEV
# TEST
# ./test-data/kube-bootstrap-tests.db
# DEV
DEFAULT_LOCATION = "./dev-data/kube-bootstrap.db"
# PROD
# /mnt/database/kube-bootstrap.db


def check_address(address: tuple[str, int]) -> bool:
    try:
        socket.create_connection(address, timeout=1)
        return True
    except socket.error:
        logger.error(f"Database address {address} is not accessible")
        return False


@dataclass
class DatabaseHandlerConfiguration:
    name: str | None
    location: Union[tuple[str, int], Path] | None = None

    def validate(self) -> bool:
        if not self.name:
            self.name = "unnamed"
            logger.trace(f"DatabaseHandlerConfiguration name set to {self.name}")
        if not self.location:
            self.location = Path(DEFAULT_LOCATION)
            logger.trace(
                f"DatabaseHandlerConfiguration location set to {self.location}"
            )
        if isinstance(self.location, Path):
            if not self.location.exists():
                logger.error(f"Database file {self.location} does not exist")
                os.makedirs(self.location.parent, exist_ok=True)
            else:
                if not os.access(self.location, os.W_OK | os.R_OK):
                    logger.error(f"Database file {self.location} is not RW-accessible")
                    return False
            return True
        elif isinstance(self.location, tuple):
            if not check_address(self.location):
                return False

            raise NotImplementedError("Remote db not currently supported")
            return True

        raise ValueError("Incorrect Configuration")
        return False
