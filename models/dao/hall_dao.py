from .base_dao import BaseDAO
from models import Hall


class HallDAO(BaseDAO):
    model = Hall
