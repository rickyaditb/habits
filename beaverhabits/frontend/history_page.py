import datetime

import pytz
from nicegui import ui

from beaverhabits.frontend.layout import layout
from beaverhabits.storage.meta import get_habit_page_path
from beaverhabits.storage.storage import Habit, HabitList, HabitListBuilder, HabitStatus
from beaverhabits.utils import get_or_create_user_timezone_sync

HISTORY_CONTENT_WIDTH = 420


def _format_completed_at(value: datetime.datetime | None) -> str:
    if value is None:
        return "Time unavailable"

    timezone_name = get_or_create_user_timezone_sync()
    timezone = pytz.timezone(timezone_name)
    if value.tzinfo is None:
        value = pytz.UTC.localize(value)

    local_value = value.astimezone(timezone)
    today = datetime.datetime.now(timezone).date()
    if local_value.date() == today:
        return local_value.strftime("%I:%M %p").lstrip("0")

    return local_value.strftime("%d %b %Y")


def _sorted_completed_records(habit: Habit):
    return sorted(
        (record for record in habit.records if record.done),
        key=lambda record: (
            record.completed_at or datetime.datetime.min.replace(tzinfo=pytz.UTC),
            record.day,
        ),
        reverse=True,
    )


def _history_row(habit: Habit, record) -> None:
    with ui.row().classes("w-full items-start justify-between px-4 py-3 gap-4"):
        with ui.column().classes("gap-0"):
            ui.link(habit.name, get_habit_page_path(habit)).classes(
                "text-base no-underline hover:no-underline"
            )
            ui.label(record.day.strftime("%A, %d %b %Y")).classes("text-sm text-gray-500")
            if record.text:
                ui.label(record.text).classes("text-sm text-gray-500 whitespace-pre-wrap")

        with ui.column().classes("gap-0 items-end shrink-0"):
            ui.badge("Checked").props("color=positive")
            ui.label(_format_completed_at(record.completed_at)).classes("text-sm text-gray-500")


def _build_global_records(habit_list: HabitList) -> list[tuple[Habit, object]]:
    records: list[tuple[Habit, object]] = []
    habits = HabitListBuilder(habit_list).status(
        HabitStatus.ACTIVE,
        HabitStatus.ARCHIVED,
    ).build()
    for habit in habits:
        for record in habit.records:
            if record.done:
                records.append((habit, record))

    return sorted(
        records,
        key=lambda item: (
            item[1].completed_at or datetime.datetime.min.replace(tzinfo=pytz.UTC),
            item[1].day,
            item[0].name.lower(),
        ),
        reverse=True,
    )


def history_page_ui(habit: Habit):
    with layout(
        title=f"{habit.name} History",
        habit=habit,
        content_width=HISTORY_CONTENT_WIDTH,
    ):
        with ui.column().classes("gap-3 w-full"):
            ui.label("Completion History").classes("text-xl font-medium")

            records = _sorted_completed_records(habit)
            if not records:
                ui.label("No completed days yet.").classes("text-gray-500")
                return

            with ui.card().classes("w-full no-shadow p-0 overflow-hidden"):
                for index, record in enumerate(records):
                    _history_row(habit, record)

                    if index < len(records) - 1:
                        ui.separator()


def all_history_page_ui(habit_list: HabitList):
    with layout(
        title="History",
        habit_list=habit_list,
        content_width=HISTORY_CONTENT_WIDTH,
    ):
        with ui.column().classes("gap-3 w-full"):
            ui.label("Completion History").classes("text-xl font-medium")

            records = _build_global_records(habit_list)
            if not records:
                ui.label("No completed days yet.").classes("text-gray-500")
                return

            with ui.card().classes("w-full no-shadow p-0 overflow-hidden"):
                for index, (habit, record) in enumerate(records):
                    _history_row(habit, record)

                    if index < len(records) - 1:
                        ui.separator()