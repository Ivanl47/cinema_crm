from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base


class Film(Base):
    __tablename__ = "films"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)  # minutes

    sessions = relationship("Session", back_populates="film", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Film(id={self.id}, title={self.title})>"
