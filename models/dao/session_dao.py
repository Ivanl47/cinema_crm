from .base_dao import BaseDAO
from ..session import Session as SessionModel


class SessionDAO(BaseDAO):
    model = SessionModel

    def list_for_film(self, film_id: int):
        return self.session.query(self.model).filter(self.model.film_id == film_id).all()
