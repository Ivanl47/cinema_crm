from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from models import Base, Film
from routers import (
    create_films_blueprint,
    create_users_blueprint,
    create_bookings_blueprint,
)

app = Flask(__name__)
app.config.from_object('config.TestConfig')

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], echo=app.config.get('SQLALCHEMY_ECHO', False), future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))


def init_db():
    Base.metadata.create_all(bind=engine)


# register blueprints (pass SessionLocal as session factory)
app.register_blueprint(create_films_blueprint(SessionLocal))
app.register_blueprint(create_users_blueprint(SessionLocal))
app.register_blueprint(create_bookings_blueprint(SessionLocal))


@app.route('/init-db', methods=['POST', 'GET'])
def init_db_route():
    init_db()
    return jsonify({'status': 'ok', 'msg': 'database initialized'})


# film routes moved to routers/films.py


@app.route('/')
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
