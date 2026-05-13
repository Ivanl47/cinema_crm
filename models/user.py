from .enums import UserRole, ConcessionCategory


def init_user_model(db):
    class User(db.Model):
        __tablename__ = "users"

        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(100), nullable=False, unique=True)
        email = db.Column(db.String(255), nullable=False, unique=True)
        password = db.Column(db.String(255), nullable=False)
        role = db.Column(db.Enum(UserRole, native_enum=False), default=UserRole.USER, nullable=False)
        concession = db.Column(db.Enum(ConcessionCategory, native_enum=False), default=ConcessionCategory.NONE, nullable=False)

        bookings = db.relationship("Booking", back_populates="user")

        def __repr__(self):
            return f"<User(id={self.id}, username={self.username})>"

    return User


# placeholder for import-time name binding from models.__init__
User = None
