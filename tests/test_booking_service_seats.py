from decimal import Decimal
from datetime import date, time

from services.booking_service import BookingService
from models import Hall, Seat, Film, Session as SessModel, Booking
from models.enums import BookingStatus


def test_seat_matrix_and_selection_service(db_session):
    # create hall with 2x2 layout
    hall = Hall(name="H1", capacity=4, rows=2, cols=2)
    db_session.add(hall)
    db_session.commit()

    # create seats for layout
    s1 = Seat(hall_id=hall.id, row=1, number=1)
    s2 = Seat(hall_id=hall.id, row=1, number=2)
    s3 = Seat(hall_id=hall.id, row=2, number=1)
    s4 = Seat(hall_id=hall.id, row=2, number=2)
    db_session.add_all([s1, s2, s3, s4])
    db_session.commit()

    # film + session
    film = Film(title="F", description="d", duration=90)
    db_session.add(film)
    db_session.commit()
    sess = SessModel(film_id=film.id, hall_id=hall.id, date=date.today(), time=time(12, 0), base_price=10)
    db_session.add(sess)
    db_session.commit()

    # create booking for seat (1,1) and mark confirmed
    booking = Booking(user_id=1, session_id=sess.id)
    db_session.add(booking)
    db_session.commit()
    # attach seat via booking_seats table
    from models import booking_seats
    db_session.execute(booking_seats.insert().values(booking_id=booking.id, seat_id=s1.id, price=Decimal("12.00")))
    booking.status = BookingStatus.CONFIRMED
    db_session.commit()

    svc = BookingService(db_session)
    matrix = svc.seat_matrix_for_session(sess.id)
    assert matrix == [[1, 0], [0, 0]]

    # trying to select already occupied seat should raise
    try:
        svc.create_booking_for_seat(user_id=2, session_id=sess.id, row=1, number=1)
        assert False, "expected ValueError for already booked seat"
    except ValueError:
        pass

    # selecting free seat should create booking
    b2 = svc.create_booking_for_seat(user_id=2, session_id=sess.id, row=1, number=2)
    assert b2 is not None and b2.id is not None
