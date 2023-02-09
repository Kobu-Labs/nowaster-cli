from datetime import datetime, timedelta

import typer

MIN_HOURS = 0.1
MIN_MINUTES = 1


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


def get_datetime_progress_ratio(
    start: datetime, end: datetime, progress: datetime
) -> float:
    return (progress.timestamp() - start.timestamp()) / (
        end.timestamp() - start.timestamp()
    )


def update_datetime(raw_datetime: datetime) -> datetime:
    if raw_datetime.year == 1900:
        # only hours and minutes were passed if year == 1900 -> set year, month, day to today
        now = datetime.now()
        return datetime(
            now.year, now.month, now.day, raw_datetime.hour, raw_datetime.minute
        )
    return raw_datetime
