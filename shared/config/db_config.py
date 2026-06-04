import psycopg2

DB_CONFIG = {
    "dbname": "spam",
    "user": "postgres",
    "password": "your_password",
    "host": "localhost",
    "port": 5432
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)