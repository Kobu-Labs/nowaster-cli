from typing import List

import requests

from config import ADDRESS
from src.schemas.recordentry import RecordEntryInDb


def get_active() -> List[RecordEntryInDb]:
    entries = requests.get(ADDRESS + "/entry/record/active").json()
    return [RecordEntryInDb(**e) for e in entries]


def finnish() -> RecordEntryInDb:
    return RecordEntryInDb(**requests.post(ADDRESS + f"/entry/record/finish/").json())


def create_new(category: str, description: str) -> requests.Response:
    return requests.post(
        ADDRESS + "/entry/record",
        json={"category": category, "description": description},
    )
