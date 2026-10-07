from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Complaint, Fee, MaintenanceRequest, Room, Student, Visitor
from ..schemas import SummaryOut

router = APIRouter(prefix="/api/stats", tags=["stats"])


def _count(db: Session, column, *conditions) -> int:
    return db.scalar(select(func.count(column)).where(*conditions)) or 0


@router.get("/summary", response_model=SummaryOut)
def summary(db: Session = Depends(get_db)):
    rooms = list(db.scalars(select(Room)))
    total_beds = sum(r.capacity for r in rooms)
    occupied_beds = sum(r.occupied for r in rooms)
    pending_count, pending_amount = db.execute(
        select(func.count(Fee.id), func.coalesce(func.sum(Fee.amount), 0)).where(Fee.status == "PENDING")
    ).one()
    return SummaryOut(
        students=_count(db, Student.id),
        unallocated_students=_count(db, Student.id, Student.room_id.is_(None)),
        rooms=len(rooms),
        total_beds=total_beds,
        occupied_beds=occupied_beds,
        occupancy_pct=round(occupied_beds * 100 / total_beds, 1) if total_beds else 0.0,
        available_rooms=sum(1 for r in rooms if r.vacancies > 0),
        open_maintenance=_count(db, MaintenanceRequest.id, MaintenanceRequest.status != "RESOLVED"),
        open_complaints=_count(db, Complaint.id, Complaint.status != "CLOSED"),
        visitors_inside=_count(db, Visitor.id, Visitor.check_out.is_(None)),
        pending_fees_count=pending_count,
        pending_fees_amount=Decimal(str(pending_amount)),
        overdue_fees_count=_count(db, Fee.id, Fee.status == "PENDING", Fee.due_date < date.today()),
    )
