from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RoomType = Literal["SINGLE", "DOUBLE", "TRIPLE", "DORM"]
Priority = Literal["LOW", "MEDIUM", "HIGH"]
MaintenanceStatus = Literal["OPEN", "IN_PROGRESS", "RESOLVED"]
MaintenanceCategory = Literal["ELECTRICAL", "PLUMBING", "FURNITURE", "CLEANING", "INTERNET", "GENERAL"]
ComplaintStatus = Literal["OPEN", "IN_REVIEW", "CLOSED"]
ComplaintCategory = Literal["MESS", "NOISE", "CLEANLINESS", "SECURITY", "ROOMMATE", "OTHER"]
FeeStatus = Literal["PENDING", "PAID"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Students ----------
class StudentBase(BaseModel):
    roll_no: str = Field(min_length=1, max_length=30)
    full_name: str = Field(min_length=1, max_length=120)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=120)
    phone: str | None = Field(default=None, max_length=20)
    course: str = Field(min_length=1, max_length=80)
    year: int = Field(default=1, ge=1, le=6)
    guardian_phone: str | None = Field(default=None, max_length=20)


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=120)
    phone: str | None = Field(default=None, max_length=20)
    course: str | None = Field(default=None, min_length=1, max_length=80)
    year: int | None = Field(default=None, ge=1, le=6)
    guardian_phone: str | None = Field(default=None, max_length=20)


class StudentOut(StudentBase, ORMModel):
    id: int
    room_id: int | None
    room_number: str | None = None
    joined_on: datetime


# ---------- Rooms ----------
class RoomBase(BaseModel):
    number: str = Field(min_length=1, max_length=20)
    block: str = Field(min_length=1, max_length=20)
    floor: int = Field(default=0, ge=0, le=50)
    room_type: RoomType = "DOUBLE"
    capacity: int = Field(default=2, ge=1, le=12)
    monthly_rent: Decimal = Field(default=Decimal("0"), ge=0)


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    block: str | None = Field(default=None, min_length=1, max_length=20)
    floor: int | None = Field(default=None, ge=0, le=50)
    room_type: RoomType | None = None
    capacity: int | None = Field(default=None, ge=1, le=12)
    monthly_rent: Decimal | None = Field(default=None, ge=0)


class RoomOut(RoomBase, ORMModel):
    id: int
    occupied: int
    vacancies: int


class RoomDetail(RoomOut):
    students: list["StudentBrief"] = []


class StudentBrief(ORMModel):
    id: int
    roll_no: str
    full_name: str


class AllocationRequest(BaseModel):
    student_id: int


# ---------- Maintenance ----------
class MaintenanceCreate(BaseModel):
    room_id: int
    title: str = Field(min_length=1, max_length=120)
    description: str | None = None
    category: MaintenanceCategory = "GENERAL"
    priority: Priority = "MEDIUM"


class MaintenanceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    category: MaintenanceCategory | None = None
    priority: Priority | None = None
    status: MaintenanceStatus | None = None


class MaintenanceStatusUpdate(BaseModel):
    status: MaintenanceStatus


class MaintenanceOut(ORMModel):
    id: int
    room_id: int
    room_number: str | None = None
    title: str
    description: str | None
    category: str
    priority: str
    status: str
    reported_at: datetime
    updated_at: datetime


# ---------- Complaints ----------
class ComplaintCreate(BaseModel):
    student_id: int
    subject: str = Field(min_length=1, max_length=150)
    details: str | None = None
    category: ComplaintCategory = "OTHER"


class ComplaintUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=1, max_length=150)
    details: str | None = None
    category: ComplaintCategory | None = None
    status: ComplaintStatus | None = None


class ComplaintOut(ORMModel):
    id: int
    student_id: int
    student_name: str | None = None
    subject: str
    details: str | None
    category: str
    status: str
    filed_at: datetime


# ---------- Visitors ----------
class VisitorCreate(BaseModel):
    student_id: int
    visitor_name: str = Field(min_length=1, max_length=120)
    relation: str = Field(min_length=1, max_length=40)
    phone: str | None = Field(default=None, max_length=20)
    purpose: str | None = Field(default=None, max_length=200)


class VisitorOut(ORMModel):
    id: int
    student_id: int
    student_name: str | None = None
    visitor_name: str
    relation: str
    phone: str | None
    purpose: str | None
    check_in: datetime
    check_out: datetime | None


# ---------- Fees ----------
class FeeCreate(BaseModel):
    student_id: int
    term: str = Field(min_length=1, max_length=30)
    amount: Decimal = Field(gt=0)
    due_date: date


class FeeUpdate(BaseModel):
    term: str | None = Field(default=None, min_length=1, max_length=30)
    amount: Decimal | None = Field(default=None, gt=0)
    due_date: date | None = None
    status: FeeStatus | None = None


class FeePayment(BaseModel):
    payment_ref: str | None = Field(default=None, max_length=60)


class FeeOut(ORMModel):
    id: int
    student_id: int
    student_name: str | None = None
    term: str
    amount: Decimal
    due_date: date
    status: str
    paid_on: date | None
    payment_ref: str | None
    overdue: bool = False


# ---------- Stats ----------
class SummaryOut(BaseModel):
    students: int
    unallocated_students: int
    rooms: int
    total_beds: int
    occupied_beds: int
    occupancy_pct: float
    available_rooms: int
    open_maintenance: int
    open_complaints: int
    visitors_inside: int
    pending_fees_count: int
    pending_fees_amount: Decimal
    overdue_fees_count: int


RoomDetail.model_rebuild()
