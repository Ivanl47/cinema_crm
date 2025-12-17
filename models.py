from datetime import datetime, date, time
from decimal import Decimal
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Time,
    DateTime,
    Numeric,
    ForeignKey,
    Table,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class UserRole(enum.Enum):
    GUEST = "GUEST"
    USER = "USER"
    ADMIN = "ADMIN"


# Seat categories are stored as simple strings on `Seat.category` (no enum)


class BookingStatus(enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class PaymentStatus(enum.Enum):
    INIT = "INIT"
    PAID = "PAID"
    FAILED = "FAILED"


# Association table between bookings and seats (many-to-many)
booking_seats = Table(
    "booking_seats",
    Base.metadata,
    Column("booking_id", Integer, ForeignKey("bookings.id"), primary_key=True),
    Column("seat_id", Integer, ForeignKey("seats.id"), primary_key=True),
    Column("price", Numeric(10, 2), nullable=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole, native_enum=False), default=UserRole.USER, nullable=False)

    bookings = relationship("Booking", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Film(Base):
    __tablename__ = "films"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    duration = Column(Integer, nullable=True)  # minutes

    sessions = relationship("Session", back_populates="film", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Film(id={self.id}, title={self.title})>"


class Hall(Base):
    __tablename__ = "halls"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)

    seats = relationship("Seat", back_populates="hall", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="hall")

    def __repr__(self):
        return f"<Hall(id={self.id}, name={self.name})>"


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True)
    hall_id = Column(Integer, ForeignKey("halls.id"), nullable=False)
    row = Column(Integer, nullable=False)
    number = Column(Integer, nullable=False)
    category = Column(String(50), nullable=False, default="REGULAR")

    hall = relationship("Hall", back_populates="seats")
    bookings = relationship("Booking", secondary=booking_seats, back_populates="seats")

    def __repr__(self):
        return f"<Seat(id={self.id}, hall_id={self.hall_id}, row={self.row}, number={self.number})>"


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


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    booking_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(SAEnum(BookingStatus, native_enum=False), default=BookingStatus.PENDING, nullable=False)

    user = relationship("User", back_populates="bookings")
    session = relationship("Session", back_populates="bookings")
    seats = relationship("Seat", secondary=booking_seats, back_populates="bookings")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Booking(id={self.id}, user_id={self.user_id}, session_id={self.session_id})>"


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
