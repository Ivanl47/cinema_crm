import json
from flask import Flask
from sqlalchemy.orm import sessionmaker

from models import Base, Hall, Seat, Film, Session as SessModel


def test_bookings_routes_matrix_and_select(engine, tables):
    # create a sessionmaker bound to the test engine
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # create initial data using a fresh session
    s = Session()
    try:
        hall = Hall(name="R", capacity=4, rows=2, cols=2)
        s.add(hall)
        s.commit()

        # seats
        from models.enums import SeatCategory
        seat1 = Seat(hall_id=hall.id, row=1, number=1, category=SeatCategory.STANDARD)
        seat2 = Seat(hall_id=hall.id, row=1, number=2, category=SeatCategory.STANDARD)
        s.add_all([seat1, seat2])
        s.commit()

        film = Film(title="RouteF", description="x", duration=80)
        s.add(film)
        s.commit()
        from datetime import date, time

        sess = SessModel(film_id=film.id, hall_id=hall.id, date=date.today(), time=time(12, 0), base_price=9.5)
        s.add(sess)
        s.commit()
        session_id = sess.id
    finally:
        s.close()

    # import blueprint factory by loading the module directly to avoid package import issues
    import importlib.util
    spec = importlib.util.spec_from_file_location("bookings_module", "./routers/bookings.py")
    mod = importlib.util.module_from_spec(spec)
    # ensure project root is on sys.path so `cinema_crm` package imports work
    import os, sys
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    spec.loader.exec_module(mod)
    create_bookings_blueprint = mod.create_bookings_blueprint

    # create test Flask app and register blueprint with session factory
    app = Flask(__name__)
    app.register_blueprint(create_bookings_blueprint(lambda: Session()))

    client = app.test_client()

    # matrix should be available
    r = client.get(f"/bookings/sessions/{session_id}/matrix")
    assert r.status_code == 200
    data = r.get_json()
    assert "matrix" in data

    # select seat (1,1) for user 1
    payload = {"user_id": 1, "row": 1, "number": 1}
    r2 = client.post(f"/bookings/sessions/{session_id}/select", data=json.dumps(payload), content_type="application/json")
    assert r2.status_code == 201
    j = r2.get_json()
    assert "id" in j and "status" in j
