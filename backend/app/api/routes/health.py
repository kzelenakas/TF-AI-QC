from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "tf-ai-qc"}


@router.get("/health/db")
def db_health(db: Session = Depends(get_db)):
    """Verify database connectivity. Used by Railway health checks."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
