from data.data_manager import DataManager
from data.model.python.data_object import DataObject
from misc.logger import logger


class BootstrapController:
    def __init__(self, dataManager: DataManager):
        if not dataManager:
            raise ValueError("DataManager cannot be None")

        if not dataManager.query("token"):
            logger.warning(
                f"Cluster token is not set at {__class__.__name__} initialization"
            )
        self.dataManager = dataManager
