from fastapi import APIRouter

from app.routers.admin.admin_router import admin_router
from app.routers.auth.user_me_router import user_me_router
from app.routers.auth.user_register_router import user_register_router
from app.routers.auth.user_token_router import user_token_router


routers = APIRouter()
router_list = [
    admin_router,
    user_me_router,
    user_register_router,
    user_token_router,
]

for router in router_list:
    routers.include_router(router)
