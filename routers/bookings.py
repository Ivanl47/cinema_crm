from flask import Blueprint, jsonify, request
from services.factory import ServiceFactory
from services.facade import BookingFacade


def create_bookings_blueprint(session_factory):
    bp = Blueprint('bookings', __name__, url_prefix='/bookings')

    @bp.route('', methods=['POST'])
    def create_booking():
        data = request.get_json() or {}
        user_id = data.get('user_id')
        session_id = data.get('session_id')
        seat_ids = data.get('seat_ids', [])
        if not (user_id and session_id and seat_ids):
            return jsonify({'error': 'user_id, session_id and seat_ids required'}), 400

        session = session_factory()
        try:
            factory = ServiceFactory(session)
            facade = BookingFacade(factory)
            booking = facade.create_booking(user_id=user_id, session_id=session_id, seat_ids=seat_ids)
            return jsonify({'id': booking.id, 'status': str(booking.status)}), 201
        except ValueError as e:
            session.rollback()
            return jsonify({'error': str(e)}), 400
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @bp.route('/sessions/<int:session_id>/matrix', methods=['GET'])
    def seat_matrix(session_id: int):
        session = session_factory()
        try:
            factory = ServiceFactory(session)
            booking_svc = factory.booking()
            matrix = booking_svc.seat_matrix_for_session(session_id)
            return jsonify({'matrix': matrix}), 200
        except ValueError as e:
            session.rollback()
            return jsonify({'error': str(e)}), 404
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @bp.route('/sessions/<int:session_id>/select', methods=['POST'])
    def select_seat(session_id: int):
        data = request.get_json() or {}
        user_id = data.get('user_id')
        row = data.get('row')
        number = data.get('number')
        if not (user_id and row and number):
            return jsonify({'error': 'user_id, row and number required'}), 400

        session = session_factory()
        try:
            factory = ServiceFactory(session)
            booking_svc = factory.booking()
            booking = booking_svc.create_booking_for_seat(user_id=user_id, session_id=session_id, row=row, number=number)
            return jsonify({'id': booking.id, 'status': str(booking.status)}), 201
        except ValueError as e:
            session.rollback()
            return jsonify({'error': str(e)}), 400
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    @bp.route('/sessions', methods=['GET'])
    def list_sessions():
        session = session_factory()
        try:
            from models import Session as SessionModel
            q = session.query(SessionModel).all()
            out = []
            for s in q:
                hall = s.hall
                out.append({
                    'id': s.id,
                    'film_id': s.film_id,
                    'hall_id': hall.id if hall else None,
                    'hall_name': hall.name if hall else None,
                    'rows': hall.rows,
                    'cols': hall.cols,
                })
            return jsonify({'sessions': out}), 200
        finally:
            session.close()

    @bp.route('/halls', methods=['GET'])
    def list_halls():
        session = session_factory()
        try:
            from models import Hall as HallModel
            qs = session.query(HallModel).all()
            out = []
            for h in qs:
                out.append({'id': h.id, 'name': h.name, 'rows': h.rows, 'cols': h.cols})
            return jsonify({'halls': out}), 200
        finally:
            session.close()

    @bp.route('/halls/<int:hall_id>/seats', methods=['GET'])
    def hall_seats(hall_id: int):
        session = session_factory()
        try:
            from models import Seat, Hall as HallModel
            hall = session.query(HallModel).get(hall_id)
            if not hall:
                return jsonify({'error': 'hall not found'}), 404
            seats = session.query(Seat).filter(Seat.hall_id == hall_id).all()
            out = []
            for s in seats:
                out.append({'id': s.id, 'row': s.row, 'number': s.number})
            return jsonify({'seats': out, 'rows': hall.rows, 'cols': hall.cols, 'hall_name': hall.name}), 200
        finally:
            session.close()

    @bp.route('/sessions/<int:session_id>/seats', methods=['GET'])
    def list_seats(session_id: int):
        session = session_factory()
        try:
            from models import Seat, Booking as BookingModel, booking_seats
            from models.enums import BookingStatus

            # Determine the session and fetch seats by its hall (avoid boolean-evaluated SQL clauses)
            from models import Session as SessionModel
            sess = session.query(SessionModel).get(session_id)
            if not sess:
                return jsonify({'error': 'session not found'}), 404
            seats = session.query(Seat).filter(Seat.hall_id == sess.hall_id).all()

            out = []
            for seat in seats:
                occ = (
                    session.query(booking_seats)
                    .join(BookingModel, booking_seats.c.booking_id == BookingModel.id)
                    .filter(booking_seats.c.seat_id == seat.id, BookingModel.session_id == session_id, BookingModel.status == BookingStatus.CONFIRMED)
                    .first()
                )
                out.append({'id': seat.id, 'row': seat.row, 'number': seat.number, 'occupied': bool(occ)})
            return jsonify({'seats': out, 'rows': sess.hall.rows, 'cols': sess.hall.cols}), 200
        finally:
            session.close()

    @bp.route('/sessions/<int:session_id>/purchase', methods=['POST'])
    def purchase(session_id: int):
        data = request.get_json() or {}
        user_id = data.get('user_id')
        seat_ids = data.get('seat_ids', [])
        card = data.get('card', '')
        if not (user_id and seat_ids and card is not None):
            return jsonify({'error': 'user_id, seat_ids and card required'}), 400

        session = session_factory()
        try:
            factory = ServiceFactory(session)
            facade = BookingFacade(factory)
            # create booking
            booking = facade.create_booking(user_id=user_id, session_id=session_id, seat_ids=seat_ids)

            # validate card: digits only -> success, else cancel
            if not card.isdigit():
                # cancel booking
                facade.cancel_booking(booking.id)
                session.rollback()
                return jsonify({'error': 'invalid card, booking cancelled'}), 400

            # compute amount (use session base_price * seats)
            from models import Session as SessionModel
            sess = session.query(SessionModel).get(session_id)
            amount = float(sess.base_price) * len(seat_ids)

            # record payment and confirm
            facade.pay_booking(booking.id, amount)
            facade.confirm_booking(booking.id)

            # return updated matrix
            booking_svc = factory.booking()
            matrix = booking_svc.seat_matrix_for_session(session_id)
            return jsonify({'matrix': matrix, 'booking_id': booking.id}), 201
        except ValueError as e:
            session.rollback()
            return jsonify({'error': str(e)}), 400
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @bp.route('', methods=['GET'])
    def list_bookings():
        """List bookings. Optional query param `user_id` filters by user."""
        user_id = request.args.get('user_id')
        session = session_factory()
        try:
            from models import Booking
            q = session.query(Booking)
            if user_id:
                try:
                    uid = int(user_id)
                    q = q.filter(Booking.user_id == uid)
                except ValueError:
                    return jsonify({'error': 'invalid user_id'}), 400
            books = q.all()
            out = []
            for b in books:
                out.append({
                    'id': b.id,
                    'user_id': b.user_id,
                    'session_id': b.session_id,
                    'status': str(b.status),
                    'seat_ids': [s.id for s in b.seats],
                })
            return jsonify({'bookings': out}), 200
        finally:
            session.close()

    @bp.route('/<int:booking_id>', methods=['GET'])
    def get_booking(booking_id: int):
        session = session_factory()
        try:
            from models import Booking
            b = session.query(Booking).get(booking_id)
            if not b:
                return jsonify({'error': 'booking not found'}), 404
            return jsonify({
                'id': b.id,
                'user_id': b.user_id,
                'session_id': b.session_id,
                'status': str(b.status),
                'seat_ids': [s.id for s in b.seats],
            }), 200
        finally:
            session.close()

    @bp.route('/sessions/<int:session_id>/booked', methods=['GET'])
    def booked_seats(session_id: int):
        """Return list of booked seats for given session (includes booking id and price if present)."""
        session = session_factory()
        try:
            from models import booking_seats, Booking as BookingModel, Seat
            # include booking owner (user_id) in results to allow owner-specific actions
            rows = (
                session.query(booking_seats.c.seat_id, booking_seats.c.booking_id, booking_seats.c.price, BookingModel.user_id)
                .join(BookingModel, booking_seats.c.booking_id == BookingModel.id)
                .filter(BookingModel.session_id == session_id)
                .all()
            )
            out = []
            for seat_id, booking_id, price, user_id in rows:
                seat = session.query(Seat).get(seat_id)
                out.append({
                    'seat_id': seat_id,
                    'row': seat.row if seat else None,
                    'number': seat.number if seat else None,
                    'booking_id': booking_id,
                    'user_id': user_id,
                    'price': float(price) if price is not None else None,
                })
            return jsonify({'booked_seats': out}), 200
        finally:
            session.close()

    @bp.route('/sessions/<int:session_id>/seats/<int:seat_id>/cancel', methods=['POST'])
    def cancel_seat(session_id: int, seat_id: int):
        data = request.get_json() or {}
        acting_user_id = data.get('acting_user_id')
        if not acting_user_id:
            return jsonify({'error': 'acting_user_id required'}), 400

        session = session_factory()
        try:
            factory = ServiceFactory(session)
            user_svc = factory.user()
            from models import booking_seats, Booking as BookingModel

            # find the booking that contains this seat for the session
            row = (
                session.query(booking_seats.c.booking_id)
                .join(BookingModel, booking_seats.c.booking_id == BookingModel.id)
                .filter(booking_seats.c.seat_id == seat_id, BookingModel.session_id == session_id)
                .first()
            )
            if not row:
                return jsonify({'error': 'booking not found for seat'}), 404
            booking_id = row[0]

            # fetch booking to check ownership
            booking = session.query(BookingModel).get(booking_id)
            if not booking:
                return jsonify({'error': 'booking not found'}), 404

            # allow if acting user is admin or owner of booking
            try:
                is_admin = user_svc.is_admin(int(acting_user_id))
            except Exception:
                is_admin = False
            if not is_admin and int(booking.user_id) != int(acting_user_id):
                return jsonify({'error': 'forbidden: not owner or admin'}), 403

            facade = BookingFacade(factory)
            # remove only the selected seat from the found booking
            updated = facade.cancel_booking_seat(booking_id, seat_id)
            if not updated:
                return jsonify({'error': 'failed to cancel seat'}), 400
            return jsonify({'booking_id': updated.id, 'status': str(updated.status)}), 200
        finally:
            session.close()

    return bp
