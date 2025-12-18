from .base_dao import BaseDAO
from models import Film


class FilmDAO(BaseDAO):
    model = Film

    def find_by_title(self, title: str):
        return self.session.query(self.model).filter(self.model.title == title).all()
