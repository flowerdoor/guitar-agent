from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.models import Lesson


class LessonLoadError(RuntimeError):
    """Raised when bundled lesson content is unavailable or malformed."""


def load_lessons(path: Path) -> tuple[Lesson, ...]:
    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LessonLoadError(f"无法读取课程文件：{exc}") from exc

    if not isinstance(raw, list) or not raw:
        raise LessonLoadError("课程文件必须包含至少一节课程。")

    lessons: list[Lesson] = []
    try:
        for item in raw:
            lessons.append(
                Lesson(
                    id=str(item["id"]),
                    order=int(item["order"]),
                    title=str(item["title"]),
                    goal=str(item["goal"]),
                    duration_minutes=int(item["duration_minutes"]),
                    explanation=str(item["explanation"]),
                    practice_steps=tuple(str(value) for value in item["practice_steps"]),
                    success_criteria=tuple(str(value) for value in item["success_criteria"]),
                    common_mistakes=tuple(str(value) for value in item["common_mistakes"]),
                )
            )
    except (KeyError, TypeError, ValueError) as exc:
        raise LessonLoadError(f"课程数据格式错误：{exc}") from exc

    ids = [lesson.id for lesson in lessons]
    orders = [lesson.order for lesson in lessons]
    if len(ids) != len(set(ids)) or len(orders) != len(set(orders)):
        raise LessonLoadError("课程 id 和 order 必须唯一。")

    return tuple(sorted(lessons, key=lambda lesson: lesson.order))

