from fastapi import APIRouter, HTTPException

from data.data_manager import dataManager

# Create router instead of app
router = APIRouter(
    prefix="/bootstrap",  # All routes will be prefixed with /users
    tags=["k3s bootstrap"],  # For documentation organization
)


@router.get("")
@router.get("/query")
async def query():
    """GET /bootstrap /bootstrap/query - Is token available"""
    data = dataManager.get_all()
    token = next("k3s-token" in dataObject.tags for dataObject in data)
    return token is not None


@router.get("/token")
async def token():
    """GET /bootstrap/token - Is token available"""
    data = dataManager.get_all()
    token = next(
        (d for d in data if "k3s-token" in d.tags),
        None,  # default if no match
    )
    if token is not None:
        return token.data
    else:
        raise HTTPException(status_code=404, detail="Token not found")


# @router.get("/{user_id}")
# async def get_user(user_id: int = Path(..., gt=0)):
#    """GET /users/{user_id} - Get user by ID"""
#    if user_id not in users_db:
#        raise HTTPException(status_code=404, detail="User not found")
#    return users_db[user_id]
#
#
# @router.post("/", status_code=201)
# async def create_user(user: CreateUserRequest):
#    """POST /users - Create new user"""
#    new_id = max(users_db.keys()) + 1 if users_db else 1
#    new_user = {"id": new_id, "name": user.name, "email": user.email}
#    users_db[new_id] = new_user
#    return new_user
#
#
# @router.delete("/{user_id}", status_code=204)
# async def delete_user(user_id: int = Path(..., gt=0)):
#    """DELETE /users/{user_id} - Delete user"""
#    if user_id not in users_db:
#        raise HTTPException(status_code=404, detail="User not found")
#    del users_db[user_id]
#    return None
