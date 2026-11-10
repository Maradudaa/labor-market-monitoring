from datetime import datetime
from pathlib import Path

import pandas as pd

from db import DB_PATH, create_database


BASE_DIR = Path(__file__).resolve().parent.parent

CSV_PATH = BASE_DIR / "data" / "raw" / "hh ru DATASET.csv"
LOG_PATH = BASE_DIR / "logs" / "load_log.csv"


COLUMNS = [
    "vacancy_id",
    "employer_id",
    "employees_number",
    "creation_date",
    "work_schedule",
    "employment",
    "length_of_employment",
    "compensation_from",
    "compensation_to",
    "accept_teenagers",
    "specialization",
    "region_name",
    "response_count",
    "female_response_count",
    "male_response_count",
    "young_response_count",
    "young_female_response_count",
    "young_male_response_count",
    "invitation_count",
    "female_invitation_count",
    "male_invitation_count",
    "young_invitation_count",
    "young_female_invitation_count",
    "young_male_invitation_count",
    "industry_id_list"
]


def write_log(
    started_at,
    finished_at,
    status,
    rows_received,
    rows_inserted,
    error=""
):
    log_record = pd.DataFrame([{
        "source": "historical_csv",
        "started_at": started_at,
        "finished_at": finished_at,
        "status": status,
        "rows_received": rows_received,
        "rows_inserted": rows_inserted,
        "error": error
    }])

    if LOG_PATH.exists():
        log_record.to_csv(
            LOG_PATH,
            mode="a",
            header=False,
            index=False
        )
    else:
        log_record.to_csv(
            LOG_PATH,
            index=False
        )


def prepare_value(value):
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def load_historical():
    create_database()

    started_at = datetime.now().isoformat()

    rows_received = 0
    rows_inserted = 0

    try:
        import sqlite3

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        insert_query = """
            INSERT OR IGNORE INTO historical_vacancies (
                vacancy_id,
                employer_id,
                employees_number,
                creation_date,
                work_schedule,
                employment,
                length_of_employment,
                compensation_from,
                compensation_to,
                accept_teenagers,
                specialization,
                region_name,
                response_count,
                female_response_count,
                male_response_count,
                young_response_count,
                young_female_response_count,
                young_male_response_count,
                invitation_count,
                female_invitation_count,
                male_invitation_count,
                young_invitation_count,
                young_female_invitation_count,
                young_male_invitation_count,
                industry_id_list
            )
            VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?
            )
        """

        for chunk in pd.read_csv(CSV_PATH, chunksize=10000):

            chunk = chunk[COLUMNS]

            rows_received += len(chunk)

            rows = []

            for row in chunk.itertuples(index=False, name=None):
                prepared_row = tuple(
                    prepare_value(value)
                    for value in row
                )

                rows.append(prepared_row)

            changes_before = connection.total_changes

            cursor.executemany(
                insert_query,
                rows
            )

            connection.commit()

            changes_after = connection.total_changes

            rows_inserted += (
                changes_after - changes_before
            )

        connection.close()

        finished_at = datetime.now().isoformat()

        write_log(
            started_at=started_at,
            finished_at=finished_at,
            status="success",
            rows_received=rows_received,
            rows_inserted=rows_inserted
        )

        print("Исторический источник успешно загружен.")
        print("Получено строк:", rows_received)
        print("Добавлено строк:", rows_inserted)

    except Exception as error:

        finished_at = datetime.now().isoformat()

        write_log(
            started_at=started_at,
            finished_at=finished_at,
            status="error",
            rows_received=rows_received,
            rows_inserted=rows_inserted,
            error=str(error)
        )

        raise


if __name__ == "__main__":
    load_historical()