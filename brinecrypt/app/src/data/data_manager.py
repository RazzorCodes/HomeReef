from dataclasses import dataclass, field
from typing import Optional

from data.model.data_object import DataObject, DataObjectSync
from data.providers.database.configuration import DatabaseHandlerConfiguration
from data.providers.database.handler import DatabaseHandler
from data.providers.local.file_manager import FileManager
from data.providers.remote.remote_manager import RemoteManager
from misc.configuration import KubeBroadcastConfiguration, ParameterType
from misc.logger import logger


@dataclass
class DataManager:
    _db_handler: DatabaseHandler
    _file_manager: FileManager
    _remote_manager: RemoteManager
    _watched_files: dict[str, str] = field(default_factory=dict)
    _watched_remotes: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self._file_manager.on_file_change = self._on_file_changed
        self._remote_manager.on_data_change = self._on_remote_changed

    def add_resources_from_configuration(
        self, configuration: KubeBroadcastConfiguration
    ) -> None:
        for item in configuration.kube_broadcast_configuration_items:
            match item.type:
                case ParameterType.PURE:
                    self.add_pure_resource(
                        name=item.name, tags=["pure"], data=str(item.value)
                    )
                case ParameterType.LOCAL:
                    self.add_file_resource(
                        name=item.name, path=item.source_details or "", tags=["local"]
                    )
                case ParameterType.REMOTE:
                    self.add_remote_resource(
                        name=item.name, url=item.source_details or "", tags=["remote"]
                    )

    def add_pure_resource(self, name: str, tags: list[str], data: str) -> Optional[str]:
        return self._db_handler.register(DataObject(name, tags, data))

    def add_file_resource(self, name: str, path: str, tags: list[str]) -> Optional[str]:
        file_obj = self._file_manager.watch(name, path, tags)
        if file_obj is None:
            return None

        uri = self._db_handler.register(file_obj)
        if uri:
            self._watched_files[path] = uri
        return uri

    def add_remote_resource(
        self, name: str, url: str, tags: list[str], interval: Optional[int] = None
    ) -> Optional[str]:
        resource_id = self._remote_manager.watch(name, url, tags, interval)
        if resource_id is None:
            return None

        import time

        time.sleep(1)  # wait for initial sync callback
        return self._watched_remotes.get(url)

    def query(self, uri: str) -> Optional[DataObject]:
        return self._db_handler.query(uri)

    def stop(self) -> None:
        self._file_manager.stop()
        self._remote_manager.stop()

    def _on_file_changed(self, file_obj: DataObjectSync) -> None:
        uri = self._db_handler.register(file_obj)
        if uri:
            self._watched_files[file_obj.path] = uri

    def _on_remote_changed(self, url: str, remote_obj: DataObject) -> None:
        uri = self._db_handler.register(remote_obj)
        if uri:
            self._watched_remotes[url] = uri


def create_data_manager() -> DataManager:
    db_handler = DatabaseHandler(DatabaseHandlerConfiguration(name="Master"))
    file_manager = FileManager(
        on_file_change=lambda _: None
    )  # overridden in __post_init__
    remote_manager = RemoteManager(on_data_change=lambda *_: None)
    return DataManager(db_handler, file_manager, remote_manager)
