import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TF AI-QC",
    description="True Footage AI-Powered Appraisal QC Platform",
    version="0.1.0",
    # Disable docs in production (NPI handling — limit exposure)
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

# CORS — restricted to Bubble domain in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Routes
app.include_router(health.router, tags=["health"])

# Sessions 1A+ will register additional routers here:
# app.include_router(reports.router, prefix="/reports", tags=["reports"])
# app.include_router(revisions.router, prefix="/revisions", tags=["revisions"])
# app.include_router(rules.router, prefix="/rules", tags=["rules"])
# app.include_router(coaching.router, prefix="/coaching", tags=["coaching"])
# app.include_router(internal.router, prefix="/internal", tags=["internal"])


@app.on_event("startup")
async def startup():
    logger.info("TF AI-QC starting up", extra={"environment": settings.environment})


@app.on_event("shutdown")
async def shutdown():
    logger.info("TF AI-QC shutting down")
