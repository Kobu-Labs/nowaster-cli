import json
from datetime import datetime, timedelta
from typing import List

import typer

from src import gui, utils
from src.endpoints import record, solid
from src.schemas.solidentry import SolidEntry, SolidEntryCreate

app = typer.Typer()


@app.command()
def graph() -> None:
    entities: List[SolidEntry] = solid.fetch_all()
    start_date = min(entities, key=lambda x: x.start_date).start_date
    end_date = max(entities, key=lambda x: x.end_date).end_date

    data = gui.group_categories(entities)
    gui.show_graph(start_date, end_date, data)


@app.command()
def export(filename: str = typer.Argument("nowaster-export")) -> None:
    with open(filename, "w") as file:
        json.dump(solid.fetch_all_raw(), file, indent=4)


@app.command("import")
def import_command(filename: str = typer.Argument(...)) -> None:
    entries_str: str
    with open(filename, "r") as file:
        entries_str = json.load(file)
    solid.import_entries(entries_str)


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
    start_date = utils.update_datetime(start_date_raw)
    end_date = utils.update_datetime(end_date_raw)

    entry = SolidEntryCreate(
        category=category,
        start_date=start_date,
        end_date=end_date,
        description=description,
    )
    response = solid.create_new_solid(entry)
    print(f"created {response.json()}")


@app.command()
def active() -> None:
    session = solid.get_active_session()
    if session is None:
        print("No active session")
        return

    completed = utils.get_datetime_progress_ratio(
        session.start_date, session.end_date, datetime.now()
    )

    gui.show_active_progress(completed)


@app.command()
def abort() -> None:
    solid.abort_current_entry()


@app.command("record")
def new_record(
    category: str = typer.Option(..., "--cat", "-c", prompt="cat"),
    description: str = typer.Option("", "--description", prompt="Desc"),
) -> None:
    active_session = record.get_active()
    if active_session is not None:
        should_continue = typer.confirm(
            "One session is already active, continue anyways?"
        )
        if not should_continue:
            return
    response = record.create_new(category, description)
    print(response)


@app.command()
def timed_active() -> None:
    recordings = record.get_active()
    gui.show_active_recordings(recordings)


@app.command()
def finish() -> None:
    print(record.finnish())


@app.command()
def all(show_ids: bool = typer.Option(False, "--id")) -> None:
    entries = solid.fetch_all()
    gui.show_entry_table(entries, show_ids)


@app.command()
def new(
    category: str = typer.Option(..., "--cat", "-c", prompt="cat"),
    duration_raw: str = typer.Option(..., "--dur", "-d", prompt="dur"),
    description: str = typer.Option("", "--description", prompt="Desc"),
) -> None:
    active_session = solid.get_active_session()
    if active_session is not None:
        should_continue = typer.confirm(
            "One session is already active, continue anyways?"
        )
        if not should_continue:
            return

    duration = utils.parse_time_unit(duration_raw)
    start_date = datetime.now()
    end_date = start_date + timedelta(minutes=duration)
    entry = SolidEntryCreate(
        category=category,
        start_date=start_date,
        end_date=end_date,
        description=description,
    )
    response = solid.create_new_solid(entry)

    if response.ok:
        gui.show_new_entry_success(SolidEntry(**response.json()))
    else:
        gui.show_generic_error_message(
            "Failed to create a new entry!\n" + response.reason
        )
