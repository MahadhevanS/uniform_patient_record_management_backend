from fastapi import APIRouter
from app.api.endpoints import auth, records, hospitals, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/v1", tags=["Authentication"])
api_router.include_router(records.router, prefix="/v1", tags=["Records"])
api_router.include_router(hospitals.router, prefix="/v1", tags=["Hospitals"])
api_router.include_router(users.router, prefix="/v1", tags=["Users"])