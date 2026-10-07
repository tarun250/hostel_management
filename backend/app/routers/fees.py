from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_or_404
from ..models import Fee, Student
from ..schemas import FeeCreate, FeeOut, FeePayment, FeeStatus, FeeUpdate

router = APIRouter(prefix="/api/fees", tags=["fees"])


@router.get("", response_model=list[FeeOut])
def list_fees(status: FeeStatus | None = None, student_id: int | None = None, db: Session = Depends(get_db)):
    query = select(Fee).order_by(Fee.due_date, Fee.id)
    if status:
        query = query.where(Fee.status == status)
    if student_id:
        query = query.where(Fee.student_id == student_id)
    return list(db.scalars(query))


@router.get("/{fee_id}", response_model=FeeOut)
def get_fee(fee_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Fee, fee_id, "Fee")


@router.post("", response_model=FeeOut, status_code=status.HTTP_201_CREATED)
def create_fee(payload: FeeCreate, db: Session = Depends(get_db)):
    get_or_404(db, Student, payload.student_id, "Student")
    fee = Fee(**payload.model_dump())
    db.add(fee)
    db.commit()
    db.refresh(fee)
    return fee


@router.put("/{fee_id}", response_model=FeeOut)
def update_fee(fee_id: int, payload: FeeUpdate, db: Session = Depends(get_db)):
    fee = get_or_404(db, Fee, fee_id, "Fee")
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(fee, key, value)
    if changes.get("status") == "PAID" and fee.paid_on is None:
        fee.paid_on = date.today()
    if changes.get("status") == "PENDING":
        fee.paid_on = None
        fee.payment_ref = None
    db.commit()
    db.refresh(fee)
    return fee


@router.put("/{fee_id}/pay", response_model=FeeOut)
def mark_paid(fee_id: int, payload: FeePayment | None = None, db: Session = Depends(get_db)):
    fee = get_or_404(db, Fee, fee_id, "Fee")
    if fee.status == "PAID":
        raise HTTPException(status_code=409, detail="Fee already paid")
    fee.status = "PAID"
    fee.paid_on = date.today()
    if payload and payload.payment_ref:
        fee.payment_ref = payload.payment_ref
    db.commit()
    db.refresh(fee)
    return fee


@router.delete("/{fee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fee(fee_id: int, db: Session = Depends(get_db)):
    fee = get_or_404(db, Fee, fee_id, "Fee")
    db.delete(fee)
    db.commit()
