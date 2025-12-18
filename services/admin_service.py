from .base import BaseService
from models import booking_seats, Booking, Session
from models.enums import BookingStatus, UserRole
from models.dao import UserDAO
from sqlalchemy import select, func
from datetime import datetime, timedelta
from decimal import Decimal


class AdminService(BaseService):
    """Administrative reporting methods.

    This service performs its own authorization checks so callers (like the
    Facade or controllers) don't need to duplicate role logic.
    """

    def __init__(self, session):
        super().__init__(session)
        self.user_dao = UserDAO(session)

    def _ensure_admin(self, acting_user_id: int):
        user = self.user_dao.get(acting_user_id)
        if not user or getattr(user, "role", None) != UserRole.ADMIN:
            raise PermissionError("admin access required")

    def tickets_sold_last_month(self, acting_user_id: int) -> int:
        """Return the total number of seats sold (booked & confirmed) in the last 30 days.

        Requires `acting_user_id` to belong to an admin user.
        """
        self._ensure_admin(acting_user_id)
        cutoff = datetime.utcnow() - timedelta(days=30)
        stmt = (
            select(func.count())
            .select_from(booking_seats.join(Booking, booking_seats.c.booking_id == Booking.id))
            .where(Booking.booking_date >= cutoff, Booking.status == BookingStatus.CONFIRMED)
        )
        result = self.session.execute(stmt).scalar_one()
        return int(result or 0)

    def revenue_for_session(self, session_id: int, acting_user_id: int) -> Decimal:
        """Calculate total revenue (sum of seat prices or session base_price fallback).

        Requires `acting_user_id` to belong to an admin user.
        Only counts seats attached to bookings that are CONFIRMED.
        """
        self._ensure_admin(acting_user_id)
        coalesce_sum = func.sum(func.coalesce(booking_seats.c.price, Session.base_price))
        stmt = (
            select(coalesce_sum)
            .select_from(booking_seats.join(Booking, booking_seats.c.booking_id == Booking.id).join(Session, Booking.session_id == Session.id))
            .where(Session.id == session_id, Booking.status == BookingStatus.CONFIRMED)
        )
        result = self.session.execute(stmt).scalar_one()
        if result is None:
            return Decimal("0.00")
        return Decimal(result)
