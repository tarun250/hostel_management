from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .routers import complaints, fees, maintenance, rooms, stats, students, visitors

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="College hostel management: students, rooms, maintenance, complaints, visitors and fees.",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

for module in (students, rooms, maintenance, complaints, visitors, fees, stats):
    app.include_router(module.router)

Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app, endpoint="/metrics")


@app.get("/", tags=["meta"])
def root():
    return {"service": settings.app_name, "version": "1.0.0", "docs": "/docs"}


@app.get("/health", tags=["meta"])
def health():
    return {"status": "UP"}


@app.get("/ready", tags=["meta"])
def ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "READY", "database": "ok"}
