from interfaces.service import ServiceInterface


class BaseService(ServiceInterface):
    """Common base for services.

    Services receive a SQLAlchemy `session` (not a session factory) and create DAO
    instances as needed. This keeps services thin and focused on business logic.
    """

    def __init__(self, session):
        self.session = session
