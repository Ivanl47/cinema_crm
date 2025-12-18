from flask import Blueprint, jsonify, request
from cinema_crm.services.factory import ServiceFactory
from cinema_crm.services.facade import AppFacade


def create_films_blueprint(session_factory):
    bp = Blueprint('films', __name__, url_prefix='/films')

    @bp.route('', methods=['GET'])
    def list_films():
        session = session_factory()
        try:
            facade = AppFacade(ServiceFactory(session))
            films = facade.list_films()
            return jsonify([{"id": f.id, "title": f.title} for f in films])
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
            facade = AppFacade(ServiceFactory(session))
            film = facade.create_film(title=title, description=data.get('description'), duration=data.get('duration'))
            return jsonify({'id': film.id, 'title': film.title}), 201
        finally:
            session.close()

    return bp
