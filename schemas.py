from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TrackEntryBase(BaseModel):
    category: str
    duration: int
    description: Optional[str] = None


class TrackEntryCreate(TrackEntryBase):
    ...


class TrackEntry(TrackEntryBase):
    id: int
    start_date: datetime
    end_date: datetime

    class Config:
        orm_mode = True
