import json
import psycopg2
import os


# -----------------------------
# LOAD JSON FILE
# -----------------------------
JSON_PATH = "pipeline/ingestion/sources/leeds_order.json"

# -----------------------------
# DB CONNECTION (EDIT IF NEEDED)
# -----------------------------
conn = psycopg2.connect(
    host="localhost",
    database="your_database_name",
    user="postgres",
    password="your_password",
    port=5432
)

cur = conn.cursor()

# -----------------------------
# READ JSON
# -----------------------------
with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

transactions = data["transactions"]
items = data["items"]

# -----------------------------
# INSERT TRANSACTIONS
# -----------------------------
for t in transactions:
    cur.execute("""
        INSERT INTO transactions (
            id, date, time, location,
            amount_paid, payment_method, card_number
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        t["id"],
        t["date"],
        t["time"],
        t["location"],
        float(t["amount_paid"]),
        t["payment_method"],
        t["card_number"]
    ))

# -----------------------------
# INSERT ITEMS
# -----------------------------
for i in items:
    cur.execute("""
        INSERT INTO items (
            item_id, transaction_id, item_name, price
        )
        VALUES (%s, %s, %s, %s)
    """, (
        i["item_id"],
        i["transaction_id"],
        i["item_name"],
        float(i["price"])
    ))

# -----------------------------
# COMMIT + CLOSE
# -----------------------------
conn.commit()
cur.close()
conn.close()

print("DONE: Data loaded into PostgreSQL")



def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )


def load_to_postgres(df, table_name):
    conn = get_connection()
    cur = conn.cursor()

    # Build insert query dynamically
    cols = ",".join(df.columns)
    placeholders = ",".join(["%s"] * len(df.columns))

    query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"

    for row in df.itertuples(index=False, name=None):
        cur.execute(query, row)

    conn.commit()
    cur.close()
    conn.close()

    return f"Loaded {len(df)} rows into {table_name}"