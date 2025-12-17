from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from models import Base, Film

app = Flask(__name__)
app.config.from_object('config.TestConfig')

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], echo=app.config.get('SQLALCHEMY_ECHO', False), future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))


def init_db():
    Base.metadata.create_all(bind=engine)


@app.route('/init-db', methods=['POST', 'GET'])
def init_db_route():
    init_db()
    return jsonify({'status': 'ok', 'msg': 'database initialized'})


@app.route('/films', methods=['GET'])
def list_films():
    session = SessionLocal()
    try:
        films = session.query(Film).all()
        result = [
            {'id': f.id, 'title': f.title, 'description': f.description, 'duration': f.duration}
            for f in films
        ]
        return jsonify(result)
    finally:
        session.close()


@app.route('/films', methods=['POST'])
def create_film():
    data = request.get_json() or {}
    title = data.get('title')
    if not title:
        return jsonify({'error': 'title required'}), 400
    session = SessionLocal()
    try:
        film = Film(title=title, description=data.get('description'), duration=data.get('duration'))
        session.add(film)
        session.commit()
        session.refresh(film)
        return jsonify({'id': film.id, 'title': film.title}), 201
    finally:
        session.close()


@app.route('/')
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
