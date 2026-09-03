from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Student:
    id: int
    name: str
    level: str
    goal: str
    practice_minutes: int
    current_stage: int


@dataclass(frozen=True)
class Message:
    role: str
    content: str
    created_at: datetime


@dataclass(frozen=True)
class Lesson:
    id: str
    order: int
    title: str
    goal: str
    duration_minutes: int
    explanation: str
    practice_steps: tuple[str, ...]
    success_criteria: tuple[str, ...]
    common_mistakes: tuple[str, ...]

    @property
    def practice_task(self) -> str:
        return "；".join(self.practice_steps)


@dataclass(frozen=True)
class PracticeRecord:
    lesson_id: str
    lesson_title: str
    duration_minutes: int
    result: str
    notes: str
    created_at: datetime


@dataclass(frozen=True)
class AgentResponse:
    reply: str
    suggested_lesson_id: str | None = None
    practice_task: str | None = None
    progress_note: str | None = None


@dataclass(frozen=True)
class DashboardState:
    student: Student
    current_lesson: Lesson | None
    completed_count: int
    total_lessons: int
    recent_practice: tuple[PracticeRecord, ...] = field(default_factory=tuple)

