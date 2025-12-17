from .base_dao import BaseDAO
from ..payment import Payment


class PaymentDAO(BaseDAO):
    model = Payment

    def list_for_booking(self, booking_id: int):
        return self.session.query(self.model).filter(self.model.booking_id == booking_id).all()
