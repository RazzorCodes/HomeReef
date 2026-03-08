import asyncio
from enum import StrEnum
from typing import override

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from misc.logger import logger
from models.config import AppConfig
from modules.module import Module, Stage
from activities.list_activity import ListActivity
from activities.scan_activity import ScanActivity
from activities.status_activity import StatusActivity
from activities.transcode_activity import TranscodeActivity


class State(StrEnum):
    UNKNOWN = "unknown"
    STARTUP = "startup"
    READY = "ready"
    SERVING = "serving"
    ERROR = "unrecoverable"

    def AsStage(self) -> Stage:
        match self:
            case State.UNKNOWN:
                return Stage.UNKNOWN
            case State.STARTUP:
                return Stage.STARTUP
            case State.SERVING:
                return Stage.PROCESSING
            case State.READY:
                return Stage.READY
            case _:
                return Stage.ERROR


class EndpointModule(Module[State]):
    def __init__(self):
        super().__init__(State.UNKNOWN)
        self._app_host: str
        self._app_port: int
        self._serving: bool = False

        self._app = FastAPI()

        self._setup_routes()
        self._create_middleware()

    @property
    def api_app(self) -> FastAPI:
        return self._app

    def expose(self):
        self._serving = True
        self.state = State.SERVING
        logger.info("Endpoint module is now SERVING requests.")

    def _create_middleware(self):
        @self._app.middleware("http")
        async def check_readiness(request: Request, call_next):
            if not self._serving:
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content={"message": "System is starting up. Please wait..."},
                )
            return await call_next(request)

    def _setup_routes(self):
        @self._app.get("/version")
        def get_version():
            try:
                with open("/app/version.txt", "r") as f:
                    return {"version": f.read().strip()}
            except Exception:
                return {"version": "unknown"}

        @self._app.get("/list")
        async def get_list():
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            
            activity = ListActivity()
            activity.setup(db=self.module_bus["database"]._database, result_future=future)
            self.module_bus["worker"].submit(activity)
            
            # Wait for the worker thread to resolve the future
            return await future

        @self._app.get("/status")
        async def get_status():
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            
            activity = StatusActivity()
            activity.setup(worker_module=self.module_bus["worker"], result_future=future)
            self.module_bus["worker"].submit(activity)
            
            return await future

        @self._app.put("/process/{target_hash}")
        async def process_hash(target_hash: str):
            activity = TranscodeActivity()
            if not activity.setup(db=self.module_bus["database"]._database, target_hash=target_hash):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"message": f"Failed to setup transcode for {target_hash}"}
                )
            
            task_id = self.module_bus["worker"].submit(activity)
            return {"task_id": task_id}

        @self._app.delete("/cancel/{task_uuid}")
        async def cancel_task(task_uuid: str):
            success = self.module_bus["worker"].cancel(task_uuid)
            if success:
                return {"message": f"Task {task_uuid} cancelled"}
            else:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"message": f"Task {task_uuid} not found"}
                )

        @self._app.put("/scan")
        async def start_scan():
            activity = ScanActivity()
            scan_path = self.module_bus["config"].media_path
            if not activity.setup(
                db=self.module_bus["database"]._database,
                path=scan_path,
                probe=True,
            ):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"message": f"Failed to setup scan for {scan_path}"},
                )

            task_id = self.module_bus["worker"].submit(activity)
            return {"task_id": task_id}

    @override
    def setup(self, config: AppConfig, module_bus: dict | None = None) -> bool:
        logger.info("Setting up endpoint module")
        self._app_host = config.app_host
        self._app_port = config.app_port
        
        self.module_bus = module_bus or {}

        self.state = State.READY
        logger.info("Endpoint module ready (waiting for server orchestration if applicable).")
        return True

    @override
    def shutdown(self, force: bool) -> bool:
        """Cleanup specific endpoint module states."""
        logger.info("Shutting down Endpoint module...")
        self.state = State.UNKNOWN
        self._serving = False
        return True
