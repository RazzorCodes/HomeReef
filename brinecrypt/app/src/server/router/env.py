"""
Environment Variables Router

This router provides HTTP endpoints for accessing environmental data
managed by the DataManager, including:
- K3s tokens
- SSH public keys
- Other configuration data

The DataManager orchestrates multiple data sources (database, files, URLs)
and provides a unified interface for data access.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import JSONResponse

from data.data_manager import get_data_manager
from misc.logger import logger

# Get the data manager instance
dataManager = get_data_manager()

# Create router
router = APIRouter(
    prefix="/env",
    tags=["Environmental Variables"],
)


@router.get("")
async def health_check():
    """
    GET /env - Health check for data services

    Returns status of database handler and other services.
    """
    try:
        status = {
            "status": "available",
            "database": "connected" if dataManager._db_handler else "unavailable",
            "file_watcher": "active" if dataManager._file_manager else "inactive",
            "watched_files": len(dataManager.get_watched_files()),
        }
        return JSONResponse(content=status, status_code=200)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/files")
async def list_watched_files():
    """
    GET /env/files - List all watched files and their URIs

    Returns a mapping of file paths to their database URIs.
    """
    try:
        watched_files = dataManager.get_watched_files()
        return JSONResponse(
            content={
                "count": len(watched_files),
                "files": watched_files,
            },
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Failed to list watched files: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file list")


@router.get("/query/{uri}")
async def query_by_uri(uri: str = Path(..., description="Resource URI to query")):
    """
    GET /env/query/{uri} - Query data by URI

    URI format: {prefix}-{internal_id}
    Examples:
        - db-1234567890.123
        - file-abc123def456

    Returns the data object if found.
    """
    try:
        logger.debug(f"Query request for URI: {uri}")

        result = dataManager.query(uri)

        if not result:
            logger.warning(f"Resource not found: {uri}")
            raise HTTPException(status_code=404, detail=f"Resource not found: {uri}")

        # Return the DataObject as JSON
        return JSONResponse(
            content={
                "uri": uri,
                "name": result.name,
                "tags": result.tags,
                "data": result.data
                if isinstance(result.data, str)
                else result.data.decode()
                if isinstance(result.data, bytes)
                else None,
                "created_at": result.created_at.isoformat()
                if result.created_at
                else None,
            },
            status_code=200,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed for URI {uri}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search")
async def search_by_tags(
    tags: Optional[str] = Query(None, description="Comma-separated tags to search for"),
):
    """
    GET /env/search?tags=tag1,tag2 - Search data by tags

    Returns all data objects matching the specified tags.
    Note: This endpoint requires DatabaseHandler.search() to be implemented.
    """
    try:
        if not tags:
            raise HTTPException(status_code=400, detail="Tags parameter is required")

        tag_list = [tag.strip() for tag in tags.split(",")]
        logger.debug(f"Search request for tags: {tag_list}")

        # TODO: Implement search_by_tags in DatabaseHandler
        raise HTTPException(
            status_code=501, detail="Search by tags not yet implemented"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/register")
async def register_data(
    name: str = Query(..., description="Name for the data object"),
    data: str = Query(..., description="Data content to store"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
):
    """
    POST /env/register - Register new data to the database

    Creates a new data object and stores it in the database.
    Returns the URI of the created resource.
    """
    try:
        from data.data_model import DataObject

        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []

        data_obj = DataObject(
            name=name,
            tags=tag_list,
            data=data,
        )

        uri = dataManager.register(data_obj)

        if not uri:
            raise HTTPException(
                status_code=500, detail="Failed to register data object"
            )

        logger.info(f"Data registered successfully: {name} -> {uri}")

        return JSONResponse(
            content={
                "uri": uri,
                "name": name,
                "tags": tag_list,
                "message": "Data registered successfully",
            },
            status_code=201,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/watch")
async def add_watched_file(
    path: str = Query(..., description="File path to watch"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
):
    """
    POST /env/watch - Add a new file to watch

    Starts watching a file for changes and syncs it to the database.
    Returns the URI of the registered file.
    """
    try:
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else []

        uri = dataManager.add_resource_file(path, tag_list)

        if not uri:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to watch file: {path}. Check if file exists.",
            )

        logger.info(f"File watch added: {path} -> {uri}")

        return JSONResponse(
            content={
                "uri": uri,
                "path": path,
                "tags": tag_list,
                "message": "File watch added successfully",
            },
            status_code=201,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add file watch: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/data/{uri}")
async def get_data_only(uri: str = Path(..., description="Resource URI")):
    """
    GET /env/data/{uri} - Get only the data content (no metadata)

    Returns just the raw data string for the given URI.
    Useful for simple key-value lookups.
    """
    try:
        logger.debug(f"Data-only request for URI: {uri}")

        result = dataManager.query(uri)

        if not result:
            raise HTTPException(status_code=404, detail=f"Resource not found: {uri}")

        # Return just the data content as plain text
        data = result.data
        if isinstance(data, bytes):
            data = data.decode()

        return data or ""

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data retrieval failed for URI {uri}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
