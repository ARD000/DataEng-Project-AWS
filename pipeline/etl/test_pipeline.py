import os
from dotenv import load_dotenv
from extract import extract_csv
from load import load_to_postgres

# Load .env safely
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, "../../.env")
load_dotenv(dotenv_path)

# Safe file path
file_path = os.path.join(BASE_DIR, "../../data/sample.csv")

table_name = "your_table_name"

# Extract
df = extract_csv(file_path)

print(f"Extracted {len(df)} rows")

# Load
result = load_to_postgres(df, table_name)

print(result)