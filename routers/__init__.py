"""Routers package — exposes blueprint factory functions.

This package contains factory functions that create Flask Blueprints
when passed a `session_factory` (typically `SessionLocal` from `app.py`).
Using factories avoids circular imports and keeps route creation explicit.
"""

from .films import create_films_blueprint
from .users import create_users_blueprint
from .bookings import create_bookings_blueprint
from .reports import create_reports_blueprint

__all__ = [
    "create_films_blueprint",
    "create_users_blueprint",
    "create_bookings_blueprint",
    "create_reports_blueprint",
]
