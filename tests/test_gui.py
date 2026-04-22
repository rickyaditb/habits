import datetime
import uuid

from nicegui import ui
from nicegui.testing import User

from beaverhabits.frontend.history_page import all_history_page_ui, history_page_ui
from beaverhabits.frontend.add_page import add_page_ui
from beaverhabits.frontend.habit_page import habit_page_ui
from beaverhabits.frontend.index_page import index_page_ui
from beaverhabits.frontend.order_page import order_page_ui
from beaverhabits.frontend.settings_page import settings_page
from beaverhabits.frontend.stats_page import stats_page_ui
from beaverhabits import views
from beaverhabits.views import dummy_habit_list

# Test cases:
# https://github.com/zauberzeug/nicegui/tree/main/tests


def dummy_today():
    return datetime.date(2024, 5, 1)


def dummy_days(count):
    today = dummy_today()
    return [today - datetime.timedelta(days=i) for i in reversed(range(count))]


async def test_index_page(user: User) -> None:
    days = dummy_days(7)
    habits = dummy_habit_list(days)

    @ui.page("/")
    def page():
        index_page_ui(days, habits)

    await user.open("/")
    await user.should_see("Habits")


async def test_add_page(user) -> None:
    days = dummy_days(7)
    habits = dummy_habit_list(days)

    @ui.page("/")
    def page():
        add_page_ui(habits)

    await user.open("/")
    await user.should_see("Habits")


async def test_order_page(user) -> None:
    days = dummy_days(7)
    habits = dummy_habit_list(days)

    @ui.page("/")
    def page():
        order_page_ui(habits)

    await user.open("/")
    await user.should_see("Habits")


async def test_habit_detail_page(user) -> None:
    days = dummy_days(7)
    today = days[-1]
    habits = dummy_habit_list(days)
    habit = habits.habits[0]

    @ui.page("/")
    def page():
        habit_page_ui(today, habit)

    await user.open("/")
    await user.should_see("Order pizz")


async def test_habit_stats_page(user) -> None:
    days = dummy_days(7)
    today = days[-1]
    habits = dummy_habit_list(days)

    @ui.page("/")
    def page():
        stats_page_ui(today, habits)

    await user.open("/")
    await user.should_see("Order pizz")


async def test_habit_history_page(user) -> None:
    days = dummy_days(7)
    habits = dummy_habit_list(days)
    habit = habits.habits[0]

    @ui.page("/")
    def page():
        history_page_ui(habit)

    await user.open("/")
    await user.should_see("Completion History")
    await user.should_see("Order pizz")


async def test_global_history_page(user) -> None:
    days = dummy_days(7)
    habits = dummy_habit_list(days)
    first_habit = habits.habits[0]
    await first_habit.tick(days[-1], True)

    @ui.page("/")
    def page():
        all_history_page_ui(habits)

    await user.open("/")
    await user.should_see("Completion History")
    await user.should_see(first_habit.name)


async def test_settings_page(user: User) -> None:
    class DummyUser:
        id = uuid.uuid4()

    @ui.page("/")
    async def page():
        await settings_page(DummyUser())

    await user.open("/")
    await user.should_see("Settings")
    await user.should_see("Day columns on homepage")


async def test_demo_settings_page(user: User) -> None:
    @ui.page("/")
    async def page():
        await settings_page()

    await user.open("/")
    await user.should_see("Settings")
    await user.should_see("Day columns on homepage")


def test_get_homepage_day_columns_from_config() -> None:
    configs = views.UserConfigs(homepage_day_columns=3)
    assert views.get_homepage_day_columns(configs) == 3


def test_get_homepage_day_columns_from_config_caps_max() -> None:
    configs = views.UserConfigs(homepage_day_columns=9)
    assert views.get_homepage_day_columns(configs) == views.MAX_HOMEPAGE_DAY_COLUMNS
