from .base_dao import BaseDAO
from ..booking import Booking


class BookingDAO(BaseDAO):
    model = Booking

    def list_for_user(self, user_id: int):
        return self.session.query(self.model).filter(self.model.user_id == user_id).all()
