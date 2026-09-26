from fastapi import APIRouter

from app.api.v1.auth import auth_router
from app.api.v1.lists import lists_router
from app.api.v1.movies import movies_router
from app.api.v1.profiles import profiles_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(movies_router)
api_router.include_router(lists_router)
api_router.include_router(profiles_router)
