import os
import json

import requests
from dotenv import load_dotenv


load_dotenv()

token = os.getenv("HH_ACCESS_TOKEN")

url = "https://api.hh.ru/vacancies"

params = {
    "area": 113,
    "per_page": 1,
    "page": 0
}

headers = {
    "Authorization": f"Bearer {token}",
    "HH-User-Agent": "LaborMarketMonitoring/1.0 maradudinaula@gail.com"
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

    vacancy = data["items"][0]

    print(json.dumps(
        vacancy,
        ensure_ascii=False,
        indent=4
    ))
else:
    print(response.text)