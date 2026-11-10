import os

import requests
from dotenv import load_dotenv


load_dotenv()

token = os.getenv("HH_ACCESS_TOKEN")

url = "https://api.hh.ru/vacancies"

params = {
    "area": 113,
    "per_page": 5,
    "page": 0
}

headers = {
    "Authorization": f"Bearer {token}",
    "HH-User-Agent": "LaborMarketMonitoring/1.0 maradudinaula@gmail.com"
}

response = requests.get(
    url,
    params=params,
    headers=headers,
    timeout=10
)

print("HTTP-статус:", response.status_code)

if response.status_code == 200:
    data = response.json()

    print("Всего найдено вакансий:", data["found"])
    print()

    for vacancy in data["items"]:
        print(
            vacancy["id"],
            "|",
            vacancy["name"],
            "|",
            vacancy["area"]["name"],
            "|",
            vacancy["published_at"]
        )
else:
    print(response.text)