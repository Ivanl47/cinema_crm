from typing import Optional
from .base_dao import BaseDAO
from models import Seat


class SeatDAO(BaseDAO):
    model = Seat

    def find_in_hall(self, hall_id: int, row: Optional[int] = None):
        q = self.session.query(self.model).filter(self.model.hall_id == hall_id)
        if row is not None:
            q = q.filter(self.model.row == row)
        return q.all()
