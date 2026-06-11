from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.connectors import router as connectors_router
from app.api.health import router as health_router
from app.api.tasks import router as tasks_router
from app.core.config import settings

app = FastAPI(
    title="Kefcatic API",
    description="No-code AI assistant automation platform",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(connectors_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
