from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RecordEntryBase(BaseModel):
    category: str
    description: Optional[str] = None


class CreateRecordEntry(RecordEntryBase):
    ...


class RecordEntryInDb(RecordEntryBase):
    class Config:
        orm_mode = True

    id: int
    start_date: datetime

