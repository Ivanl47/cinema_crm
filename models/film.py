def init_film_model(db):
    class Film(db.Model):
        __tablename__ = "films"

        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(255), nullable=False)
        description = db.Column(db.Text, nullable=True)
        duration = db.Column(db.Integer, nullable=True)  # minutes

        sessions = db.relationship("Session", back_populates="film", cascade="all, delete-orphan")

        def __repr__(self):
            return f"<Film(id={self.id}, title={self.title})>"

    return Film


# placeholder for import-time name binding from models.__init__
Film = None
