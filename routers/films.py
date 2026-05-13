from flask import Blueprint, jsonify, request, current_app
from services.factory import ServiceFactory


def create_films_blueprint(session_factory):
    bp = Blueprint('films', __name__, url_prefix='/films')

    @bp.route('', methods=['GET'])
    def list_films():
        session = session_factory()
        try:
            svc = ServiceFactory(session).film()
            films = svc.list_films()
            return jsonify([
                {"id": f.id, "title": f.title, "description": f.description, "duration": f.duration}
                for f in films
            ])
        finally:
            session.close()

    @bp.route('', methods=['POST'])
    def create_film():
        data = request.get_json() or {}
        title = data.get('title')
        if not title:
            return jsonify({'error': 'title required'}), 400
        session = session_factory()
        try:
            svc = ServiceFactory(session).film()
            film = svc.create(title=title, description=data.get('description'), duration=data.get('duration'))
            return jsonify({'id': film.id, 'title': film.title, 'description': film.description, 'duration': film.duration}), 201
        except Exception as e:
            current_app.logger.exception('create_film failed')
            return jsonify({'error': 'internal error', 'details': str(e)}), 500
        finally:
            session.close()

    @bp.route('/<int:film_id>', methods=['GET'])
    def get_film(film_id):
        session = session_factory()
        try:
            svc = ServiceFactory(session).film()
            f = svc.get(film_id)
            if not f:
                return jsonify({'error': 'not found'}), 404
            return jsonify({'id': f.id, 'title': f.title, 'description': f.description, 'duration': f.duration})
        finally:
            session.close()

    return bp
