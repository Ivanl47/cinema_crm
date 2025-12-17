import enum


class UserRole(enum.Enum):
    GUEST = "GUEST"
    USER = "USER"
    ADMIN = "ADMIN"


class BookingStatus(enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class PaymentStatus(enum.Enum):
    INIT = "INIT"
    PAID = "PAID"
    FAILED = "FAILED"


class SeatCategory(enum.Enum):
    STANDARD = "STANDARD"
    VIP = "VIP"
    BALCONY = "BALCONY"
