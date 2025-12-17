from .base import BaseService
from models.dao import BookingDAO, SessionDAO, SeatDAO, PaymentDAO
from models import Booking
from models.enums import BookingStatus, PaymentStatus
from datetime import datetime


class BookingService(BaseService):
    def __init__(self, session):
        super().__init__(session)
        self.booking_dao = BookingDAO(session)
        self.session_dao = SessionDAO(session)
        self.seat_dao = SeatDAO(session)
        self.payment_dao = PaymentDAO(session)

    def create_booking(self, user_id: int, session_id: int, seat_ids: list[int]):
        """Create booking and attach seats in a single transaction.

        The DAO create calls are made with commit=False so the service
        manages the transaction boundary (preferred SRP / single place
        for committing).
        """
        booking = self.booking_dao.create(user_id=user_id, session_id=session_id, commit=False)
        for sid in seat_ids:
            seat = self.seat_dao.get(sid)
            if seat:
                booking.seats.append(seat)
        # commit once for entire operation
        self.session.commit()
        # refresh booking to ensure relationships are loaded
        self.session.refresh(booking)
        return booking

    def cancel_booking(self, booking_id: int):
        booking = self.booking_dao.get(booking_id)
        if not booking:
            return None
        booking.status = BookingStatus.CANCELLED
        self.session.commit()
        self.session.refresh(booking)
        return booking

    def add_payment(self, booking_id: int, amount):
        payment = self.payment_dao.create(
            booking_id=booking_id,
            amount=amount,
            payment_date=datetime.utcnow(),
            status=PaymentStatus.PAID,
            commit=False,
        )
        self.session.commit()
        self.session.refresh(payment)
        return payment
