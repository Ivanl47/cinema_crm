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

    return bp
