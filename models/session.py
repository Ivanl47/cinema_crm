def init_session_model(db):
    class Session(db.Model):
        __tablename__ = "sessions"

        id = db.Column(db.Integer, primary_key=True)
        film_id = db.Column(db.Integer, db.ForeignKey("films.id"), nullable=False)
        hall_id = db.Column(db.Integer, db.ForeignKey("halls.id"), nullable=False)
        date = db.Column(db.Date, nullable=False)
        time = db.Column(db.Time, nullable=False)
        base_price = db.Column(db.Numeric(10, 2), nullable=False)

        film = db.relationship("Film", back_populates="sessions")
        hall = db.relationship("Hall", back_populates="sessions")
        bookings = db.relationship("Booking", back_populates="session")

        def __repr__(self):
            return f"<Session(id={self.id}, film_id={self.film_id}, date={self.date}, time={self.time})>"

    return Session


# placeholder for import-time name binding from models.__init__
Session = None
