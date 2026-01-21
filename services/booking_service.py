from .base import BaseService
from models.dao import BookingDAO, SessionDAO, SeatDAO, PaymentDAO
from models.enums import BookingStatus, PaymentStatus
from datetime import datetime
from sqlalchemy import select, func
from models import Session as SessionModel, booking_seats, Seat
from decimal import Decimal


class BookingService(BaseService):
    def __init__(self, session, booking_dao=None, session_dao=None, seat_dao=None, payment_dao=None):
        """BookingService may accept DAO instances for easier testing/DI.

        Backwards-compatible: when DAOs are not provided, concrete DAO
        implementations are created using the given session.
        """
        super().__init__(session)
        self.booking_dao = booking_dao if booking_dao is not None else BookingDAO(session)
        self.session_dao = session_dao if session_dao is not None else SessionDAO(session)
        self.seat_dao = seat_dao if seat_dao is not None else SeatDAO(session)
        self.payment_dao = payment_dao if payment_dao is not None else PaymentDAO(session)

    def create_booking(self, user_id: int, session_id: int, seat_ids: list[int]):
        """Create booking and attach seats in a single transaction.

        The DAO create calls are made with commit=False so the service
        manages the transaction boundary (preferred SRP / single place
        for committing).
        """
        # ensure requested seats are available for this session (no non-CANCELLED bookings)
        from models import booking_seats
        from models import Booking as BookingModel
        from models.enums import BookingStatus

        if seat_ids:
            q = (
                self.session.query(booking_seats.c.seat_id)
                .join(BookingModel, booking_seats.c.booking_id == BookingModel.id)
                .filter(BookingModel.session_id == session_id, BookingModel.status != BookingStatus.CANCELLED, booking_seats.c.seat_id.in_(seat_ids))
            )
            occupied_rows = [r[0] for r in q.all()]
            if occupied_rows:
                raise ValueError(f"seats already booked: {occupied_rows}")

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

    def list_sessions(self):
        from models import Session as SessionModel
        out = []
        qs = self.session.query(SessionModel).all()
        for s in qs:
            hall = s.hall
            out.append({
                'id': s.id,
                'film_id': s.film_id,
                'hall_id': hall.id if hall else None,
                'hall_name': hall.name if hall else None,
                'rows': hall.rows,
                'cols': hall.cols,
                'base_price': float(s.base_price) if getattr(s, 'base_price', None) is not None else None,
            })
        return out

    def list_halls(self):
        from models import Hall as HallModel
        qs = self.session.query(HallModel).all()
        out = []
        for h in qs:
            out.append({'id': h.id, 'name': h.name, 'rows': h.rows, 'cols': h.cols})
        return out

    def hall_seats(self, hall_id: int):
        from models import Seat, Hall as HallModel
        hall = self.session.query(HallModel).get(hall_id)
        if not hall:
            raise ValueError('hall not found')
        seats = self.session.query(Seat).filter(Seat.hall_id == hall_id).all()
        out = []
        for s in seats:
            out.append({'id': s.id, 'row': s.row, 'number': s.number})
        return {'seats': out, 'rows': hall.rows, 'cols': hall.cols, 'hall_name': hall.name}

    def list_seats_for_session(self, session_id: int):
        from models import Seat, Booking as BookingModel, booking_seats
        from models import Session as SessionModel
        from models.enums import BookingStatus

        sess = self.session.query(SessionModel).get(session_id)
        if not sess:
            raise ValueError('session not found')
        seats = self.session.query(Seat).filter(Seat.hall_id == sess.hall_id).all()

        out = []
        for seat in seats:
            occ = (
                self.session.query(booking_seats)
                .join(BookingModel, booking_seats.c.booking_id == BookingModel.id)
                .filter(booking_seats.c.seat_id == seat.id, BookingModel.session_id == session_id, BookingModel.status == BookingStatus.CONFIRMED)
                .first()
            )
            cat = getattr(seat, 'category', None)
            cat_val = cat.value if getattr(cat, 'value', None) is not None else cat
            out.append({'id': seat.id, 'row': seat.row, 'number': seat.number, 'occupied': bool(occ), 'category': cat_val})
        return {'seats': out, 'rows': sess.hall.rows, 'cols': sess.hall.cols}

    def list_bookings(self, user_id: int | None = None):
        from models import Booking
        q = self.session.query(Booking)
        if user_id is not None:
            q = q.filter(Booking.user_id == int(user_id))
        return q.all()

    def get_booking(self, booking_id: int):
        return self.booking_dao.get(booking_id)

    def booked_seats_for_session(self, session_id: int):
        from models import booking_seats, Booking as BookingModel, Seat
        rows = (
            self.session.query(booking_seats.c.seat_id, booking_seats.c.booking_id, booking_seats.c.price, BookingModel.user_id)
            .join(BookingModel, booking_seats.c.booking_id == BookingModel.id)
            .filter(BookingModel.session_id == session_id)
            .all()
        )
        out = []
        for seat_id, booking_id, price, user_id in rows:
            seat = self.session.query(Seat).get(seat_id)
            out.append({
                'seat_id': seat_id,
                'row': seat.row if seat else None,
                'number': seat.number if seat else None,
                'booking_id': booking_id,
                'user_id': user_id,
                'price': float(price) if price is not None else None,
            })
        return out

    def get_booking_for_seat(self, session_id: int, seat_id: int):
        from models import booking_seats, Booking as BookingModel
        row = (
            self.session.query(booking_seats.c.booking_id)
            .join(BookingModel, booking_seats.c.booking_id == BookingModel.id)
            .filter(booking_seats.c.seat_id == seat_id, BookingModel.session_id == session_id)
            .first()
        )
        if not row:
            return None
        booking_id = row[0]
        return self.get_booking(booking_id)

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
