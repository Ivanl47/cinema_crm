from decimal import Decimal
from datetime import date, time

from services.user_service import UserService
from services.admin_service import AdminService
from models.enums import UserRole, BookingStatus
from models import booking_seats


def test_user_service_hash_and_verify(db_session):
    svc = UserService(db_session)
    user = svc.create_user(username="tester", email="t@example.com", password="s3cret")
    assert user.password != "s3cret"
    assert svc.verify_password(user, "s3cret") is True
    assert svc.verify_password(user, "wrong") is False


def test_admin_reports_and_permissions(
    db_session, user_dao, film_dao, hall_dao, session_dao, seat_dao, booking_dao
):
    # create users
    admin = user_dao.create(username="admin", email="a@e", password="p", role=UserRole.ADMIN)
    user = user_dao.create(username="u", email="u@e", password="p", role=UserRole.USER)

    # create film/hall/session
    film = film_dao.create(title="F", description="d", duration=100)
    hall = hall_dao.create(name="H", capacity=10)
    sess = session_dao.create(film_id=film.id, hall_id=hall.id, date=date(2025, 11, 1), time=time(12, 0), base_price=12.50)

    # create seats
    s1 = seat_dao.create(hall_id=hall.id, row=1, number=1)
    s2 = seat_dao.create(hall_id=hall.id, row=1, number=2)

    # create a booking and mark confirmed
    booking = booking_dao.create(user_id=user.id, session_id=sess.id)
    # insert association rows with one explicit price and one NULL (to use session base_price)
    db_session.execute(
        booking_seats.insert(),
        [
            {"booking_id": booking.id, "seat_id": s1.id, "price": Decimal("15.00")},
            {"booking_id": booking.id, "seat_id": s2.id, "price": None},
        ],
    )
    booking.status = BookingStatus.CONFIRMED
    db_session.commit()

    admin_svc = AdminService(db_session)

    # admin can get tickets sold (at least the two seats we attached)
    sold = admin_svc.tickets_sold_last_month(admin.id)
    assert sold >= 2

    # revenue: 15.00 + session.base_price (12.50) = 27.50
    revenue = admin_svc.revenue_for_session(sess.id, admin.id)
    assert Decimal(revenue) == Decimal("27.50")

    # non-admin cannot call
    try:
        admin_svc.tickets_sold_last_month(user.id)
        assert False, "non-admin should not be allowed"
    except PermissionError:
        pass
