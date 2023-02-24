import random
from collections import defaultdict
from datetime import datetime
from typing import Callable, DefaultDict, Dict, List, Optional

import matplotlib.pyplot as plt
import rich
from rich.color import ANSI_COLOR_NAMES
from rich.console import Console
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from src.schemas.recordentry import RecordEntryInDb
from src.schemas.solidentry import SolidEntry

console = Console()

__COLORS = list(ANSI_COLOR_NAMES.keys())


def get_random_style() -> str:
    return random.choice(__COLORS)


def format_date(datetime_obj: datetime) -> str:
    return datetime.strftime(datetime_obj, "%Y-%m-%d %H:%M")


def group_categories(data: List[SolidEntry]) -> Dict[str, float]:
    result: DefaultDict[str, float] = defaultdict(float)
    for e in data:
        result[e.category] += (e.end_date - e.start_date).total_seconds() // 3600

    return result


def show_graph(start: datetime, end: datetime, data: Dict[str, float]) -> None:
    categories = data.keys()
    time_spent = data.values()

    def from_perc(val: float) -> str:
        return f"{sum(time_spent) / 100 * val:.1f}h"

    plt.pie(
        time_spent, autopct=from_perc, labels=categories, shadow=False, startangle=140
    )
    plt.title(
        f"Time spent per category\nTotal: {sum(time_spent)}\n{start.strftime('%b %d.')} - {end.strftime('%b %d.')}\nAverage: {sum(time_spent)/60:.2f}"
    )
    plt.show()


def show_active_progress(completed: float) -> None:
    bar = ProgressBar(completed=completed * 100, width=70, complete_style="green")
    percentage = Text(f"  {bar.percentage_completed:.2f}%", get_random_style())

    console.print(bar, percentage, "\n")


def show_active_recordings(recordings: List[RecordEntryInDb]) -> None:
    table = Table()
    for col in ("ID", "Category", "Start"):
        table.add_column(col)

    category_colors = {}

    for e in recordings:
        if not e.category in category_colors:
            category_colors[e.category] = get_random_style()

        category_rich = Text(e.category, style=category_colors[e.category])
        table.add_row(str(e.id), category_rich, str(e.start_date))

    console.print(table)


def show_entry_table(entries: List[SolidEntry], show_ids: bool = False) -> None:
    table = Table()
    if show_ids:
        table.add_column("ID")
    for column in ("Category", "Duration(mins)", "Start", "End"):
        table.add_column(column)

    category_colors = {}

    for e in entries:
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


def show_new_entry_success(entry: SolidEntry) -> None:
    time: Callable[[datetime], str] = lambda x: datetime.strftime(x, "%H:%M")
    duration = (entry.end_date - entry.start_date).total_seconds() // 60

    # <start_date> ------------<duration> mins------------> <end_date>
    content = (
        "[bold][green3]"
        + time(entry.start_date)
        + " "
        + 12 * "-"
        + str(duration)
        + " mins"
        + 12 * "-"
        + "> "
        + time(entry.end_date)
    )

    if entry.description:
        content += f"\n[grey37]Description: {entry.description}"

    rich.print(
        Panel.fit(
            content, title=f"[{get_random_style()}]{entry.category} entry created!"
        )
    )


def show_generic_error_message(
    message: str, exception: Optional[Exception] = None
) -> None:
    if exception is not None:
        message += f"\nError message: {exception}"
    rich.print(Panel.fit("[red]" + message, title="[red]Error occured!"))
