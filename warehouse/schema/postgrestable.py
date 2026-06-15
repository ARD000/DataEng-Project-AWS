import os
import psycopg2
import uuid
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
    # SIZES TABLE
    # -------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sizes (
        id      UUID            NOT NULL,
        name    VARCHAR(20)     NOT NULL,
        PRIMARY KEY (id)
    );
    """)

    # -------------------------
    # FLAVOURS TABLE
    # -------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS flavours (
        id      UUID            NOT NULL,
        name    VARCHAR(50)     NOT NULL,
        PRIMARY KEY (id)
    );
    """)

    # -------------------------
    # ORDERS TABLE
    # -------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id              UUID            NOT NULL,
        branch_name     VARCHAR(100)    NOT NULL,
        customer_name   VARCHAR(100)    NOT NULL,
        order_time      TIMESTAMP       NOT NULL,
        payment_method  VARCHAR(10)     NOT NULL,
        total_amount    DECIMAL(10,2)   NOT NULL,
        PRIMARY KEY (id)
    );
    """)

    # -------------------------
    # ORDER ITEMS TABLE
    # -------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id          UUID            NOT NULL,
        order_id    UUID            NOT NULL,
        item_name   VARCHAR(200)    NOT NULL,
        size_id     UUID,
        flavour_id  UUID,
        price       DECIMAL(10,2)   NOT NULL,
        quantity    SMALLINT        NOT NULL DEFAULT 1,
        PRIMARY KEY (id)
    );
    """)

    conn.commit()
    print("Tables created successfully!")

    seed_lookup_tables(cur, conn)

    cur.close()
    conn.close()


def seed_lookup_tables(cur, conn):
    # -------------------------
    # SEED SIZES
    # -------------------------
    sizes = ["Large", "Regular"]

    for name in sizes:
        cur.execute("""
            INSERT INTO sizes (id, name)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (str(uuid.uuid4()), name))

    # -------------------------
    # SEED FLAVOURS
    # -------------------------
    flavours = [
        "Hazelnut",
        "Caramel",
        "Vanilla",
        "Gingerbread",
        "Peppermint",
        "Cinnamon",
    ]

    for name in flavours:
        cur.execute("""
            INSERT INTO flavours (id, name)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (str(uuid.uuid4()), name))

    conn.commit()
    print("Lookup tables seeded successfully!")


if __name__ == "__main__":
    create_tables()
