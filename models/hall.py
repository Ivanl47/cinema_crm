def init_hall_model(db):
    class Hall(db.Model):
        __tablename__ = "halls"

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        capacity = db.Column(db.Integer, nullable=False)
        # optional layout dimensions: number of rows and columns in the hall
        rows = db.Column(db.Integer, nullable=True)
        cols = db.Column(db.Integer, nullable=True)

        seats = db.relationship("Seat", back_populates="hall", cascade="all, delete-orphan")
        sessions = db.relationship("Session", back_populates="hall")

        def __repr__(self):
            return f"<Hall(id={self.id}, name={self.name})>"

    return Hall


# placeholder for import-time name binding from models.__init__
Hall = None
