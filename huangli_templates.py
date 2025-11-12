"""黄历结论渲染模板与格式化工具。

该模块提供固定的黄历模板文本，以及用于格式化宜忌信息的工具函数。
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import List, Tuple

YELLOW_GODS = {"青龙", "明堂", "金贵", "天德", "玉堂", "司命"}
"""黄道吉神集合。"""

BLACK_GODS = {"朱雀", "白虎", "天牢", "玄武", "勾陈", "天刑"}
"""黑道凶神集合。"""

TEMPLATE_DICT: dict[str, str] = {
    "特凶": (
        "今日总评｜{label}｜特凶\n"
        "今天天地气机强烈相冲、波动剧烈，外在秩序不稳，重大事项一律不建议推进；常规事务也应暂停或改期，仅保留信息收集、沟通对齐等准备动作。\n"
        "{ji}\n"
        "{yi}\n"
        "结论：停一停，把时间让给复盘、校验与备选方案。"
    ),
    "大凶": (
        "今日总评｜{label}｜大凶\n"
        "今天天地能量逆风明显，适合整顿秩序、止损与充电：把时间投向文案打磨、合同复核、资产盘点、健康与家务整理，明天你会更快。\n"
        "{ji}\n"
        "{yi}\n"
        "建议：设定“三件小事清单”，完成它们，今天就是赢。"
    ),
    "凶": (
        "今日总评｜{label}｜偏弱\n"
        "今天天地能量偏弱但可控，更适合打磨与修正：聚焦复盘、校对、流程优化与小范围验证，为后续冲刺打地基。\n"
        "{ji}\n"
        "{yi}\n"
        "建议：用“小步快跑 + 及时复盘”拿几个小胜，稳定节奏、积累信心。"
    ),
    "平": (
        "今日总评｜{label}｜中性\n"
        "今天天地能量趋于中性、行进状态平稳，日常常规事务按计划推进即可；遇到重大事项，无论好事或硬决策，建议再比对更佳日期，或先做准备性动作。\n"
        "{ji}\n"
        "{yi}涉及长期风险或大规划的决策，再观望。"
    ),
    "吉": (
        "今日总评｜{label}｜良好\n"
        "今天天地能量顺畅度较好、配合度上行，整体利于推进关键节点，但仍需注意节奏与边界。\n"
        "{ji}\n"
        "{yi}体量较大或影响深远的动作，卡在当日相对吉时并完成文本复核。\n"
        "结论：把握窗口，该推进的推进，但保持留痕与风控。"
    ),
    "大吉": (
        "今日总评｜{label}｜极佳\n"
        "今天天地气机顺和而有力、助推明显，是启动/定案/发布/签署的理想窗口；协同顺、效率高。\n"
        "{ji}\n"
        "{yi}\n"
        "结论：大胆而有序地推进，先做高收益事项，并配足复核与兜底。"
    ),
}
"""六档固定模板文本。"""


def _normalize(items: Iterable[str] | None) -> List[str]:
    """去重保序并过滤空串。

    参数
    ----
    items:
        原始字符串序列，可以为 ``None``。

    返回
    ----
    list[str]
        处理后的列表。
    """

    if not items:
        return []

    seen: set[str] = set()
    normalized: List[str] = []
    for item in items:
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


def finalize_yiji(yi: Iterable[str] | None, ji: Iterable[str] | None) -> Tuple[List[str], List[str]]:
    """在冲突消解后返回最终的宜忌列表。"""

    normalized_ji = _normalize(ji)
    normalized_yi = _normalize(yi)

    taboo_set = set(normalized_ji)
    final_yi = [item for item in normalized_yi if item not in taboo_set]

    return final_yi, normalized_ji


GRADE_SENTENCE_PATTERNS: dict[str, dict[str, tuple[str, str]]] = {
    "特凶": {
        "ji": (
            "{items}等事项建议绝对不要触碰；",
            "暂无需要特别强调的忌项，但仍建议暂停一切关键推进；",
        ),
        "yi": (
            "{items}等宜项今天也不落地执行，仅作备案与预案推演。",
            "今日无宜项，聚焦复盘、校验与备选方案。",
        ),
    },
    "大凶": {
        "ji": (
            "{items}等事项今天不建议触碰；",
            "暂无明确忌项，但整体以整顿、止损与充电为主；",
        ),
        "yi": (
            "{items}保留在准备层面（对齐方案、确认需求、下单但不落地）。",
            "暂无宜项，专注于整顿秩序、盘点资产与补课。",
        ),
    },
    "凶": {
        "ji": (
            "{items}等事项今天先不推进；",
            "暂无特别忌项，但建议先聚焦复盘、校对与修正；",
        ),
        "yi": (
            "{items}等低风险、可回退的小决策与“补课型”任务优先安排；",
            "暂无宜项，聚焦小步快跑与及时复盘。",
        ),
    },
    "平": {
        "ji": (
            "{items}等事项今日不建议推进；",
            "暂无需特别规避的事项，可按计划推进常规事务；",
        ),
        "yi": (
            "{items}等低风险的小决策正常推进；",
            "暂无明确宜项，可按计划推进常规事务；",
        ),
    },
    "吉": {
        "ji": (
            "{items}等事项能避则避；",
            "暂无需要规避的事项，但仍注意节奏与边界；",
        ),
        "yi": (
            "{items}等事项优先处理签署/交付/安置/修缮/对外发布等可控动作；",
            "暂无特别宜项，但可推进关键节点，保持节奏与留痕；",
        ),
    },
    "大吉": {
        "ji": (
            "{items}如有冲突，先择时或另日；",
            "暂无明显忌项，可因势利导；",
        ),
        "yi": (
            "{items}等事项可作为当日主线优先落地，集中完成关键里程碑；",
            "暂无宜项，但整体利于推进关键里程碑，可综合评估后执行；",
        ),
    },
}
"""不同档位下宜忌语句的模板。"""


def _build_sentence(
    *,
    items: list[str],
    positive_pattern: str,
    empty_pattern: str,
) -> str:
    """根据项目列表生成完整语句。"""

    if items:
        joined = "、".join(items)
        return positive_pattern.format(items=joined)
    return empty_pattern


def format_text(
    template: str,
    *,
    label: str,
    yi: Iterable[str] | None,
    ji: Iterable[str] | None,
    grade: str,
) -> str:
    """使用模板渲染宜忌信息。

    冲突消解遵循“忌项优先”：将宜项中与忌项同名的条目剔除。

    参数
    ----
    template:
        模板字符串，包含 ``{label}``、``{yi}``、``{ji}`` 等占位符。
    label:
        标题标签文本。
    yi:
        宜项序列，允许 ``None``。
    ji:
        忌项序列，允许 ``None``。
    grade:
        当日分档，用于匹配不同的宜忌语句模板。

    返回
    ----
    str
        填充占位符后的最终文本。
    """

    final_yi, final_ji = finalize_yiji(yi, ji)

    has_global_yi = "诸事不宜" in final_yi
    has_global_ji = "诸事不宜" in final_ji

    if has_global_yi:
        final_yi = [item for item in final_yi if item != "诸事不宜"]
    if has_global_ji:
        final_ji = [item for item in final_ji if item != "诸事不宜"]

    patterns = GRADE_SENTENCE_PATTERNS.get(grade, GRADE_SENTENCE_PATTERNS["平"])

    ji_text = _build_sentence(
        items=final_ji,
        positive_pattern=patterns["ji"][0],
        empty_pattern=patterns["ji"][1],
    )
    yi_text = _build_sentence(
        items=final_yi,
        positive_pattern=patterns["yi"][0],
        empty_pattern=patterns["yi"][1],
    )

    if has_global_ji:
        ji_text = "避免重大决策。"

    if has_global_yi:
        yi_text = "没有特别适合的事项，保持日常活动即可。"

    return template.format(label=label, yi=yi_text, ji=ji_text)


__all__ = [
    "YELLOW_GODS",
    "BLACK_GODS",
    "TEMPLATE_DICT",
    "format_text",
    "_normalize",
    "finalize_yiji",
    "GRADE_SENTENCE_PATTERNS",
]

