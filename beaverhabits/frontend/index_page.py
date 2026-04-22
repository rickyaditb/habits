import datetime
from typing import List

from nicegui import ui

from beaverhabits.configs import settings
from beaverhabits.core.completions import get_habit_date_completion
from beaverhabits.frontend import javascript, textarea
from beaverhabits.frontend.components import (
    HabitCheckBox,
    IndexStreakBadge,
    IndexTotalBadge,
    TagManager,
    get_all_tags,
    habit_name_menu,
    habits_by_tags,
    note_tick,
    menu_icon_button,
    tag_filter_component,
)
from beaverhabits.frontend.layout import layout
from beaverhabits.storage.meta import get_root_path
from beaverhabits.storage.storage import (
    Habit,
    HabitList,
    HabitListBuilder,
    HabitStatus,
)

NAME_COLS, DATE_COLS = settings.INDEX_HABIT_NAME_COLUMNS, 2
COUNT_BADGE_COLS = 2 if settings.INDEX_SHOW_HABIT_COUNT else 0
COUNT_BADGE_COLS += 2 if settings.INDEX_SHOW_HABIT_STREAK else 0
MIN_INDEX_CONTENT_WIDTH = 520
NAME_SECTION_WIDTH = 220
DAY_COLUMN_WIDTH = 56
BADGE_COLUMN_WIDTH = 56
MAX_INDEX_CONTENT_WIDTH = 440
LEFT_CLASSES, RIGHT_CLASSES = (
    # grid 5
    f"col-span-{NAME_COLS} truncate max-w-[{24 * NAME_COLS}px]",
    # grid 2 2 2 2 2
    f"col-span-{DATE_COLS} px-1 place-self-center",
)
COMPAT_CLASSES = "pl-4 pr-0 py-0 dark:shadow-none"

# Sticky date row for long habit list
STICKY_STYLES = "position: sticky; top: 0; z-index: 1;"


def grid(columns, rows):
    g = ui.grid(columns=columns, rows=rows)
    g.classes("w-full gap-0 items-center")
    return g


def index_content_width(days: list[datetime.date]) -> int:
    estimated_width = (
        NAME_SECTION_WIDTH
        + len(days) * DAY_COLUMN_WIDTH
        + (COUNT_BADGE_COLS // 2) * BADGE_COLUMN_WIDTH
        + 32
    )
    return min(MAX_INDEX_CONTENT_WIDTH, max(420, estimated_width))


def week_headers(days: list[datetime.date]):
    for day in days:
        yield day.strftime("%a")
    if settings.INDEX_SHOW_HABIT_STREAK:
        yield "Stk"
    if settings.INDEX_SHOW_HABIT_COUNT:
        yield "Sum"


def day_headers(days: list[datetime.date]):
    for day in days:
        yield day.strftime("%d")
    if settings.INDEX_SHOW_HABIT_STREAK:
        yield "*"
    if settings.INDEX_SHOW_HABIT_COUNT:
        yield "#"


def habit_row(habit: Habit, tag: str, days: list[datetime.date]):
    name = habit_name_menu(habit, index_page_ui.refresh)
    name.classes(LEFT_CLASSES)
    name.props(f'role="heading" aria-level="2" aria-label="{habit.name}"')

    today = max(days)
    status_map = get_habit_date_completion(habit, min(days), today)
    for day in days:
        status = status_map.get(day, [])
        checkbox = HabitCheckBox(
            status,
            habit,
            today,
            day,
            refresh=habit_list_ui.refresh,
            enable_long_press_note=False,
        )
        checkbox.classes(RIGHT_CLASSES)
        # checkbox.classes("theme-icon-lazy invisible")

    if settings.INDEX_SHOW_HABIT_STREAK:
        IndexStreakBadge(today, habit).classes(RIGHT_CLASSES)

    if settings.INDEX_SHOW_HABIT_COUNT:
        IndexTotalBadge(today, habit).classes(RIGHT_CLASSES)


def habit_matches_tag_filters(habit: Habit) -> bool:
    selected_tags = TagManager.get_all()
    if not selected_tags:
        return True

    if not habit.tags:
        return "Others" in selected_tags

    return any(tag in selected_tags for tag in habit.tags)


@ui.refreshable
def habit_list_ui(days: list[datetime.date], active_habits: List[Habit], update_filter_state=None):
    # Total cloumn for each row
    columns = NAME_COLS + len(days) * DATE_COLS + COUNT_BADGE_COLS
    row_elements = []
    group_elements = []

    with ui.column().classes("w-full gap-1.5"):
        # Date Headers
        with grid(columns, 2).classes(COMPAT_CLASSES).style(STICKY_STYLES) as g:
            g.props('aria-hidden="true"').classes("theme-header-date")
            for it in (week_headers(days), day_headers(days)):
                ui.label("").classes(LEFT_CLASSES)
                for label in it:
                    ui.label(label).classes(RIGHT_CLASSES)

        # Habit Rows
        groups = habits_by_tags(active_habits)

        for tag, habit_list in groups.items():
            if not habit_list:
                continue

            with ui.column().classes("w-full gap-1.5") as group_column:
                for habit in habit_list:
                    with ui.card().classes(COMPAT_CLASSES).classes("theme-card-shadow w-full") as card:
                        with grid(columns, 1):
                            habit_row(habit, tag, days)
                    row_elements.append((tag, habit, card))

                ui.space()

            group_elements.append((tag, group_column))

    if update_filter_state:
        update_filter_state(row_elements, group_elements)


@ui.refreshable
def index_page_ui(days: list[datetime.date], habits: HabitList):
    active_habits = HabitListBuilder(habits).status(HabitStatus.ACTIVE).build()
    if settings.INDEX_HABIT_DATE_REVERSE:
        days = list(reversed(days))
    row_elements = []
    group_elements = []

    def sync_filter_state(new_row_elements, new_group_elements) -> None:
        row_elements.clear()
        row_elements.extend(new_row_elements)
        group_elements.clear()
        group_elements.extend(new_group_elements)
        apply_tag_filters()

    def apply_tag_filters() -> None:
        visible_groups = set()
        for tag, habit, element in row_elements:
            visible = not settings.ENABLE_TAG_FILTERS or habit_matches_tag_filters(habit)
            element.set_visibility(visible)
            if visible:
                visible_groups.add(tag)

        for tag, element in group_elements:
            element.set_visibility(tag in visible_groups)

    @ui.refreshable
    def tag_filters_ui() -> None:
        if settings.ENABLE_TAG_FILTERS:
            tag_filter_component(active_habits, refresh=apply_tag_filters)

    @ui.refreshable
    def header_actions_ui() -> None:
        menu_icon_button(
            "sym_o_history",
            click=lambda: ui.navigate.to(f"{get_root_path()}/history"),
            tooltip="History",
        )

        if not settings.ENABLE_TAG_FILTERS or not get_all_tags(active_habits):
            return

        icon = "sym_o_filter_alt" if TagManager.is_visible() else "sym_o_filter_alt_off"
        tooltip = "Hide category tags" if TagManager.is_visible() else "Show category tags"
        menu_icon_button(icon, click=toggle_tag_filters, tooltip=tooltip)

    def toggle_tag_filters() -> None:
        TagManager.toggle_visible()
        header_actions_ui.refresh()
        tag_filters_ui.refresh()

    with layout(
        habit_list=habits,
        header_actions=header_actions_ui,
        content_width=index_content_width(days),
    ):
        tag_filters_ui()

        if not active_habits:
            ui.label("List is empty.").classes("mx-auto w-80")
            return
        habit_list_ui(days, active_habits, sync_filter_state)

    # placeholder to preload js cache (daily notes)
    textarea.Textarea("").classes("hidden").props('aria-hidden="true"')
    ui.input("").classes("hidden").props('aria-hidden="true"')
