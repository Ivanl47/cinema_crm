def init_association(db):
    booking_seats = db.Table(
        "booking_seats",
        db.metadata,
        db.Column("booking_id", db.Integer, db.ForeignKey("bookings.id"), primary_key=True),
        db.Column("seat_id", db.Integer, db.ForeignKey("seats.id"), primary_key=True),
        db.Column("price", db.Numeric(10, 2), nullable=True),
    )

    return booking_seats


# placeholder for import-time binding
booking_seats = None
