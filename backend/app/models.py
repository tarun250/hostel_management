from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    block: Mapped[str] = mapped_column(String(20))
    floor: Mapped[int] = mapped_column(Integer, default=0)
    room_type: Mapped[str] = mapped_column(String(20), default="DOUBLE")  # SINGLE / DOUBLE / TRIPLE
    capacity: Mapped[int] = mapped_column(Integer, default=2)
    monthly_rent: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    students: Mapped[list["Student"]] = relationship(back_populates="room")
    maintenance_requests: Mapped[list["MaintenanceRequest"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )

    @property
    def occupied(self) -> int:
        return len(self.students)

    @property
    def vacancies(self) -> int:
        return max(self.capacity - self.occupied, 0)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    roll_no: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    course: Mapped[str] = mapped_column(String(80))
    year: Mapped[int] = mapped_column(Integer, default=1)
    guardian_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    room_id: Mapped[int | None] = mapped_column(
        ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True, index=True
    )
    joined_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    room: Mapped[Room | None] = relationship(back_populates="students")
    complaints: Mapped[list["Complaint"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    visitors: Mapped[list["Visitor"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    fees: Mapped[list["Fee"]] = relationship(back_populates="student", cascade="all, delete-orphan")

    @property
    def room_number(self) -> str | None:
        return self.room.number if self.room else None


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(30), default="GENERAL")  # ELECTRICAL / PLUMBING / ...
    priority: Mapped[str] = mapped_column(String(10), default="MEDIUM")  # LOW / MEDIUM / HIGH
    status: Mapped[str] = mapped_column(String(20), default="OPEN")  # OPEN / IN_PROGRESS / RESOLVED
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    room: Mapped[Room] = relationship(back_populates="maintenance_requests")

    @property
    def room_number(self) -> str | None:
        return self.room.number if self.room else None


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    subject: Mapped[str] = mapped_column(String(150))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(30), default="OTHER")  # MESS / NOISE / CLEANLINESS / ...
    status: Mapped[str] = mapped_column(String(20), default="OPEN")  # OPEN / IN_REVIEW / CLOSED
    filed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    student: Mapped[Student] = relationship(back_populates="complaints")

    @property
    def student_name(self) -> str | None:
        return self.student.full_name if self.student else None


class Visitor(Base):
    __tablename__ = "visitors"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    visitor_name: Mapped[str] = mapped_column(String(120))
    relation: Mapped[str] = mapped_column(String(40))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(200), nullable=True)
    check_in: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    check_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped[Student] = relationship(back_populates="visitors")

    @property
    def student_name(self) -> str | None:
        return self.student.full_name if self.student else None


class Fee(Base):
    __tablename__ = "fees"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), index=True)
    term: Mapped[str] = mapped_column(String(30))  # e.g. 2026-SEM1
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    due_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(10), default="PENDING")  # PENDING / PAID
    paid_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_ref: Mapped[str | None] = mapped_column(String(60), nullable=True)

    student: Mapped[Student] = relationship(back_populates="fees")

    @property
    def student_name(self) -> str | None:
        return self.student.full_name if self.student else None

    @property
    def overdue(self) -> bool:
        return self.status == "PENDING" and self.due_date < date.today()
