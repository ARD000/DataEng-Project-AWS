import os
from extract import extract_csv

BASE_DIR = os.path.dirname(__file__)
file_path = os.path.join(BASE_DIR, "leedsdata.csv")

df = extract_csv(file_path)

print(df.head())
print("Rows:", len(df))