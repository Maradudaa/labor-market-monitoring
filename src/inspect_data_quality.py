import sqlite3
import pandas as pd

from db import DB_PATH


connection = sqlite3.connect(DB_PATH)

historical = pd.read_sql_query(
    "SELECT * FROM historical_vacancies",
    connection
)

api = pd.read_sql_query(
    "SELECT * FROM api_vacancies",
    connection
)

connection.close()


print("HISTORICAL_VACANCIES")
print("Количество строк:", len(historical))
print("Количество столбцов:", len(historical.columns))

print("\nПропуски:")
print(historical.isnull().sum())

print("\nДубли vacancy_id:")
print(historical["vacancy_id"].duplicated().sum())

historical_dates = pd.to_datetime(
    historical["creation_date"],
    errors="coerce"
)

print("\nДиапазон дат:")
print("От:", historical_dates.min())
print("До:", historical_dates.max())

print("\nКоличество регионов:")
print(historical["region_name"].nunique())

print("Количество специализаций:")
print(historical["specialization"].nunique())


print("\n\nAPI_VACANCIES")
print("Количество строк:", len(api))
print("Количество столбцов:", len(api.columns))

print("\nПропуски:")
print(api.isnull().sum())

print("\nДубли vacancy_id:")
print(api["vacancy_id"].duplicated().sum())

api_dates = pd.to_datetime(
    api["published_at"],
    errors="coerce"
)

print("\nДиапазон дат:")
print("От:", api_dates.min())
print("До:", api_dates.max())

print("\nКоличество регионов:")
print(api["area_name"].nunique())

print("Количество профессиональных ролей:")
print(api["professional_roles"].nunique())

print("\n\nЗНАЧЕНИЯ В ИСТОРИЧЕСКИХ ДАННЫХ")

print("\nРегионы:")
for value in sorted(historical["region_name"].dropna().unique()):
    print("-", value)

print("\nСпециализации:")
for value in sorted(historical["specialization"].dropna().unique()):
    print("-", value)

print("\nТипы занятости:")
for value in sorted(historical["employment"].dropna().unique()):
    print("-", value)

print("\nГрафики работы:")
for value in sorted(historical["work_schedule"].dropna().unique()):
    print("-", value)

print("\nОпыт работы:")
for value in sorted(historical["length_of_employment"].dropna().unique()):
    print("-", value)


print("\n\nЗНАЧЕНИЯ В API")

print("\nРегионы:")
for value in sorted(api["area_name"].dropna().unique()):
    print("-", value)

print("\nПрофессиональные роли:")
for value in sorted(api["professional_roles"].dropna().unique()):
    print("-", value)

print("\nФормы занятости:")
for value in sorted(api["employment_form"].dropna().unique()):
    print("-", value)

print("\nОпыт работы:")
for value in sorted(api["experience"].dropna().unique()):
    print("-", value)

print("\nФорматы работы:")
for value in sorted(api["work_format"].dropna().unique()):
    print("-", value)