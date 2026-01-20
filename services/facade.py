from typing import List
from .factory import ServiceFactory
from models.enums import BookingStatus



class BookingFacade:
    """Facade to orchestrate booking flows using lower-level services.

    The facade receives a `ServiceFactory` (already bound to a session)
    and calls service methods to perform higher-level operations. It
    centralizes transaction boundaries for multi-step flows when needed.
    """

    def __init__(self, factory: ServiceFactory):
        self.factory = factory
        self.booking_svc = factory.booking()
        self.user_svc = factory.user()
        self.film_svc = factory.film()
        # admin service for reporting
        try:
            self.admin_svc = factory.admin()
        except Exception:
            self.admin_svc = None

    def create_booking(self, user_id: int, session_id: int, seat_ids: List[int]):
        """Create a booking and attach seats. Returns Booking instance."""
        # Validate existence
        user = self.user_svc.get_user(user_id)
        if user is None:
            raise ValueError("user not found")

        sess = self.film_svc  # film service used for session listing; kept for possible checks

        # Delegate to booking service which controls transaction for this simple flow
        booking = self.booking_svc.create_booking(user_id=user_id, session_id=session_id, seat_ids=seat_ids)
        return booking

    def cancel_booking(self, booking_id: int):
        return self.booking_svc.cancel_booking(booking_id)

    def cancel_booking_seat(self, booking_id: int, seat_id: int):
        """Remove a single seat from a booking via booking service."""
        return self.booking_svc.remove_seat_from_booking(booking_id, seat_id)

    def pay_booking(self, booking_id: int, amount):
        # In real app: call payment gateway, then record payment
        return self.booking_svc.add_payment(booking_id, amount)

    def confirm_booking(self, booking_id: int):
        # Simple confirm: set status to CONFIRMED
        b = self.booking_svc.booking_dao.get(booking_id)
        if not b:
            return None
        b.status = BookingStatus.CONFIRMED
        self.booking_svc.session.commit()
        self.booking_svc.session.refresh(b)
        return b

    def generate_ticket(self, booking_id: int):
        # Stub: return a simple ticket representation
        booking = self.booking_svc.booking_dao.get(booking_id)
        if not booking:
            return None
        seats = [f"{s.row}-{s.number}" for s in booking.seats]
        return {
            "booking_id": booking.id,
            "user_id": booking.user_id,
            "session_id": booking.session_id,
            "seats": seats,
        }

    # --- Admin report helpers ---
    def tickets_sold_last_month(self, acting_user_id: int):
        """Return tickets sold in last 30 days. Delegates authorization to AdminService."""
        if not self.admin_svc:
            raise RuntimeError("Admin service not available")
        return self.admin_svc.tickets_sold_last_month(acting_user_id)

    def revenue_for_session(self, session_id: int, acting_user_id: int):
        """Return revenue for a session. Delegates authorization to AdminService."""
        if not self.admin_svc:
            raise RuntimeError("Admin service not available")
        return self.admin_svc.revenue_for_session(session_id, acting_user_id)


class AppFacade:
    """Higher-level facade that exposes common app operations for routers.

    This keeps controllers thin and routes all business logic through a single
    facade. The AppFacade composes the BookingFacade and delegates user/film
    related operations to the appropriate services.
    """

    def __init__(self, factory: ServiceFactory):
        self.factory = factory
        self.booking = BookingFacade(factory)
        # create dedicated services for direct operations
        self.user_svc = factory.user()
        self.film_svc = factory.film()

    # User operations
    def create_user(self, username: str, email: str, password: str, role=None):
        return self.user_svc.create_user(username=username, email=email, password=password, role=role)

    # Film operations
    def create_film(self, title: str, description: str | None, duration: int):
        # Prefer FilmService.create(...). For compatibility with older
        # implementations that might expose `create_film`, try both.
        try:
            return self.film_svc.create(title=title, description=description, duration=duration)
        except AttributeError:
            # fallback for older API
            try:
                return self.film_svc.create_film(title=title, description=description, duration=duration)
            except AttributeError:
                raise

    def list_films(self):
        return self.film_svc.list_films()
