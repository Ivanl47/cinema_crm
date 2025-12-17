class Config:
    SECRET_KEY = "dev"
    SQLALCHEMY_ECHO = False


class TestConfig(Config):
    # SQLite file used for local testing; change to your DB URI as needed
    SQLALCHEMY_DATABASE_URI = "sqlite:///cinema_test.db"
    SQLALCHEMY_ECHO = False
