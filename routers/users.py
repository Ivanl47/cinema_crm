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

    @bp.route('/admin/login', methods=['POST'])
    def admin_login():
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
        if not (username and password):
            return jsonify({'error': 'username and password required'}), 400

        session = session_factory()
        try:
            factory = ServiceFactory(session)
            user_svc = factory.user()
            # try find user
            user = user_svc.find_by_username(username)
            # if user exists, verify password and role
            if user:
                if not user_svc.verify_password(user, password):
                    return jsonify({'error': 'invalid credentials'}), 401
                from models.enums import UserRole
                is_admin = getattr(user, 'role', None) == UserRole.ADMIN
                if not is_admin:
                    return jsonify({'error': 'admin role required'}), 403
                return jsonify({'user_id': user.id, 'is_admin': True}), 200

            # If no user found, allow bootstrap admin creation for common defaults
            if (username == 'admin' and password == 'root') or (username == 'root' and password == 'root'):
                # create admin user
                facade = AppFacade(factory)
                user = facade.create_user(username=username, email=f'{username}@local', password=password, role='ADMIN')
                return jsonify({'user_id': user.id, 'is_admin': True}), 201

            return jsonify({'error': 'invalid credentials'}), 401
        finally:
            session.close()
    
    @bp.route('/auth', methods=['POST'])
    def auth_or_create():
        """Authenticate a user or create if missing.

        Body: { username, password, email? }
        If user exists, verify password and return user_id and is_admin flag.
        If user does not exist, create and return created user info.
        """
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        if not (username and password):
            return jsonify({'error': 'username and password required'}), 400

        session = session_factory()
        try:
            factory = ServiceFactory(session)
            user_svc = factory.user()
            user = user_svc.find_by_username(username)
            if user:
                # verify
                if not user_svc.verify_password(user, password):
                    return jsonify({'error': 'invalid credentials'}), 401
                from models.enums import UserRole
                is_admin = getattr(user, 'role', None) == UserRole.ADMIN
                return jsonify({'user_id': user.id, 'username': user.username, 'is_admin': bool(is_admin)}), 200

            # create user
            facade = AppFacade(factory)
            created = facade.create_user(username=username, email=email or f'{username}@local', password=password)
            return jsonify({'user_id': created.id, 'username': created.username, 'is_admin': False}), 201
        finally:
            session.close()

    @bp.route('/<int:user_id>/promote', methods=['POST'])
    def promote_user(user_id: int):
        """Promote an existing user to admin role. Requires acting_user_id (admin)."""
        data = request.get_json() or {}
        acting_user_id = data.get('acting_user_id')
        if not acting_user_id:
            return jsonify({'error': 'acting_user_id required'}), 400

        session = session_factory()
        try:
            factory = ServiceFactory(session)
            user_svc = factory.user()
            # ensure acting user is admin
            try:
                if not user_svc.is_admin(int(acting_user_id)):
                    return jsonify({'error': 'forbidden: admin required'}), 403
            except Exception:
                return jsonify({'error': 'invalid acting_user_id'}), 400

            # find target user
            target = user_svc.find_by_username(None) if False else user_svc.get_user(user_id)
            if not target:
                return jsonify({'error': 'user not found'}), 404

            from models.enums import UserRole
            # update role to ADMIN
            user_svc.dao.update(target, role=UserRole.ADMIN)
            return jsonify({'id': target.id, 'username': target.username, 'role': 'ADMIN'}), 200
        finally:
            session.close()

    @bp.route('/admins', methods=['GET'])
    def list_admins():
        """Return all admin users except the special 'root' account."""
        session = session_factory()
        try:
            from models import User as UserModel
            from models.enums import UserRole
            admins = session.query(UserModel).filter(UserModel.role == UserRole.ADMIN).all()
            out = []
            for u in admins:
                # exclude literal 'root' username from the list
                if getattr(u, 'username', '').lower() == 'root':
                    continue
                out.append({'id': u.id, 'username': u.username, 'email': u.email})
            return jsonify({'admins': out}), 200
        finally:
            session.close()

    @bp.route('/<int:user_id>/demote', methods=['POST'])
    def demote_user(user_id: int):
        """Demote an admin to regular user. Requires acting_user_id (admin). Cannot demote 'root'."""
        data = request.get_json() or {}
        acting_user_id = data.get('acting_user_id')
        if not acting_user_id:
            return jsonify({'error': 'acting_user_id required'}), 400

        session = session_factory()
        try:
            factory = ServiceFactory(session)
            user_svc = factory.user()
            # ensure acting user is admin
            try:
                if not user_svc.is_admin(int(acting_user_id)):
                    return jsonify({'error': 'forbidden: admin required'}), 403
            except Exception:
                return jsonify({'error': 'invalid acting_user_id'}), 400

            target = user_svc.get_user(user_id)
            if not target:
                return jsonify({'error': 'user not found'}), 404
            if getattr(target, 'username', '').lower() == 'root':
                return jsonify({'error': 'cannot demote root user'}), 403

            from models.enums import UserRole
            user_svc.dao.update(target, role=UserRole.USER)
            return jsonify({'id': target.id, 'username': target.username, 'role': 'USER'}), 200
        finally:
            session.close()
    
    return bp
