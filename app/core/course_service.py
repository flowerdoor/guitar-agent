from __future__ import annotations

from app.core.models import DashboardState, Lesson, Student
from app.data.repository import Repository


class CourseService:
    def __init__(self, repository: Repository, lessons: tuple[Lesson, ...]):
        self.repository = repository
        self.lessons = lessons

    def get_dashboard(self, student_id: int | None = None) -> DashboardState:
        student = self.repository.get_or_create_default_student()
        if student_id is not None and student.id != student_id:
            raise ValueError("找不到指定学生。")
        completed = self.repository.completed_lesson_ids(student.id)
        current = next((lesson for lesson in self.lessons if lesson.id not in completed), None)
        history = self.repository.list_practice_records(student.id, limit=12)
        return DashboardState(
            student=student,
            current_lesson=current,
            completed_count=len(completed.intersection({lesson.id for lesson in self.lessons})),
            total_lessons=len(self.lessons),
            recent_practice=history,
        )

    def complete_current_lesson(
        self, student_id: int, duration_minutes: int, notes: str = ""
    ) -> DashboardState:
        dashboard = self.get_dashboard(student_id)
        lesson = dashboard.current_lesson
        if lesson is None:
            raise ValueError("基础课程已经全部完成。")
        self.repository.complete_lesson(
            student_id,
            lesson_id=lesson.id,
            lesson_title=lesson.title,
            task=lesson.practice_task,
            duration_minutes=duration_minutes,
            notes=notes,
        )
        self.repository.set_current_stage(student_id, lesson.order + 1)
        return self.get_dashboard(student_id)

    def set_current_lesson(
        self, student_id: int, lesson_id: str | None
    ) -> DashboardState:
        self.get_dashboard(student_id)
        if lesson_id is None:
            completed_ids = [lesson.id for lesson in self.lessons]
            current_stage = len(self.lessons) + 1
        else:
            selected = next(
                (lesson for lesson in self.lessons if lesson.id == lesson_id),
                None,
            )
            if selected is None:
                raise ValueError("找不到要切换的课程。")
            completed_ids = [
                lesson.id for lesson in self.lessons if lesson.order < selected.order
            ]
            current_stage = selected.order

        self.repository.replace_lesson_progress(
            student_id,
            completed_ids,
            current_stage,
        )
        return self.get_dashboard(student_id)

    def update_student(
        self, student_id: int, *, name: str, goal: str, practice_minutes: int
    ) -> DashboardState:
        self.repository.update_student(
            student_id,
            name=name,
            goal=goal,
            practice_minutes=practice_minutes,
        )
        return self.get_dashboard(student_id)
