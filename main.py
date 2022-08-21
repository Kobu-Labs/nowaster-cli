from datetime import datetime
from typing import List, Optional
import random

import requests

import schemas

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.color import ANSI_COLOR_NAMES
from rich.progress_bar import ProgressBar

import typer

app = typer.Typer()
console = Console()

SERVER_ADDR = "http://127.0.0.1:8000"
__COLORS = list(ANSI_COLOR_NAMES.keys())


def get_random_style() -> str:
    return random.choice(__COLORS)


@app.command()
def new(
    category: str = typer.Option(..., "--cat", "-c"),
    duration: int = typer.Option(..., "--dur", "-d"),
    description: Optional[str] = "",
) -> None:
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
    for column in ("Category", "Duration", "Start", "End"):
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


if __name__ == "__main__":
    app()
