"""Database models package using Flask-SQLAlchemy.

Expose `db` (SQLAlchemy instance) and initialize models via initializer
functions that accept the `db` object. This keeps import-time binding
explicit and avoids circular import issues.
"""
from flask_sqlalchemy import SQLAlchemy
from .enums import UserRole, BookingStatus, PaymentStatus, SeatCategory

# create the SQLAlchemy instance used by the application
db = SQLAlchemy()

# Import model initializers
from .film import init_film_model
from .hall import init_hall_model
from .seat import init_seat_model
from .session import init_session_model
from .booking import init_booking_model
from .payment import init_payment_model
from .user import init_user_model
from .association import init_association

# Initialize models after `db` is defined
Film = init_film_model(db)
Hall = init_hall_model(db)
Seat = init_seat_model(db)
Session = init_session_model(db)
Booking = init_booking_model(db)
Payment = init_payment_model(db)
User = init_user_model(db)
booking_seats = init_association(db)

__all__ = [
    "db",
    "UserRole",
    "BookingStatus",
    "PaymentStatus",
    "SeatCategory",
    "booking_seats",
    "User",
    "Film",
    "Hall",
    "Seat",
    "Session",
    "Booking",
    "Payment",
]
