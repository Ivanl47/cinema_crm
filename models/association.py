from sqlalchemy import Table, Column, Integer, ForeignKey, Numeric
from .base import Base

booking_seats = Table(
    "booking_seats",
    Base.metadata,
    Column("booking_id", Integer, ForeignKey("bookings.id"), primary_key=True),
    Column("seat_id", Integer, ForeignKey("seats.id"), primary_key=True),
    Column("price", Numeric(10, 2), nullable=True),
)
