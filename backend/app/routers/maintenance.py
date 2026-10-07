from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_or_404
from ..models import MaintenanceRequest, Room
from ..schemas import (
    MaintenanceCreate,
    MaintenanceOut,
    MaintenanceStatus,
    MaintenanceStatusUpdate,
    MaintenanceUpdate,
)

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


@router.get("", response_model=list[MaintenanceOut])
def list_requests(
    status: MaintenanceStatus | None = None,
    room_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = select(MaintenanceRequest).order_by(MaintenanceRequest.reported_at.desc())
    if status:
        query = query.where(MaintenanceRequest.status == status)
    if room_id:
        query = query.where(MaintenanceRequest.room_id == room_id)
    return list(db.scalars(query))


@router.get("/{request_id}", response_model=MaintenanceOut)
def get_request(request_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, MaintenanceRequest, request_id, "Maintenance request")


@router.post("", response_model=MaintenanceOut, status_code=status.HTTP_201_CREATED)
def raise_request(payload: MaintenanceCreate, db: Session = Depends(get_db)):
    get_or_404(db, Room, payload.room_id, "Room")
    item = MaintenanceRequest(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{request_id}", response_model=MaintenanceOut)
def update_request(request_id: int, payload: MaintenanceUpdate, db: Session = Depends(get_db)):
    item = get_or_404(db, MaintenanceRequest, request_id, "Maintenance request")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{request_id}/status", response_model=MaintenanceOut)
def set_status(request_id: int, payload: MaintenanceStatusUpdate, db: Session = Depends(get_db)):
    item = get_or_404(db, MaintenanceRequest, request_id, "Maintenance request")
    item.status = payload.status
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(request_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, MaintenanceRequest, request_id, "Maintenance request")
    db.delete(item)
    db.commit()
