import threading
from dataclasses import dataclass

import uvicorn
from fastapi import FastAPI
from router.bootstrap import router as bootstrap_router
from router.credentials import router as credentials_router
from router.env import router as env_router


@dataclass
class KubeBroadcastServerParameters:
    name: str = "kube-broadcast-default"
    version: str = "0.0.0"
    description: str = ""
    address: str = "0.0.0.0"
    port: int = 8000


class KubeBroadcastServer(FastAPI):
    def __init__(self, parameters: KubeBroadcastServerParameters):
        super().__init__(
            title=parameters.name,
            version=parameters.version,
            description=parameters.description,
        )

        self.include_router(bootstrap_router)
        self.include_router(credentials_router)
        self.include_router(env_router)

        threading.Thread(
            target=uvicorn.run,
            args=(self,),
            kwargs={"host": parameters.address, "port": parameters.port},
            daemon=True,
        ).start()


if __name__ == "__main__":
    import time

    KubeBroadcastServer(
        KubeBroadcastServerParameters(
            name="__main__-kube-broadcast",
            version="0.0.0alpha",
            description="---",
            address="0.0.0.0",
            port=8000,
        )
    )

    while True:
        time.sleep(1)
