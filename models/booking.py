from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from .enums import BookingStatus


def init_booking_model(db):
    class Booking(db.Model):
        __tablename__ = "bookings"

        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
        session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=False)
        booking_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
        status = db.Column(db.Enum(BookingStatus, native_enum=False), default=BookingStatus.PENDING, nullable=False)

        user = db.relationship("User", back_populates="bookings")
        session = db.relationship("Session", back_populates="bookings")
        seats = db.relationship("Seat", secondary="booking_seats", back_populates="bookings")
        payments = db.relationship("Payment", back_populates="booking", cascade="all, delete-orphan")

        def __repr__(self):
            return f"<Booking(id={self.id}, user_id={self.user_id}, session_id={self.session_id})>"

    return Booking


# placeholder for import-time name binding from models.__init__
Booking = None
