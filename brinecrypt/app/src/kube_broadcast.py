"""
kube-broadcast: Configuration broadcast server for Razzor-Homelab
"""

import sys
from importlib.metadata import metadata
from pathlib import Path

#
import uvicorn
from fastapi import FastAPI

from data.data_manager import DataManager
from data.providers.database.configuration import DatabaseHandlerConfiguration
from data.providers.database.handler import DatabaseHandler
from data.providers.local.file_manager import FileManager

#
from data.providers.remote.remote_manager import RemoteManager
from misc.configuration import retrieve_configuration
from misc.logger import logger

# Load package metadata
try:
    meta = metadata("kube-broadcast")
    APP_NAME = meta["Name"]
    APP_VERSION = meta["Version"]
    APP_DESCRIPTION = meta.get("Summary", "")
except Exception:
    APP_NAME = "kube-broadcast"
    APP_VERSION = "-.-.-"
    APP_DESCRIPTION = ""


def kube_broadcast():
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")

    kube_broadcast_args = retrieve_configuration()
    data_manager = DataManager(
        DatabaseHandler(
            DatabaseHandlerConfiguration(
                name="Master",
                location=Path(
                    kube_broadcast_args.kube_broadcast_database
                    or "/tmp/kube-broadcast.db"
                ),
            )
        ),
        FileManager(),
        RemoteManager(),
    )

    data_manager.add_resources_from_configuration(kube_broadcast_args)
    app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
    )
    try:
        uvicorn.run(
            app,
            host=kube_broadcast_args.kube_broadcast_host or "0.0.0.0",
            port=kube_broadcast_args.kube_broadcast_port or 8000,
            log_level="debug",
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if data_manager:
            data_manager.stop()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    logger.info("====================")
    logger.info("Starting application")
    logger.info("====================")

    kube_broadcast()
