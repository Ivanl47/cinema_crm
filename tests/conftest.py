import pytest
import sys
import os
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, time

# Ensure project root is on sys.path so `models` package can be imported
# Ensure project root is on sys.path so `import models` works when running pytest
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models.base import Base
from models.dao import (
    UserDAO,
    FilmDAO,
    HallDAO,
    SessionDAO,
    SeatDAO,
    BookingDAO,
    PaymentDAO,
)


@pytest.fixture(scope="session")
def engine():
    return create_engine("sqlite:///:memory:", future=True)


@pytest.fixture(scope="session")
def tables(engine):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(engine, tables):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def user_dao(db_session):
    return UserDAO(db_session)


@pytest.fixture()
def film_dao(db_session):
    return FilmDAO(db_session)


@pytest.fixture()
def hall_dao(db_session):
    return HallDAO(db_session)


@pytest.fixture()
def session_dao(db_session):
    return SessionDAO(db_session)


@pytest.fixture()
def seat_dao(db_session):
    return SeatDAO(db_session)


@pytest.fixture()
def booking_dao(db_session):
    return BookingDAO(db_session)


@pytest.fixture()
def payment_dao(db_session):
    return PaymentDAO(db_session)
