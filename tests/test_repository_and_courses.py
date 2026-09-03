from pathlib import Path

from app.core.course_service import CourseService
from app.core.lessons import load_lessons
from app.data.repository import Repository


LESSONS_FILE = Path(__file__).resolve().parents[1] / "lessons" / "lessons.json"


def make_service(tmp_path):
    repository = Repository(tmp_path / "guitar.db")
    repository.initialize()
    lessons = load_lessons(LESSONS_FILE)
    return repository, CourseService(repository, lessons)


def test_default_student_and_course_are_created(tmp_path):
    repository, service = make_service(tmp_path)

    dashboard = service.get_dashboard()

    assert dashboard.student.level == "零基础"
    assert dashboard.current_lesson is not None
    assert dashboard.current_lesson.order == 1
    assert dashboard.completed_count == 0
    assert dashboard.total_lessons == 5
    assert repository.list_messages(dashboard.student.id) == ()


def test_completion_persists_after_repository_reopens(tmp_path):
    database_path = tmp_path / "guitar.db"
    repository = Repository(database_path)
    repository.initialize()
    lessons = load_lessons(LESSONS_FILE)
    service = CourseService(repository, lessons)
    student = service.get_dashboard().student

    after = service.complete_current_lesson(student.id, 18, "持琴已经比较放松")

    reopened = Repository(database_path)
    reopened.initialize()
    reopened_dashboard = CourseService(reopened, lessons).get_dashboard(student.id)
    assert after.current_lesson is not None
    assert after.current_lesson.order == 2
    assert reopened_dashboard.completed_count == 1
    assert reopened_dashboard.current_lesson.order == 2
    assert reopened_dashboard.recent_practice[0].duration_minutes == 18
    assert reopened_dashboard.recent_practice[0].notes == "持琴已经比较放松"


def test_profile_updates_are_persistent(tmp_path):
    repository, service = make_service(tmp_path)
    student = service.get_dashboard().student

    dashboard = service.update_student(
        student.id,
        name="小林",
        goal="学会弹唱",
        practice_minutes=30,
    )

    assert dashboard.student.name == "小林"
    assert dashboard.student.goal == "学会弹唱"
    assert dashboard.student.practice_minutes == 30


def test_chat_history_is_returned_in_chronological_order(tmp_path):
    repository, service = make_service(tmp_path)
    student_id = service.get_dashboard().student.id
    repository.add_message(student_id, "user", "第一条")
    repository.add_message(student_id, "assistant", "第二条")

    history = repository.list_messages(student_id)

    assert [item.content for item in history] == ["第一条", "第二条"]


def test_course_progress_can_roll_back_without_deleting_practice_history(tmp_path):
    repository, service = make_service(tmp_path)
    student_id = service.get_dashboard().student.id
    for _ in range(3):
        service.complete_current_lesson(student_id, 20, "历史记录")

    dashboard = service.set_current_lesson(student_id, "lesson-02-open-strings")

    assert dashboard.completed_count == 1
    assert dashboard.current_lesson is not None
    assert dashboard.current_lesson.id == "lesson-02-open-strings"
    assert dashboard.student.current_stage == 2
    assert len(dashboard.recent_practice) == 3


def test_course_progress_can_jump_forward(tmp_path):
    repository, service = make_service(tmp_path)
    student_id = service.get_dashboard().student.id

    dashboard = service.set_current_lesson(student_id, "lesson-04-chords")

    assert dashboard.completed_count == 3
    assert dashboard.current_lesson is not None
    assert dashboard.current_lesson.id == "lesson-04-chords"
    assert repository.completed_lesson_ids(student_id) == frozenset(
        {
            "lesson-01-posture",
            "lesson-02-open-strings",
            "lesson-03-rhythm",
        }
    )


def test_course_progress_can_be_set_to_all_complete_and_reopened(tmp_path):
    _, service = make_service(tmp_path)
    student_id = service.get_dashboard().student.id

    completed = service.set_current_lesson(student_id, None)
    reopened = service.set_current_lesson(student_id, "lesson-05-changes")

    assert completed.current_lesson is None
    assert completed.completed_count == completed.total_lessons
    assert completed.student.current_stage == completed.total_lessons + 1
    assert reopened.current_lesson is not None
    assert reopened.current_lesson.id == "lesson-05-changes"
    assert reopened.completed_count == 4


def test_unknown_course_progress_target_is_rejected(tmp_path):
    _, service = make_service(tmp_path)
    student_id = service.get_dashboard().student.id

    try:
        service.set_current_lesson(student_id, "missing-lesson")
    except ValueError as exc:
        assert "找不到" in str(exc)
    else:
        raise AssertionError("Unknown lesson should be rejected")
