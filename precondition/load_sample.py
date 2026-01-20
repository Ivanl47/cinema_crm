"""Seed the database with sample data if empty.

Usage:
    from app import create_app
    app = create_app()
    with app.app_context():
        from precondition.load_sample import load_sample
        load_sample()

This module avoids extra dependencies and uses built-in modules.
"""
from datetime import datetime, timedelta
import random

from models import db, Film, Hall, Seat, Session, User
from models.enums import UserRole, SeatCategory


def _create_films():
    sample_titles = [
        "The Last Horizon",
        "Midnight Garden",
        "Echoes of Tomorrow",
        "Paper Planes",
        "Neon Rivers",
    ]
    films = []
    for i, title in enumerate(sample_titles, start=1):
        f = Film(title=title, description=f"Sample description for {title}.", duration=90 + i * 10)
        films.append(f)
        db.session.add(f)
    db.session.flush()
    return films


def _create_halls_and_seats():
    halls = []
    # create 2 halls with simple seat grids
    for h_idx in range(1, 3):
        rows = 8
        cols = 10
        hall = Hall(name=f"Hall {h_idx}", rows=rows, cols=cols, capacity=rows * cols)
        db.session.add(hall)
        db.session.flush()
        # create seats
        for r in range(1, rows + 1):
            for c in range(1, cols + 1):
                # simple category distribution: front rows are premium
                if r <= 2:
                    category = SeatCategory.VIP
                elif r >= 7:
                    category = SeatCategory.BALCONY
                else:
                    category = SeatCategory.STANDARD
                seat = Seat(hall_id=hall.id, row=r, number=c, category=category)
                db.session.add(seat)
        halls.append(hall)
    db.session.flush()
    return halls


def _create_sessions(films, halls):
    sessions = []
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    for i, film in enumerate(films):
        # one session per film in each hall over the next two days
        for h in halls:
            start = now + timedelta(hours=2 + i * 3)
            sess = Session(film_id=film.id, hall_id=h.id, date=start.date(), time=start.time(), base_price=50)
            db.session.add(sess)
            sessions.append(sess)
    db.session.flush()
    return sessions


def _create_users():
    admin = User(username='admin', email='admin@example.local', password='password', role=UserRole.ADMIN)
    guest = User(username='guest', email='guest@example.local', password='password', role=UserRole.USER)
    db.session.add(admin)
    db.session.add(guest)
    db.session.flush()
    return [admin, guest]


def load_sample(force: bool = False):
    """Populate the database with sample data.

    If `force` is False, the loader will only create data when the DB appears
    empty (no films and no halls). If `force` is True, the database schema will
    be dropped and recreated and sample data will be inserted.

    Returns True if data was created, False if nothing was done.
    """
    if force:
        # destructive: drop and recreate tables then seed
        db.drop_all()
        db.create_all()
    else:
        # Quick emptiness check: any films or halls present
        if Film.query.first() or Hall.query.first():
            return False

    try:
        films = _create_films()
        halls = _create_halls_and_seats()
        sessions = _create_sessions(films, halls)
        users = _create_users()
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        raise


if __name__ == '__main__':
    print('This module is intended to be used inside the Flask app context.')
