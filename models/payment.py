from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Numeric, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from .enums import PaymentStatus


def init_payment_model(db):
    class Payment(db.Model):
        __tablename__ = "payments"

        id = db.Column(db.Integer, primary_key=True)
        booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
        amount = db.Column(db.Numeric(10, 2), nullable=False)
        payment_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
        status = db.Column(db.Enum(PaymentStatus, native_enum=False), default=PaymentStatus.INIT, nullable=False)

        booking = db.relationship("Booking", back_populates="payments")

        def __repr__(self):
            return f"<Payment(id={self.id}, booking_id={self.booking_id}, amount={self.amount})>"

    return Payment


# placeholder for import-time name binding from models.__init__
Payment = None
