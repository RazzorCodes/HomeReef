from abc import ABC, abstractmethod
from dataclasses import dataclass

from data.model.data_object import DataObject
from misc.logger import logger


@dataclass
class DataHandlerContext:
    name: str
    type: type


class DataHandler(ABC):
    def __init__(self, n: str, t: type) -> None:
        logger.trace(f"Initializing DataHandler {n} of type {t.__name__}")
        self.context = DataHandlerContext(name=n, type=t)

    def query(self, uri: str) -> DataObject | None:
        logger.debug(f"DataHandler {self.context.name} queried for {uri}")
        if self._check_access("ns", "acc", "query"):
            return self._query(uri)
        else:
            logger.warning(f"DataHandler {self.context.name} got unauthorised request")

    def register(self, object: DataObject) -> str | None:
        logger.debug(
            f"DataHandler {self.context.name} registering object {object.name}"
        )
        if self._check_access("ns", "acc", "register"):
            return self._register(object)
        else:
            logger.warning(f"DataHandler {self.context.name} got unauthorised request")

    def _check_access(self, namespace, account, path) -> bool:
        return True

    @abstractmethod
    def _query(self, uri: str) -> DataObject | None:
        raise NotImplementedError

    @abstractmethod
    def _register(self, object: DataObject) -> str | None:
        raise NotImplementedError
