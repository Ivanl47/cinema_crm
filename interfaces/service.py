from abc import ABC


class ServiceInterface(ABC):
    """Marker interface for services to allow type hints and DI.

    Keep minimal to avoid enforcing constructor signatures across implementations.
    """
    pass
