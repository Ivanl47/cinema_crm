from datetime import date, time


def test_booking_flow(db_session, user_dao, film_dao, hall_dao, session_dao, booking_dao):
    # create prerequisites
    user = user_dao.create(username="bob", email="bob@example.com", password="p")
    film = film_dao.create(title="B Movie", description="x", duration=90)
    hall = hall_dao.create(name="Main", capacity=50)

    sess = session_dao.create(film_id=film.id, hall_id=hall.id, date=date(2025, 1, 1), time=time(12, 0), base_price=10.0)

    # create booking
    booking = booking_dao.create(user_id=user.id, session_id=sess.id)
    assert booking.id is not None

    # list for user
    user_bookings = booking_dao.list_for_user(user.id)
    assert any(b.id == booking.id for b in user_bookings)

    # cleanup
    booking_dao.delete(booking)
    assert booking_dao.get(booking.id) is None
