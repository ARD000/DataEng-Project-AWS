
import os
import csv
import json
import uuid

# -----------------------------
# BASE PATH (ETL folder)
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# CSV location:
# pipeline/ingestion/sources/leedsdata.csv
CSV_PATH = os.path.normpath(
    os.path.join(BASE_DIR, "..", "ingestion", "sources", "leedsdata.csv")
)

# Output location (same folder)
OUTPUT_PATH = os.path.normpath(
    os.path.join(BASE_DIR, "..", "ingestion", "sources", "leeds_order.json")
)

# -----------------------------
# DEBUG
# -----------------------------
print("CWD:", os.getcwd())
print("CSV PATH:", CSV_PATH)
print("CSV EXISTS:", os.path.exists(CSV_PATH))


# -----------------------------
# EXTRACT
# -----------------------------
def extract_csv(file_path):
    print(f"Loading CSV: {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV not found at: {file_path}")

    with open(file_path, mode="r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


# -----------------------------
# TRANSFORM
# -----------------------------
def transform_data(rows):
    transactions = []
    items = []

    for row in rows:
        transaction_id = str(uuid.uuid4())

        # -------------------------
        # TRANSACTIONS TABLE
        # -------------------------
        transactions.append({
            "id": transaction_id,
            "date": row["date"],
            "time": row[" time"].strip(),
            "location": row[" location"].strip(),
            "amount_paid": row[" amount_paid"],
            "payment_method": row[" payment_method"],
            "card_number": row[" card_number"]
        })

        # -------------------------
        # ITEMS TABLE
        # -------------------------
        raw_items = row.get(" items_total")

        if raw_items:
            item_list = raw_items.split(",")

            for item in item_list:
                item = item.strip()

                if " - " not in item:
                    continue

                name, price = item.rsplit(" - ", 1)

                items.append({
                    "item_id": str(uuid.uuid4()),
                    "transaction_id": transaction_id,
                    "item_name": name.strip(),
                    "price": float(price)
                })

    return transactions, items


# -----------------------------
# LOAD
# -----------------------------
def load_json(data, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# -----------------------------
# PIPELINE
# -----------------------------
def run_pipeline():
    rows = extract_csv(CSV_PATH)

    transactions, items = transform_data(rows)

    load_json(
        {
            "transactions": transactions,
            "items": items
        },
        OUTPUT_PATH
    )

    print("\n--- DONE ---")
    print("Transactions:", len(transactions))
    print("Items:", len(items))

    return transactions, items


run_pipeline()