from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_or_404
from ..models import Fee, Student
from ..schemas import FeeOut, StudentCreate, StudentOut, StudentUpdate

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("", response_model=list[StudentOut])
def list_students(search: str | None = None, unallocated: bool = False, db: Session = Depends(get_db)):
    query = select(Student).order_by(Student.roll_no)
    if search:
        like = f"%{search}%"
        query = query.where(or_(Student.full_name.ilike(like), Student.roll_no.ilike(like)))
    if unallocated:
        query = query.where(Student.room_id.is_(None))
    return list(db.scalars(query))


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Student, student_id, "Student")


@router.get("/{student_id}/fees", response_model=list[FeeOut])
def student_fees(student_id: int, db: Session = Depends(get_db)):
    get_or_404(db, Student, student_id, "Student")
    return list(db.scalars(select(Fee).where(Fee.student_id == student_id).order_by(Fee.due_date)))


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def register_student(payload: StudentCreate, db: Session = Depends(get_db)):
    student = Student(**payload.model_dump())
    db.add(student)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Roll number or email already registered")
    db.refresh(student)
    return student


@router.put("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, payload: StudentUpdate, db: Session = Depends(get_db)):
    student = get_or_404(db, Student, student_id, "Student")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already in use")
    db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = get_or_404(db, Student, student_id, "Student")
    db.delete(student)
    db.commit()
