from .base import BaseService
from models.dao import UserDAO


class UserService(BaseService):
    def __init__(self, session):
        super().__init__(session)
        self.dao = UserDAO(session)

    def create_user(self, username: str, email: str, password: str, role: str = None):
        payload = {"username": username, "email": email, "password": password}
        if role is not None:
            payload["role"] = role
        return self.dao.create(**payload)

    def get_user(self, user_id: int):
        return self.dao.get(user_id)

    def find_by_username(self, username: str):
        return self.dao.find_by_username(username)
