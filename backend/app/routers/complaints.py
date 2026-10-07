from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_or_404
from ..models import Complaint, Student
from ..schemas import ComplaintCreate, ComplaintOut, ComplaintStatus, ComplaintUpdate

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


@router.get("", response_model=list[ComplaintOut])
def list_complaints(
    status: ComplaintStatus | None = None,
    student_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = select(Complaint).order_by(Complaint.filed_at.desc())
    if status:
        query = query.where(Complaint.status == status)
    if student_id:
        query = query.where(Complaint.student_id == student_id)
    return list(db.scalars(query))


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Complaint, complaint_id, "Complaint")


@router.post("", response_model=ComplaintOut, status_code=status.HTTP_201_CREATED)
def file_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    get_or_404(db, Student, payload.student_id, "Student")
    complaint = Complaint(**payload.model_dump())
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


@router.put("/{complaint_id}", response_model=ComplaintOut)
def update_complaint(complaint_id: int, payload: ComplaintUpdate, db: Session = Depends(get_db)):
    complaint = get_or_404(db, Complaint, complaint_id, "Complaint")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(complaint, key, value)
    db.commit()
    db.refresh(complaint)
    return complaint


@router.delete("/{complaint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = get_or_404(db, Complaint, complaint_id, "Complaint")
    db.delete(complaint)
    db.commit()
