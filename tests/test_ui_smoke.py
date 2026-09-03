from pathlib import Path

from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox

from app.core.agent import GuitarAgent
from app.core.course_service import CourseService
from app.core.lessons import load_lessons
from app.core.models import AgentResponse
from app.data.repository import Repository
from app.ui.main_window import MainWindow
from app.ui.progress_dialog import CourseProgressDialog


LESSONS_FILE = Path(__file__).resolve().parents[1] / "lessons" / "lessons.json"


class FakeChatClient:
    def chat(self, messages):
        return "测试回复"


def test_main_window_can_render_dashboard(tmp_path):
    application = QApplication.instance() or QApplication([])
    repository = Repository(tmp_path / "guitar.db")
    repository.initialize()
    course_service = CourseService(repository, load_lessons(LESSONS_FILE))
    agent = GuitarAgent(repository, course_service, FakeChatClient())

    window = MainWindow(
        agent,
        course_service,
        repository,
        api_configured=False,
        config_path=tmp_path / "config.local.json",
    )
    application.processEvents()

    assert window.lesson_title.text() == "认识吉他与正确持琴"
    assert window.progress_text.text() == "0/5 节"
    assert window.switch_progress_button.isEnabled()
    assert "你好" in window.chat_history.toPlainText()

    window.close()


def test_stream_chunks_update_one_reply_instead_of_adding_duplicates(tmp_path):
    application = QApplication.instance() or QApplication([])
    repository = Repository(tmp_path / "guitar.db")
    repository.initialize()
    course_service = CourseService(repository, load_lessons(LESSONS_FILE))
    agent = GuitarAgent(repository, course_service, FakeChatClient())
    window = MainWindow(
        agent,
        course_service,
        repository,
        api_configured=True,
        config_path=tmp_path / "config.local.json",
    )
    initial_count = len(window._chat_items)

    window._on_chat_chunk("第一段")
    window._on_chat_chunk("第二段")
    window._on_chat_success(AgentResponse(reply="第一段第二段"))
    application.processEvents()

    assert len(window._chat_items) == initial_count + 1
    assert window._chat_items[-1] == ("assistant", "第一段第二段", False)
    assert window.chat_history.toPlainText().count("第一段第二段") == 1

    window.close()


def test_progress_dialog_apply_button_accepts_selected_lesson():
    application = QApplication.instance() or QApplication([])
    lessons = load_lessons(LESSONS_FILE)
    dialog = CourseProgressDialog(lessons, lessons[0].id)
    dialog.lesson_select.setCurrentIndex(2)
    dialog.show()
    application.processEvents()

    dialog.buttons.button(QDialogButtonBox.StandardButton.Ok).click()
    application.processEvents()

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.selected_lesson_id() == lessons[2].id
