import os
import sqlite3

import pandas as pd
import requests
from dotenv import load_dotenv

from db import DB_PATH


load_dotenv()

token = os.getenv("HH_ACCESS_TOKEN")

headers = {
    "Authorization": f"Bearer {token}",
    "HH-User-Agent": "LaborMarketMonitoring/1.0 (maradudinaula@gmail.com)"
}


# Читаем две таблицы из нашей базы
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


def get_area_to_region_map():
    response = requests.get(
        "https://api.hh.ru/areas",
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    countries = response.json()

    area_to_region = {}

    # Находим Россию
    russia = next(
        country
        for country in countries
        if country["name"] == "Россия"
    )

    # Первый уровень внутри России — субъекты РФ
    for region in russia["areas"]:
        region_id = region["id"]
        region_name = region["name"]

        # Сам субъект тоже связываем с самим собой
        area_to_region[region_id] = region_name

        # Все города внутри субъекта
        for city in region["areas"]:
            area_to_region[city["id"]] = region_name

    return area_to_region


area_to_region = get_area_to_region_map()

api["region_name"] = api["area_id"].map(area_to_region)


print("Всего вакансий API:", len(api))

print(
    "Регион определён:",
    api["region_name"].notna().sum()
)

print(
    "Регион не определён:",
    api["region_name"].isna().sum()
)

print("\nПолученные субъекты РФ:")

for region in sorted(
    api["region_name"].dropna().unique()
):
    print("-", region)


historical_regions = set(
    historical["region_name"]
    .dropna()
    .unique()
)

api_filtered = api[
    api["region_name"].isin(historical_regions)
].copy()

print()
print("После фильтрации по регионам:")
print("Было вакансий API:", len(api))
print("Осталось вакансий:", len(api_filtered))

print("\nРегионы после фильтрации:")

for region in sorted(
    api_filtered["region_name"]
    .dropna()
    .unique()
):
    print("-", region)

historical_specializations = set(
    historical["specialization"]
    .dropna()
    .unique()
)


def map_specialization(row):
    role = row["professional_roles"]
    name = row["name"]

    # 1. Если роль из API точно совпадает
    # с одной из исторических специализаций
    if role in historical_specializations:
        return role, "exact"

    # 2. Если роль API неоднозначная,
    # пробуем уточнить её по названию вакансии
    if role == "Водитель, экспедитор":
        if "водитель" in name.lower():
            return "Водитель", "name_match"

    # 3. Если однозначно сопоставить не удалось
    return None, "unmapped"


# Применяем функцию ко всем вакансиям API
mapping_result = api_filtered.apply(
    map_specialization,
    axis=1
)


# Создаём нормализованную специализацию
api_filtered["specialization_norm"] = mapping_result.apply(
    lambda x: x[0]
)


# Создаём статус сопоставления
api_filtered["mapping_status"] = mapping_result.apply(
    lambda x: x[1]
)


print()
print("Результат сопоставления специализаций:")

print(
    api_filtered[
        [
            "name",
            "professional_roles",
            "specialization_norm",
            "mapping_status"
        ]
    ]
    .drop_duplicates()
    .to_string(index=False)
)


print()

mapped_count = (
    api_filtered["mapping_status"]
    .isin(["exact", "name_match"])
    .sum()
)

unmapped_count = (
    (api_filtered["mapping_status"] == "unmapped")
    .sum()
)

print(
    "Сопоставлено вакансий:",
    mapped_count
)

print(
    "Не сопоставлено вакансий:",
    unmapped_count
)


coverage = (
    api_filtered["mapping_status"]
    .isin(["exact", "name_match"])
    .mean()
    * 100
)

print(
    "Покрытие сопоставления:",
    round(coverage, 2),
    "%"
)


print()
print("Несопоставленные вакансии:")

print(
    api_filtered[
        api_filtered["mapping_status"] == "unmapped"
    ][
        [
            "name",
            "professional_roles",
            "area_name",
            "region_name"
        ]
    ]
    .to_string(index=False)
)

historical["vacancy_date"] = pd.to_datetime(
    historical["creation_date"],
    errors="coerce"
)

api_filtered["vacancy_date"] = pd.to_datetime(
    api_filtered["published_at"],
    errors="coerce",
    utc=True
).dt.tz_localize(None)


print()
print("Диапазон дат после преобразования:")

print(
    "Исторические данные:",
    historical["vacancy_date"].min(),
    "-",
    historical["vacancy_date"].max()
)

print(
    "API:",
    api_filtered["vacancy_date"].min(),
    "-",
    api_filtered["vacancy_date"].max()
)

historical["week_start"] = (
    historical["vacancy_date"]
    - pd.to_timedelta(
        historical["vacancy_date"].dt.weekday,
        unit="D"
    )
)

api_filtered["week_start"] = (
    api_filtered["vacancy_date"]
    - pd.to_timedelta(
        api_filtered["vacancy_date"].dt.weekday,
        unit="D"
    )
)

historical["week_start"] = historical["week_start"].dt.normalize()
api_filtered["week_start"] = api_filtered["week_start"].dt.normalize()


print()
print("Первые даты и соответствующие недели:")

print("\nИсторические данные:")
print(
    historical[
        ["vacancy_date", "week_start"]
    ].head()
)

print("\nAPI:")
print(
    api_filtered[
        ["vacancy_date", "week_start"]
    ].head()
)

historical_weekly = (
    historical
    .groupby("week_start")
    .size()
    .reset_index(name="vacancy_count")
)

historical_min_date = historical["vacancy_date"].min().normalize()
historical_max_date = historical["vacancy_date"].max().normalize()

historical_weekly["week_end"] = (
    historical_weekly["week_start"]
    + pd.Timedelta(days=6)
)

historical_weekly["is_full_week"] = (
    (historical_weekly["week_start"] >= historical_min_date)
    &
    (historical_weekly["week_end"] <= historical_max_date)
)

historical_weekly_full = historical_weekly[
    historical_weekly["is_full_week"]
].copy()


print()
print("До удаления неполных недель:", len(historical_weekly))
print(
    "Полных недель:",
    len(historical_weekly_full)
)

print("\nПервые полные недели:")
print(
    historical_weekly_full.head()
)

# Историческая недельная витрина:
# неделя + регион + специализация -> количество вакансий

historical_weekly_by_category = (
    historical[
        historical["week_start"].isin(
            historical_weekly_full["week_start"]
        )
    ]
    .groupby(
        [
            "week_start",
            "region_name",
            "specialization"
        ]
    )
    .size()
    .reset_index(name="vacancy_count")
)


from itertools import product


# ==========================================
# ИСТОРИЧЕСКАЯ НЕДЕЛЬНАЯ ВИТРИНА
# неделя + регион + специализация
# ==========================================

historical_weekly_by_category = (
    historical[
        historical["week_start"].isin(
            historical_weekly_full["week_start"]
        )
    ]
    .groupby(
        [
            "week_start",
            "region_name",
            "specialization"
        ]
    )
    .size()
    .reset_index(name="vacancy_count")
)


print()
print("Историческая недельная витрина:")
print(historical_weekly_by_category.head(10))

print()
print(
    "Количество строк до заполнения нулей:",
    len(historical_weekly_by_category)
)


# ==========================================
# СОЗДАЁМ ВСЕ ВОЗМОЖНЫЕ КОМБИНАЦИИ
# неделя × регион × специализация
# ==========================================

weeks = sorted(
    historical_weekly_full["week_start"].unique()
)

regions = sorted(
    historical["region_name"]
    .dropna()
    .unique()
)

specializations = sorted(
    historical["specialization"]
    .dropna()
    .unique()
)


full_index = pd.DataFrame(
    product(
        weeks,
        regions,
        specializations
    ),
    columns=[
        "week_start",
        "region_name",
        "specialization"
    ]
)


# ==========================================
# ДОБАВЛЯЕМ ФАКТИЧЕСКОЕ КОЛИЧЕСТВО ВАКАНСИЙ
# ==========================================

historical_weekly_complete = full_index.merge(
    historical_weekly_by_category,
    on=[
        "week_start",
        "region_name",
        "specialization"
    ],
    how="left"
)


# Если вакансий в конкретной комбинации не было,
# ставим 0
historical_weekly_complete["vacancy_count"] = (
    historical_weekly_complete["vacancy_count"]
    .fillna(0)
    .astype(int)
)


print()
print("После заполнения отсутствующих комбинаций:")

print(
    "Количество строк:",
    len(historical_weekly_complete)
)

print(
    "Количество нулевых значений:",
    (
        historical_weekly_complete["vacancy_count"]
        == 0
    ).sum()
)

print()
print("Первые строки полной исторической витрины:")

print(
    historical_weekly_complete.head(10)
)


# ==========================================
# НЕДЕЛЬНАЯ ВИТРИНА API
# ==========================================

# Оставляем только вакансии,
# которые удалось сопоставить
# с историческими специализациями
api_mapped = api_filtered[
    api_filtered["mapping_status"].isin(
        [
            "exact",
            "name_match"
        ]
    )
].copy()


api_weekly_by_category = (
    api_mapped
    .groupby(
        [
            "week_start",
            "region_name",
            "specialization_norm"
        ]
    )
    .size()
    .reset_index(name="vacancy_count")
)


# Приводим название столбца
# к такому же виду, как в исторической витрине
api_weekly_by_category = (
    api_weekly_by_category.rename(
        columns={
            "specialization_norm":
                "specialization"
        }
    )
)


print()
print("Недельная витрина API:")

print(
    api_weekly_by_category
)

print()

print(
    "Количество строк API:",
    len(api_weekly_by_category)
)