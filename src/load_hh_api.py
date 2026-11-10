import os
import csv
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

from db import DB_PATH, create_database


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_PATH = BASE_DIR / "logs" / "load_log.csv"

load_dotenv()

token = os.getenv("HH_ACCESS_TOKEN")

URL = "https://api.hh.ru/vacancies"

HEADERS = {
    "Authorization": f"Bearer {token}",
    "HH-User-Agent": "LaborMarketMonitoring/1.0 (maradudinaula@gmail.com)"
}


def list_to_text(items):
    if not items:
        return None

    return ", ".join(
        item["name"]
        for item in items
        if "name" in item
    )


def write_log(
    started_at,
    finished_at,
    status,
    rows_received,
    rows_inserted,
    error=""
):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    write_header = (
        not LOG_PATH.exists()
        or LOG_PATH.stat().st_size == 0
    )

    with open(
        LOG_PATH,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if write_header:
            writer.writerow([
                "source",
                "started_at",
                "finished_at",
                "status",
                "rows_received",
                "rows_inserted",
                "error"
            ])

        writer.writerow([
            "hh_api",
            started_at,
            finished_at,
            status,
            rows_received,
            rows_inserted,
            error
        ])


def get_date_from():
    connection = sqlite3.connect(DB_PATH)

    result = connection.execute("""
        SELECT MAX(published_at)
        FROM api_vacancies
    """).fetchone()[0]

    connection.close()

    if result is None:
        return None

    last_date = datetime.strptime(
        result,
        "%Y-%m-%dT%H:%M:%S%z"
    )

    date_from = last_date - timedelta(minutes=5)

    return date_from.strftime(
        "%Y-%m-%dT%H:%M:%S%z"
    )


def load_vacancies():
    started_at = datetime.now().astimezone().isoformat()

    rows_received = 0
    rows_inserted = 0

    try:
        if not token:
            raise RuntimeError(
                "В .env не найден HH_ACCESS_TOKEN"
            )

        create_database()

        date_from = get_date_from()

        if date_from:
            print(
                "Загружаем вакансии, опубликованные с:",
                date_from
            )
        else:
            print("Предыдущих данных нет.")

        connection = sqlite3.connect(DB_PATH)

        page = 0

        while True:
            params = {
                "area": 113,
                "per_page": 100,
                "page": page
            }

            if date_from:
                params["date_from"] = date_from

            response = requests.get(
                URL,
                params=params,
                headers=HEADERS,
                timeout=10
            )

            print(
                "Страница:",
                page,
                "| HTTP:",
                response.status_code
            )

            response.raise_for_status()

            data = response.json()
            vacancies = data["items"]

            rows_received += len(vacancies)

            for vacancy in vacancies:
                employer = vacancy.get("employer") or {}
                salary = vacancy.get("salary") or {}
                area = vacancy.get("area") or {}
                experience = vacancy.get("experience") or {}
                employment_form = (
                    vacancy.get("employment_form") or {}
                )

                loaded_at = (
                    datetime.now()
                    .astimezone()
                    .isoformat()
                )

                cursor = connection.execute(
                    """
                    INSERT OR IGNORE INTO api_vacancies (
                        vacancy_id,
                        name,
                        employer_id,
                        employer_name,
                        area_id,
                        area_name,
                        salary_from,
                        salary_to,
                        salary_currency,
                        salary_gross,
                        published_at,
                        created_at,
                        professional_roles,
                        experience,
                        employment_form,
                        work_format,
                        work_schedule_by_days,
                        alternate_url,
                        loaded_at
                    )
                    VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        vacancy.get("id"),
                        vacancy.get("name"),
                        employer.get("id"),
                        employer.get("name"),
                        area.get("id"),
                        area.get("name"),
                        salary.get("from"),
                        salary.get("to"),
                        salary.get("currency"),
                        salary.get("gross"),
                        vacancy.get("published_at"),
                        vacancy.get("created_at"),
                        list_to_text(
                            vacancy.get(
                                "professional_roles"
                            )
                        ),
                        experience.get("name"),
                        employment_form.get("name"),
                        list_to_text(
                            vacancy.get("work_format")
                        ),
                        list_to_text(
                            vacancy.get(
                                "work_schedule_by_days"
                            )
                        ),
                        vacancy.get("alternate_url"),
                        loaded_at
                    )
                )

                if cursor.rowcount == 1:
                    rows_inserted += 1

            connection.commit()

            page += 1

            if page >= data["pages"]:
                break

            # API поиска hh.ru ограничивает глубину
            # выдачи 2000 вакансиями
            if page >= 20:
                break

        connection.close()

        finished_at = (
            datetime.now()
            .astimezone()
            .isoformat()
        )

        write_log(
            started_at,
            finished_at,
            "success",
            rows_received,
            rows_inserted
        )

        print()
        print("Получено вакансий:", rows_received)
        print("Добавлено новых:", rows_inserted)

    except Exception as error:
        finished_at = (
            datetime.now()
            .astimezone()
            .isoformat()
        )

        write_log(
            started_at,
            finished_at,
            "error",
            rows_received,
            rows_inserted,
            str(error)
        )

        print("Ошибка:", error)


if __name__ == "__main__":
    load_vacancies()