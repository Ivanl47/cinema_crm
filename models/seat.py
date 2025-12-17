from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from .base import Base
from .enums import SeatCategory


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)
    row = Column(Integer, nullable=False)
    number = Column(Integer, nullable=False)
    category = Column(SAEnum(SeatCategory, native_enum=False), nullable=False, default=SeatCategory.STANDARD)

    hall = relationship("Hall", back_populates="seats")
    bookings = relationship("Booking", secondary="booking_seats", back_populates="seats")

    def __repr__(self):
        return f"<Seat(id={self.id}, hall_id={self.hall_id}, row={self.row}, number={self.number})>"
