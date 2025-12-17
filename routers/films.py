from flask import Blueprint, jsonify, request

def create_films_blueprint(session_factory):
    bp = Blueprint('films', __name__, url_prefix='/films')

    @bp.route('', methods=['GET'])
    def list_films():
        session = session_factory()
        try:
            films = session.query('Film').all() if False else session.query.__self__
        finally:
            session.close()
        # NOTE: real implementation is registered in app by passing models; stub kept minimal
        return jsonify([])

    @bp.route('', methods=['POST'])
    def create_film():
        data = request.get_json() or {}
        title = data.get('title')
        if not title:
            return jsonify({'error': 'title required'}), 400
        session = session_factory()
        try:
            # create and commit directly here for simplicity
            from models import Film
            film = Film(title=title, description=data.get('description'), duration=data.get('duration'))
            session.add(film)
            session.commit()
            session.refresh(film)
            return jsonify({'id': film.id, 'title': film.title}), 201
        finally:
            session.close()

    return bp
