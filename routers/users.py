from flask import Blueprint, jsonify, request
from cinema_crm.services.factory import ServiceFactory
from cinema_crm.services.facade import AppFacade


def create_users_blueprint(session_factory):
    bp = Blueprint('users', __name__, url_prefix='/users')

    @bp.route('', methods=['POST'])
    def create_user():
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

    return bp
