from .base import BaseService
from models.dao import UserDAO
from models.enums import UserRole
from werkzeug.security import generate_password_hash, check_password_hash


class UserService(BaseService):
    def __init__(self, session):
        super().__init__(session)
        self.dao = UserDAO(session)

    def create_user(self, username: str, email: str, password: str, role: UserRole | str | None = None):
        """Create a user. Defaults to `UserRole.USER` if no role provided."""
        """Create a user. Defaults to `UserRole.USER` if no role provided.

        Passwords are hashed before being stored.
        """
        hashed = generate_password_hash(password)
        payload = {"username": username, "email": email, "password": hashed}
        if role is None:
            payload["role"] = UserRole.USER
        else:
            payload["role"] = role
        return self.dao.create(**payload)

    def get_user(self, user_id: int):
        return self.dao.get(user_id)

    def find_by_username(self, username: str):
        return self.dao.find_by_username(username)

    def is_admin(self, user_id: int) -> bool:
        """Return True if the user has an admin role."""
        user = self.get_user(user_id)
        if not user:
            return False
        return getattr(user, "role", None) == UserRole.ADMIN

    def verify_password(self, user, password: str) -> bool:
        """Verify a plaintext password against the stored hash on a `User` instance."""
        if not user:
            return False
        return check_password_hash(user.password, password)
