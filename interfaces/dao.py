from abc import ABC, abstractmethod
from typing import List, Optional


class DAOInterface(ABC):
    """Minimal DAO interface for type hints and DI.

    Concrete DAOs should implement these methods. Keeping the surface
    small avoids breaking existing implementations.
    """

    @abstractmethod
    def get(self, id: int):
        raise NotImplementedError()

    @abstractmethod
    def list(self, offset: int = 0, limit: int = 100) -> List:
        raise NotImplementedError()

    @abstractmethod
    def create(self, commit: bool = True, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def update(self, obj, commit: bool = True, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def delete(self, obj, commit: bool = True):
        raise NotImplementedError()
