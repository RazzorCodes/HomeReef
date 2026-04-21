import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Union


@dataclass
class DataObject:
    name: str
    tags: list[str] = field(default_factory=list)
    data: Union[str, bytes, None] = None
    created_at: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return json.dumps(
            {
                "name": self.name,
                "tags": self.tags,
                "data": self.data.decode()
                if isinstance(self.data, bytes)
                else self.data,
                "created_at": {
                    "hr": self.created_at.isoformat(),
                    "ts": self.created_at.timestamp(),
                },
            }
        )


@dataclass
class DataObjectSync(DataObject):
    sync: bool = False
    last_update: datetime = field(default_factory=lambda: datetime.fromtimestamp(0))
    path: str = ""

    def __str__(self) -> str:
        obj = json.loads(super().__str__())

        obj["sync"] = self.sync
        obj["path"] = self.path
        obj["last_update"] = {
            "hr": self.last_update.isoformat(),
            "ts": self.last_update.timestamp(),
        }

        return json.dumps(obj)
