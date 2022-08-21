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

import schemas

app = typer.Typer()
console = Console()

SERVER_ADDR = "http://127.0.0.1:8000"
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
    category: str = typer.Option(..., "--cat", "-c"),
    duration_raw: str = typer.Option(..., "--dur", "-d"), description: Optional[str] = None,
) -> None:
    duration = parse_time_unit(duration_raw)
    response = requests.post(
        SERVER_ADDR + "/entries",
        json={"category": category, "duration": duration, "description": description},
    )
    print(f"created {response.json()}")


def fetch_all() -> List[schemas.TrackEntry]:
    data = requests.get(SERVER_ADDR + "/" + "entries").json()
    return [schemas.TrackEntry(**e) for e in data]


@app.command()
def all(show_ids: bool = typer.Option(False, "--id")) -> None:
    data = fetch_all()

    table = Table()
    if show_ids:
        table.add_column("ID")
    for column in ("Category", "Duration(mins)", "Start", "End"):
        table.add_column(column)

    category_colors = {}

    for e in data:
        if not e.category in category_colors:
            category_colors[e.category] = get_random_style()

        category_rich = Text(e.category, style=category_colors[e.category])
        if show_ids:
            table.add_row(
                str(e.id),
                category_rich,
                str(e.duration),
                str(e.start_date),
                str(e.end_date),
            )
        else:
            table.add_row(
                category_rich, str(e.duration), str(e.start_date), str(e.end_date)
            )

    console.print(table)


def get_datetime_progress_ratio(
    start: datetime, end: datetime, progress: datetime
) -> float:
    return (progress.timestamp() - start.timestamp()) / (
        end.timestamp() - start.timestamp()
    )


@app.command()
def active() -> None:
    data = requests.get(SERVER_ADDR + "/entries/active").json()
    if not data:
        typer.echo("No active session")
        return

    track_e = schemas.TrackEntry(**data)

    completed = get_datetime_progress_ratio(
        track_e.start_date, track_e.end_date, datetime.now()
    )
    bar = ProgressBar(completed=completed * 100, width=70, complete_style="green")
    percentage = Text(f"  {bar.percentage_completed:.2f}%", get_random_style())

    console.print(bar, percentage, "\n")


@app.command()
def abort() -> None:
    requests.delete(SERVER_ADDR + "/active")


if __name__ == "__main__":
    app()
