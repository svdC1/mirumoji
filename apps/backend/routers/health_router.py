from fastapi import APIRouter
from utils.system_info_utils import get_system_info

health_router = APIRouter(prefix="/health")


@health_router.get("/status")
async def health_check():
    return {"status": "ok"}


@health_router.get("/system")
async def gpu_check():
    return get_system_info()
