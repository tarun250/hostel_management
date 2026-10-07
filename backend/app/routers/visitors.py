from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_or_404
from ..models import Student, Visitor
from ..schemas import VisitorCreate, VisitorOut

router = APIRouter(prefix="/api/visitors", tags=["visitors"])


@router.get("", response_model=list[VisitorOut])
def list_visitors(inside: bool | None = None, student_id: int | None = None, db: Session = Depends(get_db)):
    query = select(Visitor).order_by(Visitor.check_in.desc())
    if inside is True:
        query = query.where(Visitor.check_out.is_(None))
    elif inside is False:
        query = query.where(Visitor.check_out.is_not(None))
    if student_id:
        query = query.where(Visitor.student_id == student_id)
    return list(db.scalars(query))


@router.get("/{visitor_id}", response_model=VisitorOut)
def get_visitor(visitor_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Visitor, visitor_id, "Visitor entry")


@router.post("", response_model=VisitorOut, status_code=status.HTTP_201_CREATED)
def check_in(payload: VisitorCreate, db: Session = Depends(get_db)):
    get_or_404(db, Student, payload.student_id, "Student")
    entry = Visitor(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.post("/{visitor_id}/checkout", response_model=VisitorOut)
def check_out(visitor_id: int, db: Session = Depends(get_db)):
    entry = get_or_404(db, Visitor, visitor_id, "Visitor entry")
    if entry.check_out is not None:
        raise HTTPException(status_code=409, detail="Visitor already checked out")
    entry.check_out = datetime.now(timezone.utc)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{visitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_visitor(visitor_id: int, db: Session = Depends(get_db)):
    entry = get_or_404(db, Visitor, visitor_id, "Visitor entry")
    db.delete(entry)
    db.commit()
