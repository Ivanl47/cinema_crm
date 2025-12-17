from .film_service import FilmService
from .user_service import UserService
from .booking_service import BookingService


class ServiceFactory:
    """Create service instances bound to a SQLAlchemy session."""

    def __init__(self, session):
        self.session = session

    def film(self):
        return FilmService(self.session)

    def user(self):
        return UserService(self.session)

    def booking(self):
        return BookingService(self.session)
