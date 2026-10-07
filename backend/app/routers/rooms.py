from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_or_404
from ..models import Room, Student
from ..schemas import AllocationRequest, RoomCreate, RoomDetail, RoomOut, RoomUpdate

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


def _all_rooms(db: Session, block: str | None = None) -> list[Room]:
    query = select(Room).order_by(Room.block, Room.number)
    if block:
        query = query.where(Room.block == block)
    return list(db.scalars(query))


@router.get("", response_model=list[RoomOut])
def list_rooms(block: str | None = None, db: Session = Depends(get_db)):
    return _all_rooms(db, block)


@router.get("/available", response_model=list[RoomOut])
def available_rooms(block: str | None = None, db: Session = Depends(get_db)):
    return [room for room in _all_rooms(db, block) if room.vacancies > 0]


@router.get("/{room_id}", response_model=RoomDetail)
def get_room(room_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Room, room_id, "Room")


@router.post("", response_model=RoomOut, status_code=status.HTTP_201_CREATED)
def create_room(payload: RoomCreate, db: Session = Depends(get_db)):
    room = Room(**payload.model_dump())
    db.add(room)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"Room {payload.number} already exists")
    db.refresh(room)
    return room


@router.put("/{room_id}", response_model=RoomOut)
def update_room(room_id: int, payload: RoomUpdate, db: Session = Depends(get_db)):
    room = get_or_404(db, Room, room_id, "Room")
    changes = payload.model_dump(exclude_unset=True)
    if "capacity" in changes and changes["capacity"] < room.occupied:
        raise HTTPException(
            status_code=409,
            detail=f"Capacity cannot be lower than current occupancy ({room.occupied})",
        )
    for key, value in changes.items():
        setattr(room, key, value)
    db.commit()
    db.refresh(room)
    return room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room(room_id: int, db: Session = Depends(get_db)):
    room = get_or_404(db, Room, room_id, "Room")
    if room.occupied:
        raise HTTPException(status_code=409, detail="Room still has students. Deallocate them first")
    db.delete(room)
    db.commit()


@router.post("/{room_id}/allocate", response_model=RoomDetail)
def allocate(room_id: int, payload: AllocationRequest, db: Session = Depends(get_db)):
    room = get_or_404(db, Room, room_id, "Room")
    student = get_or_404(db, Student, payload.student_id, "Student")
    if student.room_id == room.id:
        raise HTTPException(status_code=409, detail="Student is already in this room")
    if student.room_id is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Student already allocated to room {student.room_number}. Deallocate first",
        )
    if room.vacancies <= 0:
        raise HTTPException(status_code=409, detail=f"Room {room.number} is full")
    student.room = room
    db.commit()
    db.refresh(room)
    return room


@router.post("/{room_id}/deallocate", response_model=RoomDetail)
def deallocate(room_id: int, payload: AllocationRequest, db: Session = Depends(get_db)):
    room = get_or_404(db, Room, room_id, "Room")
    student = get_or_404(db, Student, payload.student_id, "Student")
    if student.room_id != room.id:
        raise HTTPException(status_code=400, detail="Student is not in this room")
    student.room = None
    db.commit()
    db.refresh(room)
    return room
