from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base


class Hall(Base):
    __tablename__ = "halls"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)

    seats = relationship("Seat", back_populates="hall", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="hall")

    def __repr__(self):
        return f"<Hall(id={self.id}, name={self.name})>"
