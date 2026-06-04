import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

host_name = os.getenv("POSTGRES_HOST")
database_name = os.getenv("POSTGRES_DB")
user_name = os.getenv("POSTGRES_USER")
user_password = os.getenv("POSTGRES_PASSWORD")


def get_connection():
    return psycopg2.connect(
        host=host_name,
        dbname=database_name,
        user=user_name,
        password=user_password
    )


def create_tables():
    conn = get_connection()
    cur = conn.cursor()

    # -------------------------
    # TRANSACTIONS TABLE
    # -------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id UUID PRIMARY KEY,
        date TEXT,
        time TEXT,
        location TEXT,
        amount_paid NUMERIC,
        payment_method TEXT,
        card_number TEXT
    );
    """)

    # -------------------------
    # ITEMS TABLE
    # -------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        item_id UUID PRIMARY KEY,
        transaction_id UUID REFERENCES transactions(id),
        item_name TEXT,
        price NUMERIC
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

    print("Tables created successfully!")


if __name__ == "__main__":
    create_tables()