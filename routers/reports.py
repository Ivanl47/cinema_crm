from flask import Blueprint, jsonify, request, make_response
from services.factory import ServiceFactory
from datetime import datetime, timedelta
import io, csv


def create_reports_blueprint(session_factory):
    bp = Blueprint('reports', __name__, url_prefix='/reports')

    def _require_admin(session, acting_user_id):
        factory = ServiceFactory(session)
        user_svc = factory.user()
        try:
            return user_svc.is_admin(int(acting_user_id))
        except Exception:
            return False

    @bp.route('/sold_tickets', methods=['GET'])
    def sold_tickets():
        """Return sold tickets in CSV for a given booking date range.

        Query params: `acting_user_id`, `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD)
        """
        acting_user_id = request.args.get('acting_user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if not (acting_user_id and start_date and end_date):
            return jsonify({'error': 'acting_user_id, start_date and end_date required'}), 400

        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1, seconds=-1)
        except Exception:
            return jsonify({'error': 'invalid date format, use YYYY-MM-DD'}), 400

        session = session_factory()
        try:
            if not _require_admin(session, acting_user_id):
                return jsonify({'error': 'forbidden: admin required'}), 403

            from models import booking_seats
            from models import Booking as BookingModel, Session as SessionModel, Film as FilmModel, Hall as HallModel, Seat as SeatModel
            from models.enums import BookingStatus
            from sqlalchemy import text

            sql = text(
                """
                SELECT b.id AS booking_id, b.booking_date, b.user_id, b.session_id AS session_id,
                       sess.date AS session_date, sess.time AS session_time, f.title AS film_title,
                       h.name AS hall_name, bs.seat_id AS seat_id, seat.`row` AS seat_row, seat.number AS seat_number, bs.price AS price
                FROM bookings b
                JOIN booking_seats bs ON bs.booking_id = b.id
                JOIN sessions sess ON b.session_id = sess.id
                JOIN films f ON sess.film_id = f.id
                JOIN halls h ON sess.hall_id = h.id
                JOIN seats seat ON bs.seat_id = seat.id
                WHERE b.status = :confirmed AND b.booking_date BETWEEN :start AND :end
                ORDER BY b.booking_date ASC
                """
            )

            rows = session.execute(sql, {'confirmed': BookingStatus.CONFIRMED.value, 'start': start_dt, 'end': end_dt}).fetchall()

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['booking_id', 'booking_date', 'user_id', 'session_id', 'session_date', 'session_time', 'film_title', 'hall_name', 'seat_id', 'seat_row', 'seat_number', 'price'])
            for r in rows:
                writer.writerow([r.booking_id, r.booking_date, r.user_id, r.session_id, r.session_date, r.session_time, r.film_title, r.hall_name, r.seat_id, r.seat_row, r.seat_number, float(r.price) if r.price is not None else None])

            resp = make_response(output.getvalue())
            resp.headers['Content-Type'] = 'text/csv'
            resp.headers['Content-Disposition'] = f'attachment; filename="sold_tickets_{start_date}_to_{end_date}.csv"'
            return resp
        finally:
            session.close()

    @bp.route('/revenue_per_session', methods=['GET'])
    def revenue_per_session():
        """Return revenue grouped by session (CSV).

        Query params: `acting_user_id`, `start_date`, `end_date` (YYYY-MM-DD)
        """
        acting_user_id = request.args.get('acting_user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if not (acting_user_id and start_date and end_date):
            return jsonify({'error': 'acting_user_id, start_date and end_date required'}), 400

        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1, seconds=-1)
        except Exception:
            return jsonify({'error': 'invalid date format, use YYYY-MM-DD'}), 400

        session = session_factory()
        try:
            if not _require_admin(session, acting_user_id):
                return jsonify({'error': 'forbidden: admin required'}), 403

            from sqlalchemy import text
            from models.enums import BookingStatus

            sql = text(
                """
                SELECT sess.id AS session_id, f.title AS film_title, sess.date AS session_date, sess.time AS session_time, h.name AS hall_name,
                       COUNT(bs.seat_id) AS tickets_sold, SUM(bs.price) AS revenue
                FROM bookings b
                JOIN booking_seats bs ON bs.booking_id = b.id
                JOIN sessions sess ON b.session_id = sess.id
                JOIN films f ON sess.film_id = f.id
                JOIN halls h ON sess.hall_id = h.id
                WHERE b.status = :confirmed AND b.booking_date BETWEEN :start AND :end
                GROUP BY sess.id, f.title, sess.date, sess.time, h.name
                ORDER BY sess.date, sess.time
                """
            )

            rows = session.execute(sql, {'confirmed': BookingStatus.CONFIRMED.value, 'start': start_dt, 'end': end_dt}).fetchall()

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['session_id', 'film_title', 'session_date', 'session_time', 'hall_name', 'tickets_sold', 'revenue'])
            for r in rows:
                writer.writerow([r.session_id, r.film_title, r.session_date, r.session_time, r.hall_name, int(r.tickets_sold) if r.tickets_sold is not None else 0, float(r.revenue) if r.revenue is not None else 0.0])

            resp = make_response(output.getvalue())
            resp.headers['Content-Type'] = 'text/csv'
            resp.headers['Content-Disposition'] = f'attachment; filename="revenue_per_session_{start_date}_to_{end_date}.csv"'
            return resp
        finally:
            session.close()

    @bp.route('/occupancy_by_day', methods=['GET'])
    def occupancy_by_day():
        """Return hall occupancy per day (CSV).

        Query params: `acting_user_id`, `start_date`, `end_date` (YYYY-MM-DD)
        """
        acting_user_id = request.args.get('acting_user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if not (acting_user_id and start_date and end_date):
            return jsonify({'error': 'acting_user_id, start_date and end_date required'}), 400

        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        except Exception:
            return jsonify({'error': 'invalid date format, use YYYY-MM-DD'}), 400

        session = session_factory()
        try:
            if not _require_admin(session, acting_user_id):
                return jsonify({'error': 'forbidden: admin required'}), 403

            from sqlalchemy import text

            sql = text(
                """
                SELECT sess.date AS day, h.id AS hall_id, h.name AS hall_name,
                       COUNT(DISTINCT seat.id) AS seats, COUNT(DISTINCT sess.id) AS sessions_count, COUNT(bs.seat_id) AS booked_seats
                FROM sessions sess
                JOIN halls h ON sess.hall_id = h.id
                JOIN seats seat ON seat.hall_id = h.id
                LEFT JOIN bookings b ON b.session_id = sess.id AND b.status = :confirmed
                LEFT JOIN booking_seats bs ON bs.booking_id = b.id
                WHERE sess.date BETWEEN :start AND :end
                GROUP BY sess.date, h.id, h.name
                ORDER BY sess.date, h.name
                """
            )

            from models.enums import BookingStatus
            rows = session.execute(sql, {'confirmed': BookingStatus.CONFIRMED.value, 'start': start_dt, 'end': end_dt}).fetchall()

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['day', 'hall_id', 'hall_name', 'seats_per_hall', 'sessions_count', 'booked_seats', 'occupancy_percent'])
            for r in rows:
                seats = int(r.seats) if r.seats is not None else 0
                sessions_count = int(r.sessions_count) if r.sessions_count is not None else 0
                booked = int(r.booked_seats) if r.booked_seats is not None else 0
                total_possible = seats * sessions_count if seats and sessions_count else 0
                occupancy = round((booked / total_possible) * 100.0, 2) if total_possible else 0.0
                writer.writerow([r.day, r.hall_id, r.hall_name, seats, sessions_count, booked, occupancy])

            resp = make_response(output.getvalue())
            resp.headers['Content-Type'] = 'text/csv'
            resp.headers['Content-Disposition'] = f'attachment; filename="occupancy_{start_date}_to_{end_date}.csv"'
            return resp
        finally:
            session.close()

    return bp
