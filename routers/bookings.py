from flask import Blueprint, jsonify, request
from cinema_crm.services.factory import ServiceFactory
from cinema_crm.services.facade import BookingFacade


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
    return bp
