"""initial hostel schema: rooms, students, maintenance, complaints, visitors, fees

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-07
"""
import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("number", sa.String(20), nullable=False),
        sa.Column("block", sa.String(20), nullable=False),
        sa.Column("floor", sa.Integer(), nullable=False),
        sa.Column("room_type", sa.String(20), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("monthly_rent", sa.Numeric(10, 2), nullable=False),
    )
    op.create_index("ix_rooms_number", "rooms", ["number"], unique=True)

    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("roll_no", sa.String(30), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(120), nullable=False, unique=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("course", sa.String(80), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("guardian_phone", sa.String(20), nullable=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True),
        sa.Column("joined_on", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_students_roll_no", "students", ["roll_no"], unique=True)
    op.create_index("ix_students_room_id", "students", ["room_id"])

    op.create_table(
        "maintenance_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("priority", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_maintenance_requests_room_id", "maintenance_requests", ["room_id"])

    op.create_table(
        "complaints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("subject", sa.String(150), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("filed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_complaints_student_id", "complaints", ["student_id"])

    op.create_table(
        "visitors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("visitor_name", sa.String(120), nullable=False),
        sa.Column("relation", sa.String(40), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("purpose", sa.String(200), nullable=True),
        sa.Column("check_in", sa.DateTime(timezone=True), nullable=False),
        sa.Column("check_out", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_visitors_student_id", "visitors", ["student_id"])

    op.create_table(
        "fees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("term", sa.String(30), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("paid_on", sa.Date(), nullable=True),
        sa.Column("payment_ref", sa.String(60), nullable=True),
    )
    op.create_index("ix_fees_student_id", "fees", ["student_id"])


def downgrade() -> None:
    for table in ("fees", "visitors", "complaints", "maintenance_requests", "students", "rooms"):
        op.drop_table(table)
