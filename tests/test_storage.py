import datetime
from unittest.mock import patch

import pytz

from beaverhabits.storage.dict import DictHabit, DictHabitList
from beaverhabits.frontend.history_page import (
    _format_completed_at,
    _sorted_completed_records,
)


async def test_tick_stores_completed_at_timestamp():
    habit_list = DictHabitList(
        {
            "habits": [
                {
                    "id": "habit-1",
                    "name": "Running",
                    "records": [],
                }
            ]
        }
    )
    habit = DictHabit(habit_list.data["habits"][0], habit_list)

    day = datetime.date(2026, 4, 22)
    record = await habit.tick(day, True)

    assert record.completed_at is not None
    assert record.completed_at.tzinfo is not None
    assert record.completed_at.tzinfo.utcoffset(record.completed_at) == pytz.UTC.utcoffset(
        record.completed_at
    )

    previous_completed_at = record.completed_at
    record = await habit.tick(day, False)
    assert record.completed_at == previous_completed_at


async def test_history_is_sorted_by_check_time_not_habit_day():
    habit_list = DictHabitList(
        {
            "habits": [
                {
                    "id": "habit-1",
                    "name": "Running",
                    "records": [
                        {
                            "day": "2026-04-22",
                            "done": True,
                            "completed_at": "2026-04-22T08:00:00+00:00",
                        },
                        {
                            "day": "2026-04-18",
                            "done": True,
                            "completed_at": "2026-04-22T09:00:00+00:00",
                        },
                    ],
                }
            ]
        }
    )
    habit = DictHabit(habit_list.data["habits"][0], habit_list)

    records = _sorted_completed_records(habit)

    assert [record.day for record in records] == [
        datetime.date(2026, 4, 18),
        datetime.date(2026, 4, 22),
    ]


def test_format_completed_at_shows_time_only_for_today():
    timezone = pytz.timezone("UTC")
    fixed_now = timezone.localize(datetime.datetime(2026, 4, 22, 12, 0, 0))

    class FixedDateTime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz is not None else fixed_now.replace(tzinfo=None)

    with patch("beaverhabits.frontend.history_page.datetime.datetime", FixedDateTime):
        today_value = timezone.localize(datetime.datetime(2026, 4, 22, 9, 15, 0))
        older_value = timezone.localize(datetime.datetime(2026, 4, 21, 9, 15, 0))

        assert _format_completed_at(today_value) == "9:15 AM"
        assert _format_completed_at(older_value) == "21 Apr 2026"
import uuid

import pytest
from nicegui import ui
from nicegui.testing import User

from beaverhabits import views
from beaverhabits.app.auth import user_authenticate, user_create
from beaverhabits.app.db import User as HabitUser
from beaverhabits.app.db import create_db_and_tables, engine
from beaverhabits.configs import StorageType, settings
from beaverhabits.utils import dummy_days

EMAIL = f"{uuid.uuid1()}@test.com"
PASSWORD = "test"


@pytest.fixture
async def habit_user():
    await create_db_and_tables()

    user = await user_authenticate(email=EMAIL, password=PASSWORD)
    if not user:
        user = await user_create(email=EMAIL, password=PASSWORD)
    yield user

    # close db connection after test
    await engine.dispose()


async def test_user_session(user: User):
    @ui.page("/")
    async def page():
        days = await dummy_days(5)
        habit_list = views.get_or_create_session_habit_list(days)
        assert habit_list is not None

    await user.open("/")


async def test_user_db(user: User, habit_user: HabitUser):
    settings.HABITS_STORAGE = StorageType.USER_DATABASE

    @ui.page("/")
    async def page():
        days = await dummy_days(5)
        habit_list = await views.get_or_create_user_habit_list(
            habit_user, views.dummy_habit_list(days)
        )
        assert habit_list is not None

        habit_list = await views.get_user_habit_list(habit_user)
        assert habit_list is not None

    await user.open("/")

    # close db connection after test

    await engine.dispose()


async def test_user_disk(user: User, habit_user: HabitUser):
    settings.HABITS_STORAGE = StorageType.USER_DISK

    @ui.page("/")
    async def page():
        days = await dummy_days(5)
        habit_list = await views.get_or_create_user_habit_list(
            habit_user, views.dummy_habit_list(days)
        )
        assert habit_list is not None

        habit_list = await views.get_user_habit_list(habit_user)
        assert habit_list is not None

    await user.open("/")
    # close db connection after test
    await engine.dispose()
