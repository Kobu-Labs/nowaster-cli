from datetime import datetime
from typing import Any, Dict, List, Optional, cast

import requests

from config import ADDRESS
from src.schemas.solidentry import SolidEntry, SolidEntryCreate

DictStrAny = Dict[str, Any]


def fetch_all_raw() -> List[DictStrAny]:
    return cast(List[DictStrAny], requests.get(ADDRESS + "/entry/solid").json())


def fetch_all() -> List[SolidEntry]:
    return [SolidEntry(**e) for e in fetch_all_raw()]


def get_active_session() -> Optional[SolidEntry]:
    data = requests.get(
        ADDRESS + "/entry/solid/active/",
        params={"local_time": datetime.now().isoformat()},
    )
    if data.status_code != 200:
        return None

    if not data.json():
        return None

    return SolidEntry(**data.json())


def import_entries(entries_json_str: str) -> None:
    requests.post(ADDRESS + "/entry/solid/import", json=entries_json_str)


def abort_current_entry() -> None:
    requests.delete(ADDRESS + "/entry/solid")


def create_new_solid(entry: SolidEntryCreate) -> requests.Response:
    return requests.post(ADDRESS + "/entry/solid", data=entry.json())
