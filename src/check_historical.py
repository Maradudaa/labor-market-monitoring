import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "raw" / "hh ru DATASET.csv"

df = pd.read_csv(CSV_PATH)

print("Количество строк:", len(df))
print("Количество столбцов:", len(df.columns))

print("\nНазвания столбцов:")
for column in df.columns:
    print(column)

print("\nПервые 5 строк:")
print(df.head())