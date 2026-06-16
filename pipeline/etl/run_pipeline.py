import sys
import os

# make sure imports work regardless of where this is run from
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from warehouse.schema.postgrestable import create_tables
from pipeline.etl.transform import CSV_PATH, extract_csv, transform_data, load_json, OUTPUT_PATH
from pipeline.etl.load import load_to_database


def run():
    print("=== TeamSPAM ETL Pipeline ===\n")

    # step 1 - make sure the tables exist in the database
    # this also seeds the sizes and flavours lookup tables
    print("Step 1: Creating tables...")
    create_tables()

    # step 2 - read the raw CSV from the branch sources folder
    print("\nStep 2: Extracting CSV...")
    rows = extract_csv(CSV_PATH)
    print(f"Extracted {len(rows)} rows")

    # step 3 - clean and reshape the data to match our schema
    print("\nStep 3: Transforming data...")
    orders, order_items = transform_data(rows)
    print(f"Transformed into {len(orders)} orders and {len(order_items)} order items")

    # step 4 - save a copy as JSON (useful for debugging)
    print("\nStep 4: Saving JSON snapshot...")
    load_json({"orders": orders, "order_items": order_items}, OUTPUT_PATH)

    # step 5 - load into postgres
    print("\nStep 5: Loading into database...")
    load_to_database(orders, order_items)

    print("\n=== Pipeline complete ===")


if __name__ == "__main__":
    run()
