import os
import pymysql
from flask import Flask, send_from_directory
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

from config import config
from models import db
from routers import (
    create_films_blueprint,
    create_users_blueprint,
    create_bookings_blueprint,
)


def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Ensure the physical database exists (create if missing) before initializing SQLAlchemy
    def ensure_database_exists(app):
        cfg = app.config
        db_name = cfg.get('DB_NAME')
        host = cfg.get('DB_HOST', 'localhost')
        port = int(cfg.get('DB_PORT', 3306))
        user = cfg.get('DB_USER', '')
        password = cfg.get('DB_PASSWORD', '')

        # Use PyMySQL to connect to the server (without selecting a database)
        try:
            conn = pymysql.connect(host=host, port=port, user=user, password=password, charset='utf8mb4')
            with conn.cursor() as cur:
                cur.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.commit()
            conn.close()
        except Exception:
            # Re-raise so startup fails loudly if DB server is unreachable or credentials are wrong
            raise

    ensure_database_exists(app)

    # Initialize extensions
    db.init_app(app)
    
    # Create a plain SQLAlchemy engine + SessionLocal for existing router factories
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], echo=app.config.get('SQLALCHEMY_ECHO', False), future=True)
    SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

    # Optional: run precondition loader if explicitly enabled via env var
    if os.environ.get('PRECONDITION_AUTOLOAD', '').lower() in ('1', 'true', 'yes'):
        try:
            from precondition.load_sample import load_sample
            with app.app_context():
                print('Running precondition autoload...')
                load_sample()
        except Exception as e:
            # don't fail app startup for precondition; surface a warning
            print('Precondition autoload failed:', e)

    # Register routes (pass SessionLocal as before)
    app.register_blueprint(create_films_blueprint(SessionLocal))
    app.register_blueprint(create_users_blueprint(SessionLocal))
    app.register_blueprint(create_bookings_blueprint(SessionLocal))
    
    # Serve single-page UI and its assets from static/ui
    @app.route('/')
    def index():
        return send_from_directory('static/ui', 'index.html')

    @app.route('/ui/<path:filename>')
    def ui_assets(filename):
        return send_from_directory('static/ui', filename)
    
    # Create tables
    with app.app_context():
        db.create_all()
        # Ensure `concession` column exists on `users` table (safe, idempotent)
        try:
            with engine.connect() as conn:
                try:
                    has_col = conn.execute(text("SHOW COLUMNS FROM users LIKE 'concession'"))
                    if has_col.fetchone() is None:
                        conn.execute(text("ALTER TABLE users ADD COLUMN concession VARCHAR(50) DEFAULT 'NONE'"))
                except Exception:
                    # fallback: try generic ALTER for SQLite or other DBs
                    try:
                        conn.execute(text("ALTER TABLE users ADD COLUMN concession VARCHAR(50)"))
                        conn.execute(text("UPDATE users SET concession = 'NONE' WHERE concession IS NULL"))
                    except Exception:
                        app.logger.exception('could not ensure users.concession column')
        except Exception:
            app.logger.exception('failed to run concession column migration')
        # Autoload sample data in development when DB appears empty
        try:
            if app.config.get('DEBUG', False):
                from precondition.load_sample import load_sample
                load_sample()
        except Exception as e:
            app.logger.exception('precondition autoload failed')
        # Ensure a base admin user exists (username: root, password: root)
        try:
            # Use the SessionLocal created above to perform a simple check/create
            sess = SessionLocal()
            from services.factory import ServiceFactory
            from services.facade import AppFacade
            factory = ServiceFactory(sess)
            user_svc = factory.user()
            existing = user_svc.find_by_username('root')
            if not existing:
                facade = AppFacade(factory)
                facade.create_user(username='root', email='root@local', password='root', role='ADMIN')
            sess.close()
        except Exception:
            app.logger.exception('failed to ensure root admin')
    
    return app


if __name__ == '__main__':
    # Note: Change host to '127.0.0.1' in production and disable debug mode
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
