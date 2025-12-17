from typing import Type, List, Optional
from sqlalchemy.orm import Session


class BaseDAO:
    """Very small generic DAO helper. Subclass and set `model` attribute."""

    model = None  # override in subclasses

    def __init__(self, session: Session):
        self.session = session

    def get(self, id: int):
        return self.session.get(self.model, id)

    def list(self, offset: int = 0, limit: int = 100) -> List:
        return self.session.query(self.model).offset(offset).limit(limit).all()

    def create(self, commit: bool = True, **kwargs):
        """Create and return a new model instance.

        By default this will commit the transaction to preserve backwards
        compatibility with existing callers. Call with `commit=False` to
        defer committing to the caller (preferred in services to control
        transactions).
        """
        obj = self.model(**kwargs)
        self.session.add(obj)
        if commit:
            self.session.commit()
            self.session.refresh(obj)
        else:
            # ensure PK populated without committing
            self.session.flush()
        return obj

    def update(self, obj, commit: bool = True, **kwargs):
        for k, v in kwargs.items():
            setattr(obj, k, v)
        if commit:
            self.session.commit()
            self.session.refresh(obj)
        else:
            self.session.flush()
        return obj

    def delete(self, obj, commit: bool = True):
        self.session.delete(obj)
        if commit:
            self.session.commit()
        else:
            self.session.flush()
