from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Numeric, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from .base import Base
from .enums import PaymentStatus


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(SAEnum(PaymentStatus, native_enum=False), default=PaymentStatus.INIT, nullable=False)

    booking = relationship("Booking", back_populates="payments")

    def __repr__(self):
        return f"<Payment(id={self.id}, booking_id={self.booking_id}, amount={self.amount})>"
