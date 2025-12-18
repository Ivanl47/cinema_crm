from flask import Blueprint, jsonify, request
from services.factory import ServiceFactory
from services.facade import AppFacade


def create_films_blueprint(session_factory):
    bp = Blueprint('films', __name__, url_prefix='/films')

    @bp.route('', methods=['GET'])
    def list_films():
        session = session_factory()
        try:
            facade = AppFacade(ServiceFactory(session))
            films = facade.list_films()
            return jsonify([
                {"id": f.id, "title": f.title, "description": f.description, "duration": f.duration}
                for f in films
            ])
        finally:
            session.close()

    from flask import current_app

    @bp.route('', methods=['POST'])
    def create_film():
        data = request.get_json() or {}
        title = data.get('title')
        if not title:
            return jsonify({'error': 'title required'}), 400
        session = session_factory()
        try:
            facade = AppFacade(ServiceFactory(session))
            film = facade.create_film(title=title, description=data.get('description'), duration=data.get('duration'))
            return jsonify({'id': film.id, 'title': film.title, 'description': film.description, 'duration': film.duration}), 201
        except Exception as e:
            # Log full traceback and return error details (development help)
            current_app.logger.exception('create_film failed')
            # Return minimal error info to client for debugging (remove in production)
            return jsonify({'error': 'internal error', 'details': str(e)}), 500
        finally:
            session.close()

    return bp
