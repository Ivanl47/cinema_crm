from .enums import SeatCategory


def init_seat_model(db):
    class Seat(db.Model):
        __tablename__ = "seats"

        id = db.Column(db.Integer, primary_key=True)
        hall_id = db.Column(db.Integer, db.ForeignKey("halls.id"), nullable=False)
        row = db.Column(db.Integer, nullable=False)
        number = db.Column(db.Integer, nullable=False)
        category = db.Column(db.Enum(SeatCategory, native_enum=False), nullable=False, default=SeatCategory.STANDARD)

        hall = db.relationship("Hall", back_populates="seats")
        bookings = db.relationship("Booking", secondary="booking_seats", back_populates="seats")

        def __repr__(self):
            return f"<Seat(id={self.id}, hall_id={self.hall_id}, row={self.row}, number={self.number})>"

    return Seat


# placeholder for import-time name binding from models.__init__
Seat = None
