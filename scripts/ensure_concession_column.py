import pymysql
from config import config
import os

cfg = config[os.environ.get('FLASK_ENV', 'development')]

def ensure_column():
    host = cfg.DB_HOST
    port = int(cfg.DB_PORT)
    user = cfg.DB_USER
    password = cfg.DB_PASSWORD
    dbname = cfg.DB_NAME

    conn = pymysql.connect(host=host, port=port, user=user, password=password, db=dbname, charset='utf8mb4')
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW COLUMNS FROM users LIKE 'concession'")
            if cur.fetchone() is None:
                print('Adding concession column to users...')
                cur.execute("ALTER TABLE users ADD COLUMN concession VARCHAR(50) DEFAULT 'NONE'")
                conn.commit()
                print('Added concession column.')
            else:
                print('concession column already exists.')
    finally:
        conn.close()

if __name__ == '__main__':
    ensure_column()
