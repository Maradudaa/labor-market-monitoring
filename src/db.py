import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "labor_market.db"


def create_database():
    connection = sqlite3.connect(DB_PATH)

    # Таблица с историческими данными из CSV
    connection.execute("""
        CREATE TABLE IF NOT EXISTS historical_vacancies (
            vacancy_id INTEGER PRIMARY KEY,
            employer_id INTEGER,
            employees_number INTEGER,
            creation_date TEXT,
            work_schedule TEXT,
            employment TEXT,
            length_of_employment TEXT,
            compensation_from REAL,
            compensation_to REAL,
            accept_teenagers INTEGER,
            specialization TEXT,
            region_name TEXT,
            response_count INTEGER,
            female_response_count INTEGER,
            male_response_count INTEGER,
            young_response_count INTEGER,
            young_female_response_count INTEGER,
            young_male_response_count INTEGER,
            invitation_count INTEGER,
            female_invitation_count INTEGER,
            male_invitation_count INTEGER,
            young_invitation_count INTEGER,
            young_female_invitation_count INTEGER,
            young_male_invitation_count INTEGER,
            industry_id_list TEXT
        )
    """)

    # Таблица с актуальными вакансиями из API hh.ru
    connection.execute("""
        CREATE TABLE IF NOT EXISTS api_vacancies (
            vacancy_id TEXT PRIMARY KEY,
            name TEXT,
            employer_id TEXT,
            employer_name TEXT,
            area_id TEXT,
            area_name TEXT,
            salary_from REAL,
            salary_to REAL,
            salary_currency TEXT,
            salary_gross INTEGER,
            published_at TEXT,
            created_at TEXT,
            professional_roles TEXT,
            experience TEXT,
            employment_form TEXT,
            work_format TEXT,
            work_schedule_by_days TEXT,
            alternate_url TEXT,
            loaded_at TEXT
        )
    """)

    connection.commit()
    connection.close()

    print("База данных создана.")


if __name__ == "__main__":
    create_database()