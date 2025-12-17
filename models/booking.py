from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from .base import Base
from .enums import BookingStatus


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    booking_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(SAEnum(BookingStatus, native_enum=False), default=BookingStatus.PENDING, nullable=False)

    user = relationship("User", back_populates="bookings")
    session = relationship("Session", back_populates="bookings")
    seats = relationship("Seat", secondary="booking_seats", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Booking(id={self.id}, user_id={self.user_id}, session_id={self.session_id})>"
