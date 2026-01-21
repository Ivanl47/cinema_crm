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
            factory = ServiceFactory(session)
            booking_svc = factory.booking()
            out = booking_svc.list_sessions()
            return jsonify({'sessions': out}), 200
        finally:
            session.close()

    @bp.route('/halls', methods=['GET'])
    def list_halls():
        session = session_factory()
        try:
            factory = ServiceFactory(session)
            booking_svc = factory.booking()
            out = booking_svc.list_halls()
            return jsonify({'halls': out}), 200
        finally:
            session.close()

    @bp.route('/halls/<int:hall_id>/seats', methods=['GET'])
    def hall_seats(hall_id: int):
        session = session_factory()
        try:
            factory = ServiceFactory(session)
            booking_svc = factory.booking()
            try:
                result = booking_svc.hall_seats(hall_id)
            except ValueError as e:
                return jsonify({'error': str(e)}), 404
            return jsonify(result), 200
        finally:
            session.close()

    @bp.route('/sessions/<int:session_id>/seats', methods=['GET'])
    def list_seats(session_id: int):
        session = session_factory()
        try:
            factory = ServiceFactory(session)
            booking_svc = factory.booking()
            try:
                result = booking_svc.list_seats_for_session(session_id)
            except ValueError as e:
                return jsonify({'error': str(e)}), 404
            return jsonify(result), 200
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
            try:
                booking, total = facade.purchase_booking(session_id=session_id, user_id=user_id, seat_ids=seat_ids, card=card)
            except ValueError as e:
                session.rollback()
                return jsonify({'error': str(e)}), 400

            # return updated matrix
            booking_svc = factory.booking()
            matrix = booking_svc.seat_matrix_for_session(session_id)
            return jsonify({'matrix': matrix, 'booking_id': booking.id, 'amount': total}), 201
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
            factory = ServiceFactory(session)
            booking_svc = factory.booking()
            try:
                uid = int(user_id) if user_id is not None else None
            except ValueError:
                return jsonify({'error': 'invalid user_id'}), 400
            books = booking_svc.list_bookings(user_id=uid)
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
            factory = ServiceFactory(session)
            booking_svc = factory.booking()
            b = booking_svc.get_booking(booking_id)
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
            factory = ServiceFactory(session)
            booking_svc = factory.booking()
            out = booking_svc.booked_seats_for_session(session_id)
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
            booking_svc = factory.booking()
            booking = booking_svc.get_booking_for_seat(session_id=session_id, seat_id=seat_id)
            if not booking:
                return jsonify({'error': 'booking not found for seat'}), 404

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
