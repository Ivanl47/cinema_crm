from sqlalchemy import Column, Integer, Date, Time, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    film_id = Column(Integer, ForeignKey("films.id"), nullable=False)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)

    film = relationship("Film", back_populates="sessions")
    hall = relationship("Hall", back_populates="sessions")
    bookings = relationship("Booking", back_populates="session")

    def __repr__(self):
        return f"<Session(id={self.id}, film_id={self.film_id}, date={self.date}, time={self.time})>"
