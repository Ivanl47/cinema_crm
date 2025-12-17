from .base import BaseService
from models.dao import FilmDAO


class FilmService(BaseService):
    def __init__(self, session):
        super().__init__(session)
        self.dao = FilmDAO(session)

    def list_films(self, offset=0, limit=100):
        return self.dao.list(offset=offset, limit=limit)

    def get(self, film_id):
        return self.dao.get(film_id)

    def create(self, title: str, description: str = None, duration: int = None):
        return self.dao.create(title=title, description=description, duration=duration)
