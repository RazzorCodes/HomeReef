import uvicorn
from config import config
from fastapi import FastAPI
from governors.governor import Governor
from models.configuration import Configuration

gov = Governor(
    Configuration(database_path=config.db_path, media_path=config.media_path)
)


async def lifespan(app: FastAPI):
    gov.setup()
    yield
    gov.shutdown()


app = FastAPI(lifespan=lifespan)


@app.put("/process/{file_hash}")
def trigger_transcode_file(file_hash: str):
    task_id = gov.start_transcode(file_hash)
    return {"message": "Transcode started", "task_id": task_id}


@app.get("/list")
def list_database():
    return gov.list_database()


@app.get("/status")
def get_current_transcode_status():
    """Returns a list of whatever the Governor is currently working on."""
    return {"active_tasks": [task_id for task_id in gov.get_status().keys()]}


@app.put("/rescan")
def rescan_library():
    return {"takid": gov.start_scan()}


@app.delete("/task/{task_id}")
def stop_task(task_id: str):
    gov.stop_task(task_id)


if __name__ == "__main__":
    uvicorn.run("app:app", host=config.app_host, port=config.app_port, reload=True)
