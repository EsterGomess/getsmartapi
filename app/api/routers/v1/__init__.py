""" V1 API routers initialization file."""
from app.api.routers.v1.user import router as customer_auth_router
from app.api.routers.v1.auth import router as auth_router
from app.api.routers.v1.note import router as note_router
from app.api.routers.v1.topic import router as topic_router