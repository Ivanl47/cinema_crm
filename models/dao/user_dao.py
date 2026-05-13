from .base_dao import BaseDAO
from models import User


class UserDAO(BaseDAO):
    model = User

    def find_by_username(self, username: str):
        return self.session.query(self.model).filter(self.model.username == username).first()
