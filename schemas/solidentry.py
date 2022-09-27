from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EntryBase(BaseModel):
    category: str
    start_date: datetime
    end_date: datetime
    description: Optional[str] = None

class SolidEntryCreate(EntryBase):
    ...


class SolidEntry(EntryBase):
    class Config:
        orm_mode = True

    id: int

