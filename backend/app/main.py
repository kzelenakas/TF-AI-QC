import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import health
from app.api.routes import reports
from app.api.routes import revisions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TF AI-QC",
    description="True Footage AI-Powered Appraisal QC Platform",
    version="0.1.0",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Routes
app.include_router(health.router, tags=["health"])
app.include_router(reports.router)
app.include_router(revisions.router)

# Session 4+ will register additional routers:
# app.include_router(rules.router)
# app.include_router(coaching.router)
# app.include_router(internal.router)


@app.on_event("startup")
async def startup():
    logger.info("TF AI-QC starting up", extra={"environment": settings.environment})


@app.on_event("shutdown")
async def shutdown():
    logger.info("TF AI-QC shutting down")
