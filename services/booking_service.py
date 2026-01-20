from .base import BaseService
from models.dao import BookingDAO, SessionDAO, SeatDAO, PaymentDAO
from models.enums import BookingStatus, PaymentStatus
from datetime import datetime
from sqlalchemy import select, func
from models import Session as SessionModel, booking_seats, Seat
from decimal import Decimal


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

    def remove_seat_from_booking(self, booking_id: int, seat_id: int):
        """Remove a single seat from a booking. If the booking becomes empty,
        mark it as CANCELLED. Returns the updated booking or None if not found.
        """
        booking = self.booking_dao.get(booking_id)
        if not booking:
            return None

        seat = self.seat_dao.get(seat_id)
        if not seat:
            return None

        # Detach the seat if it's part of the booking
        if seat in booking.seats:
            booking.seats.remove(seat)
            # If no seats left, cancel booking
            if not booking.seats:
                booking.status = BookingStatus.CANCELLED
            self.session.commit()
            self.session.refresh(booking)
            return booking

        return None

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

    def seat_matrix_for_session(self, session_id: int) -> list[list[int]]:
        """Return a 2D matrix (rows x cols) with 1 for occupied seats and 0 for free.

        Uses hall.rows/cols if available, otherwise derives dimensions from seats.
        Counts seats as occupied if attached to a booking for this session with status CONFIRMED.
        """
        sess = self.session_dao.get(session_id)
        if not sess:
            raise ValueError("session not found")
        hall = sess.hall
        # determine dimensions
        if hall.rows and hall.cols:
            rows, cols = hall.rows, hall.cols
        else:
            # derive from existing seats
            q = select(func.max(Seat.row), func.max(Seat.number)).where(Seat.hall_id == hall.id)
            rmax, cmax = self.session.execute(q).scalar_one()
            rows = rmax or 0
            cols = cmax or 0

        # empty matrix
        matrix = [[0 for _ in range(cols)] for _ in range(rows)]

        # query occupied seats for this session via Booking model
        from models import Booking as BookingModel

        occ_q = (
            select(Seat.id, Seat.row, Seat.number)
            .select_from(Seat.__table__.join(booking_seats, Seat.id == booking_seats.c.seat_id).join(BookingModel, booking_seats.c.booking_id == BookingModel.id))
            .where(BookingModel.session_id == session_id, BookingModel.status == BookingStatus.CONFIRMED)
        )
        rows_iter = self.session.execute(occ_q).all()
        for sid, r, c in rows_iter:
            if r and c and 1 <= r <= rows and 1 <= c <= cols:
                matrix[r - 1][c - 1] = 1

        return matrix

    def create_booking_for_seat(self, user_id: int, session_id: int, row: int, number: int):
        """Create booking for a specific seat (row/number) if available."""
        sess = self.session_dao.get(session_id)
        if not sess:
            raise ValueError("session not found")
        hall = sess.hall
        seat = self.session.query(Seat).filter(Seat.hall_id == hall.id, Seat.row == row, Seat.number == number).first()
        if not seat:
            raise ValueError("seat not found")

        # check if seat already booked for this session (pending or confirmed)
        from models import Booking as BookingModel

        occ = (
            self.session.query(booking_seats)
            .join(BookingModel, booking_seats.c.booking_id == BookingModel.id)
            .filter(booking_seats.c.seat_id == seat.id, BookingModel.session_id == session_id)
            .first()
        )
        if occ:
            raise ValueError("seat already booked")

        return self.create_booking(user_id=user_id, session_id=session_id, seat_ids=[seat.id])
