import random
from datetime import datetime, timedelta
from typing import List, Optional

import requests
import typer
from rich.color import ANSI_COLOR_NAMES
from rich.console import Console
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from config import ADDRESS
from schemas.recordentry import RecordEntryInDb
from schemas.solidentry import SolidEntry, SolidEntryCreate

app = typer.Typer()
console = Console()

__COLORS = list(ANSI_COLOR_NAMES.keys())

MIN_HOURS = 0.1
MIN_MINUTES = 1


def get_random_style() -> str:
    return random.choice(__COLORS)


def parse_time_unit(unit: str) -> float:
    if len(unit) <= 1:
        raise typer.BadParameter("Either number or unit was not passed")

    time_unit = unit[-1]
    value_raw = unit[: len(unit) - 1]

    try:
        value = float(value_raw)
    except ValueError:
        raise typer.BadParameter("Invalid number format")

    if value < MIN_MINUTES and time_unit == "m":
        raise typer.BadParameter(f"minimum minutes is {MIN_MINUTES}")
    if value < MIN_HOURS and time_unit == "h":
        raise typer.BadParameter(f"minimum hours is {MIN_HOURS}")

    if time_unit == "m":
        result = timedelta(minutes=value)
    elif time_unit == "h":
        result = timedelta(hours=value)
    else:
        raise typer.BadParameter("Invalid time unit")

    return result.total_seconds() / 60


@app.command()
def new(
    category: str = typer.Option(..., "--cat", "-c", prompt="cat"),
    duration_raw: str = typer.Option(..., "--dur", "-d", prompt="dur"),
    description: str = typer.Option("", "--description", prompt="Desc"),
) -> None:
    active_session = get_active_session()
    if active_session is not None:
        should_continue = typer.confirm(
            "One session is already active, continue anyways?"
        )
        if not should_continue:
            return

    duration = parse_time_unit(duration_raw)
    start_date = datetime.now()
    end_date = start_date + timedelta(minutes=duration)
    entry = SolidEntryCreate(
        category=category,
        start_date=start_date,
        end_date=end_date,
        description=description,
    )
    response = requests.post(ADDRESS + "/entry/solid", data=entry.json())
    print(f"created {response.json()}")


def fetch_all() -> List[SolidEntry]:
    data = requests.get(ADDRESS + "/entry/solid").json()
    return [SolidEntry(**e) for e in data]


def format_date(datetime_obj: datetime) -> str:
    return datetime.strftime(datetime_obj, "%Y-%m-%d %H:%M")


@app.command()
def all(show_ids: bool = typer.Option(False, "--id")) -> None:
    sessions = fetch_all()

    table = Table()
    if show_ids:
        table.add_column("ID")
    for column in ("Category", "Duration(mins)", "Start", "End"):
        table.add_column(column)

    category_colors = {}

    for e in sessions:
        duration = str((e.end_date - e.start_date).total_seconds() // 60)
        if not e.category in category_colors:
            category_colors[e.category] = get_random_style()

        category_rich = Text(e.category, style=category_colors[e.category])
        if show_ids:
            table.add_row(
                str(e.id),
                category_rich,
                format_date(e.start_date),
                format_date(e.end_date),
            )
        else:
            table.add_row(
                category_rich,
                duration,
                format_date(e.start_date),
                format_date(e.end_date),
            )

    console.print(table)


def get_datetime_progress_ratio(
    start: datetime, end: datetime, progress: datetime
) -> float:
    return (progress.timestamp() - start.timestamp()) / (
        end.timestamp() - start.timestamp()
    )


def get_active_session() -> Optional[SolidEntry]:
    data = requests.get(ADDRESS + "/entry/solid/active/", params={"local_time":datetime.now().isoformat()})
    if data.status_code != 200:
        return None

    if not data.json():
        return None

    return SolidEntry(**data.json())


@app.command()
def active() -> None:
    session = get_active_session()
    if session is None:
        print("No active session")
        return

    completed = get_datetime_progress_ratio(
        session.start_date, session.end_date, datetime.now()
    )
    bar = ProgressBar(completed=completed * 100, width=70, complete_style="green")
    percentage = Text(f"  {bar.percentage_completed:.2f}%", get_random_style())

    console.print(bar, percentage, "\n")


@app.command()
def abort() -> None:
    requests.delete(ADDRESS + "/entry/solid")


@app.command()
def record(
    category: str = typer.Option(..., "--cat", "-c", prompt="cat"),
    description: str = typer.Option("", "--description", prompt="Desc"),
) -> None:
    active_session = get_active_session()
    if active_session is not None:
        should_continue = typer.confirm(
            "One session is already active, continue anyways?"
        )
        if not should_continue:
            return
    response = requests.post(
        ADDRESS + "/entry/record",
        json={"category": category, "description": description},
    )
    print(response)


@app.command()
def timed_active() -> None:
    response = requests.get(ADDRESS + "/entry/record/active")
    sessions = [RecordEntryInDb(**e) for e in response.json()]

    table = Table()
    for col in ("ID", "Category", "Start"):
        table.add_column(col)

    category_colors = {}

    for e in sessions:
        if not e.category in category_colors:
            category_colors[e.category] = get_random_style()

        category_rich = Text(e.category, style=category_colors[e.category])
        table.add_row(str(e.id), category_rich, str(e.start_date))

    console.print(table)


@app.command()
def finish() -> None:
    response = requests.post(ADDRESS + f"/entry/record/finish/")
    print(response.json())


def update_datetime(raw_datetime: datetime) -> datetime:
    if raw_datetime.year == 1900:
        # only hours and minutes were passed if year == 1900 -> set year, month, day to today
        now = datetime.now()
        return datetime(
            now.year, now.month, now.day, raw_datetime.hour, raw_datetime.minute
        )
    return raw_datetime


@app.command()
def backlog(
    category: str = typer.Option(..., "--cat", "-c", prompt="cat"),
    start_date_raw: datetime = typer.Option(
        ..., "--start", "-s", prompt="start", formats=["%Y-%m-%d %H:%M", "%H:%M"]
    ),
    end_date_raw: datetime = typer.Option(
        ..., "--end", "-e", prompt="end", formats=["%Y-%m-%d %H:%M", "%H:%M"]
    ),
    description: str = typer.Option("", "--description", prompt="Desc"),
) -> None:
    start_date = update_datetime(start_date_raw)
    end_date = update_datetime(end_date_raw)

    entry = SolidEntryCreate(
        category=category,
        start_date=start_date,
        end_date=end_date,
        description=description,
    )
    response = requests.post(ADDRESS + "/entry/solid", data=entry.json())
    print(f"created {response.json()}")


if __name__ == "__main__":
    app()
