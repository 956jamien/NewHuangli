"""黄历结论渲染层实现。"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Tuple

from cnlunar import Lunar

from huangli_templates import (
    BLACK_GODS,
    TEMPLATE_DICT,
    YELLOW_GODS,
    finalize_yiji,
    format_text,
)

__all__ = [
    "detect_hard_taboo",
    "pick_officer_yiji",
    "grade_day",
    "render_conclusion",
    "render_for_date",
    "render_structured",
    "DayConclusion",
]

SOLAR_TERMS_FOUR_ABSOLUTE = ("立春", "立夏", "立秋", "立冬")
SOLAR_TERMS_FOUR_SEPARATION = ("春分", "夏至", "秋分", "冬至")
YANGGONG_THIRTEEN = {
    (1, 13),
    (2, 11),
    (3, 9),
    (4, 7),
    (5, 5),
    (6, 2),
    (7, 1),
    (7, 29),
    (8, 27),
    (9, 25),
    (10, 23),
    (11, 21),
    (12, 19),
}


@dataclass(slots=True)
class DayConclusion:
    """结构化的日结论结果。"""

    date: datetime
    label: str
    grade: str
    yi: List[str]
    ji: List[str]
    text: str


def _prev_md(month: int, day: int) -> Tuple[int, int]:
    """返回给定月日的前一日月日元组。"""

    # 使用任意闰年以兼容 2 月 29 日，此处选 2000 年。
    dt = datetime(year=2000, month=month, day=day) - timedelta(days=1)
    return dt.month, dt.day


def detect_hard_taboo(almanac: Lunar) -> bool:
    """检测四绝、四离及杨公十三忌等硬禁忌。"""

    current_md = (almanac.date.month, almanac.date.day)

    if current_md in YANGGONG_THIRTEEN:
        return True

    solar_terms = getattr(almanac, "thisYearSolarTermsDic", {}) or {}

    for name in SOLAR_TERMS_FOUR_ABSOLUTE + SOLAR_TERMS_FOUR_SEPARATION:
        if name not in solar_terms:
            continue
        month, day = solar_terms[name]
        if _prev_md(month, day) == current_md:
            return True

    return False


def pick_officer_yiji(almanac: Lunar) -> Tuple[List[str], List[str]]:
    """获取当日宜忌信息。"""

    good_thing = getattr(almanac, "goodThing", None)
    bad_thing = getattr(almanac, "badThing", None)

    if (
        isinstance(good_thing, Iterable)
        and not isinstance(good_thing, (str, bytes))
        and isinstance(bad_thing, Iterable)
        and not isinstance(bad_thing, (str, bytes))
    ):
        return list(good_thing), list(bad_thing)

    try:
        from cnlunar.config import THING_CATEGORY_MAP, officerThings
    except Exception as exc:  # pragma: no cover - 环境错误
        raise RuntimeError(
            "无法导入 cnlunar.config.officerThings，请确保依赖完整可用。"
        ) from exc

    officer = getattr(almanac, "today12DayOfficer", None)
    if not officer:
        raise RuntimeError("Lunar 对象缺少 today12DayOfficer 信息。")

    try:
        yi_tuple, ji_tuple = officerThings[officer]
    except KeyError as exc:
        raise RuntimeError(f"未找到对应的 officerThings 项：{officer}") from exc

    def _map_categories(items: Iterable[str]) -> List[str]:
        mapped: List[str] = []
        seen: set[str] = set()
        for item in items:
            category = THING_CATEGORY_MAP.get(item)
            if not category:
                continue
            if category in seen:
                continue
            seen.add(category)
            mapped.append(category)
        return mapped

    return _map_categories(yi_tuple), _map_categories(ji_tuple)


def grade_day(almanac: Lunar, *, hard_taboo: bool) -> str:
    """按照规则计算当日等级。"""

    if hard_taboo:
        return "特凶"

    god = getattr(almanac, "today12DayGod", "") or ""
    level = _resolve_level(almanac)
    grade = BASE_GRADE_BY_LEVEL.get(level, "平")

    if god in BLACK_GODS:
        if grade == "大吉":
            grade = "吉"
        elif grade == "吉":
            grade = "平"
        elif grade == "平":
            grade = "凶"
        elif grade == "凶":
            grade = "大凶"
    elif god in YELLOW_GODS:
        if grade == "凶":
            grade = "平"
        elif grade == "平":
            grade = "吉"
        elif grade == "吉":
            grade = "大吉"

    return grade


def render_conclusion(almanac: Lunar, *, enhance_minor_taboo: bool = False) -> str:
    """渲染当日黄历总评文案。"""

    _ = enhance_minor_taboo  # 参数保留，当前未使用。

    officer = getattr(almanac, "today12DayOfficer", "") or ""
    god = getattr(almanac, "today12DayGod", "") or ""
    if officer and god:
        label = f"{officer}日·{god}"
    else:
        label = officer or god or "今日"

    yi_raw, ji_raw = pick_officer_yiji(almanac)
    final_yi, final_ji = finalize_yiji(yi_raw, ji_raw)

    grade = grade_day(almanac, hard_taboo=detect_hard_taboo(almanac))
    if "诸事不宜" in final_ji and grade in {"吉", "大吉"}:
        grade = "凶"

    template = TEMPLATE_DICT[grade]
    return format_text(template, label=label, yi=final_yi, ji=final_ji, grade=grade)


def render_for_date(dt: datetime) -> str:
    """构造 :class:`Lunar` 对象并渲染。"""

    almanac = Lunar(dt)
    body = render_conclusion(almanac)
    return f"{dt:%Y-%m-%d}\n{body}"


def render_structured(almanac: Lunar) -> DayConclusion:
    """返回结构化的日结论结果。"""

    officer = getattr(almanac, "today12DayOfficer", "") or ""
    god = getattr(almanac, "today12DayGod", "") or ""
    if officer and god:
        label = f"{officer}日·{god}"
    else:
        label = officer or god or "今日"

    yi_raw, ji_raw = pick_officer_yiji(almanac)
    final_yi, final_ji = finalize_yiji(yi_raw, ji_raw)

    grade = grade_day(almanac, hard_taboo=detect_hard_taboo(almanac))
    if "诸事不宜" in final_ji and grade in {"吉", "大吉"}:
        grade = "凶"

    template = TEMPLATE_DICT[grade]
    text = format_text(template, label=label, yi=final_yi, ji=final_ji, grade=grade)

    return DayConclusion(
        date=almanac.date,
        label=label,
        grade=grade,
        yi=final_yi,
        ji=final_ji,
        text=text,
    )

LEVEL_NAME_ALIAS = {
    "从宜不从忌": "上",
    "从宜亦从忌": "中",
    "从忌不从宜": "下",
    "诸事皆忌": "无",
}
"""thingLevelName 与评档规则之间的映射。"""

LEVEL_VALUE_ALIAS = {0: "上", 1: "中", 2: "下", 3: "无"}
"""数值 ``thingLevel`` 与评档规则之间的映射。"""

BASE_GRADE_BY_LEVEL = {
    "上": "大吉",
    "中": "吉",
    "下": "平",
    "无": "凶",
}
"""不同等级对应的初始档位。"""


def _resolve_level(almanac: Lunar) -> str:
    """归一化 ``thingLevel`` / ``thingLevelName`` 为规则所需的档位。"""

    level_name = getattr(almanac, "thingLevelName", "") or ""
    level_name = str(level_name).strip()
    if level_name in LEVEL_NAME_ALIAS:
        return LEVEL_NAME_ALIAS[level_name]

    level_value = getattr(almanac, "thingLevel", None)
    if level_value in LEVEL_VALUE_ALIAS:
        return LEVEL_VALUE_ALIAS[level_value]

    return "无"
