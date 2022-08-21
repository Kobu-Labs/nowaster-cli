import random
from typing import List, Optional

import requests
import typer
from rich.color import ANSI_COLOR_NAMES
from rich.console import Console
from rich.table import Table
from rich.text import Text

import schemas

app = typer.Typer()
console = Console()

SERVER_ADDR = "http://127.0.0.1:8000"


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
            category_colors[e.category] = random.choice(list(ANSI_COLOR_NAMES.keys()))

        category_rich = Text(e.category)
        category_rich.stylize(category_colors[e.category])
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


if __name__ == "__main__":
    app()
