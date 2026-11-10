import sqlite3

from db import DB_PATH


connection = sqlite3.connect(DB_PATH)

count = connection.execute(
    "SELECT COUNT(*) FROM api_vacancies"
).fetchone()[0]

print("Всего вакансий в api_vacancies:", count)
print()

rows = connection.execute("""
    SELECT
        vacancy_id,
        name,
        area_name,
        published_at,
        loaded_at
    FROM api_vacancies
    LIMIT 5
""").fetchall()

for row in rows:
    print(
        row[0],
        "|",
        row[1],
        "|",
        row[2],
        "|",
        row[3],
        "| загружено:",
        row[4]
    )

connection.close()