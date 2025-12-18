from flask import Blueprint, jsonify, request
from services.factory import ServiceFactory
from services.facade import AppFacade


def create_users_blueprint(session_factory):
    bp = Blueprint('users', __name__, url_prefix='/users')

    @bp.route('', methods=['GET', 'POST'])
    def users_root():
        """Handle listing users (GET) and creating users (POST) on the same rule.

        Using one view for both methods avoids duplicate rule registration which
        can cause method-not-allowed behaviour in some setups.
        """
        if request.method == 'POST':
            data = request.get_json() or {}
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            if not (username and email and password):
                return jsonify({'error': 'username, email and password required'}), 400
            session = session_factory()
            try:
                facade = AppFacade(ServiceFactory(session))
                user = facade.create_user(username=username, email=email, password=password)
                return jsonify({'id': user.id, 'username': user.username}), 201
            finally:
                session.close()

        # GET
        username = request.args.get('username')
        session = session_factory()
        try:
            factory = ServiceFactory(session)
            user_svc = factory.user()
            if username:
                user = user_svc.find_by_username(username)
                if not user:
                    return jsonify({'error': 'user not found'}), 404
                return jsonify({'user': {'id': user.id, 'username': user.username, 'email': user.email}}), 200
            # list via DAO for full list
            users = user_svc.dao.list()
            out = [{'id': u.id, 'username': u.username, 'email': u.email} for u in users]
            return jsonify({'users': out}), 200
        finally:
            session.close()

    @bp.route('/<int:user_id>', methods=['GET'])
    def get_user(user_id: int):
        session = session_factory()
        try:
            factory = ServiceFactory(session)
            user_svc = factory.user()
            user = user_svc.get_user(user_id)
            if not user:
                return jsonify({'error': 'user not found'}), 404
            return jsonify({'id': user.id, 'username': user.username, 'email': user.email}), 200
        finally:
            session.close()

    return bp
