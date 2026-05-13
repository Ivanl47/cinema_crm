from .base import BaseService
from models.dao import UserDAO
from models.enums import UserRole
from werkzeug.security import generate_password_hash, check_password_hash


class UserService(BaseService):
    def __init__(self, session, user_dao=None):
        """UserService may accept a `user_dao` for testing/DI. Backwards-compatible."""
        super().__init__(session)
        self.dao = user_dao if user_dao is not None else UserDAO(session)

    def create_user(self, username: str, email: str, password: str, role: UserRole | str | None = None, concession: str | None = None):
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
        # optionally set concession category (expects string matching ConcessionCategory)
        if concession is not None:
            payload["concession"] = concession
        return self.dao.create(**payload)

    def get_user(self, user_id: int):
        return self.dao.get(user_id)

    def find_by_username(self, username: str):
        return self.dao.find_by_username(username)

    def list_users(self, offset: int = 0, limit: int = 100):
        return self.dao.list(offset=offset, limit=limit)

    def update_user_role(self, user, role):
        return self.dao.update(user, role=role)

    def delete_user(self, user):
        return self.dao.delete(user)

    def list_admins(self):
        from models import User as UserModel
        from models.enums import UserRole
        qs = self.dao.session.query(UserModel).filter(UserModel.role == UserRole.ADMIN).all()
        out = []
        for u in qs:
            if getattr(u, 'username', '').lower() == 'root':
                continue
            out.append(u)
        return out

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
