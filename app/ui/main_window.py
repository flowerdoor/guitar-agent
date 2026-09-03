from __future__ import annotations

import html
from pathlib import Path

from PySide6.QtCore import QEvent, QThread, QTimer, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStyle,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.core.agent import GuitarAgent, INTERRUPTED_REPLY_SUFFIX
from app.core.course_service import CourseService
from app.core.models import AgentResponse, DashboardState
from app.data.repository import DatabaseError, Repository
from app.ui.chat_worker import ChatWorker
from app.ui.progress_dialog import CourseProgressDialog
from app.ui.settings_dialog import StudentSettingsDialog


APP_STYLESHEET = """
QMainWindow, QWidget {
    background: #f5f6f4;
    color: #202521;
    font-family: "Microsoft YaHei UI", "Segoe UI";
    font-size: 14px;
}
QFrame#Header {
    background: #ffffff;
    border-bottom: 1px solid #dfe4df;
}
QFrame#ChatPanel, QFrame#PracticePanel {
    background: #ffffff;
    border: 1px solid #dfe4df;
    border-radius: 6px;
}
QLabel#AppTitle {
    color: #18382c;
    font-size: 22px;
    font-weight: 700;
}
QLabel#PanelTitle, QLabel#LessonTitle, QLabel#DialogTitle {
    color: #202521;
    font-size: 17px;
    font-weight: 700;
}
QLabel#SectionTitle {
    color: #526058;
    font-size: 12px;
    font-weight: 700;
}
QLabel#MutedText {
    color: #707b74;
}
QLabel#ApiReady {
    color: #176b4d;
    background: #e6f3ec;
    padding: 5px 10px;
    border-radius: 4px;
}
QLabel#ApiMissing {
    color: #9b4a2f;
    background: #faece5;
    padding: 5px 10px;
    border-radius: 4px;
}
QTextBrowser#ChatHistory {
    background: #fbfcfb;
    border: none;
    padding: 8px;
}
QPlainTextEdit, QLineEdit, QSpinBox {
    background: #ffffff;
    border: 1px solid #cbd2cc;
    border-radius: 5px;
    padding: 8px;
    selection-background-color: #2d7358;
}
QPlainTextEdit:focus, QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #2d7358;
}
QPushButton {
    min-height: 34px;
    background: #eef1ee;
    border: 1px solid #cbd2cc;
    border-radius: 5px;
    padding: 0 14px;
}
QPushButton:hover {
    background: #e4e9e5;
}
QPushButton:pressed {
    background: #d9e0db;
}
QPushButton:disabled {
    color: #9da49f;
    background: #f0f1f0;
}
QPushButton#PrimaryButton {
    color: #ffffff;
    background: #24684f;
    border: 1px solid #24684f;
    font-weight: 600;
}
QPushButton#PrimaryButton:hover {
    background: #1e5b45;
}
QProgressBar {
    height: 8px;
    border: none;
    background: #e7ebe7;
    border-radius: 4px;
    text-align: center;
}
QProgressBar::chunk {
    background: #d08a4b;
    border-radius: 4px;
}
QListWidget {
    background: #fbfcfb;
    border: 1px solid #e2e6e2;
    border-radius: 5px;
    outline: none;
}
QListWidget::item {
    border-bottom: 1px solid #edf0ed;
    padding: 9px;
}
QScrollArea {
    border: none;
    background: transparent;
}
QSplitter::handle {
    background: transparent;
    width: 8px;
}
QStatusBar {
    background: #ffffff;
    border-top: 1px solid #dfe4df;
    color: #667169;
}
"""


class MainWindow(QMainWindow):
    def __init__(
        self,
        agent: GuitarAgent,
        course_service: CourseService,
        repository: Repository,
        *,
        api_configured: bool,
        config_path: Path,
    ):
        super().__init__()
        self.agent = agent
        self.course_service = course_service
        self.repository = repository
        self.api_configured = api_configured
        self.config_path = config_path
        self.dashboard = self.course_service.get_dashboard()
        self._chat_items: list[tuple[str, str, bool]] = []
        self._chat_thread: QThread | None = None
        self._chat_worker: ChatWorker | None = None
        self._stream_reply_index: int | None = None
        self._stream_buffer = ""
        self._stream_render_timer = QTimer(self)
        self._stream_render_timer.setSingleShot(True)
        self._stream_render_timer.setInterval(35)
        self._stream_render_timer.timeout.connect(self._render_chat)

        self.setWindowTitle("弦上教练 - 吉他初学者智能体")
        self.setMinimumSize(980, 680)
        self.resize(1180, 780)
        self.setStyleSheet(APP_STYLESHEET)

        self._build_ui()
        self._load_messages()
        self._refresh_dashboard(self.dashboard)

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("Header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 14, 24, 14)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title = QLabel("弦上教练")
        title.setObjectName("AppTitle")
        subtitle = QLabel("你的本地吉他入门学习助手")
        subtitle.setObjectName("MutedText")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.api_status = QLabel(
            "DeepSeek 已配置" if self.api_configured else "DeepSeek 待配置"
        )
        self.api_status.setObjectName("ApiReady" if self.api_configured else "ApiMissing")
        settings_button = QPushButton("学习设置")
        settings_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        )
        settings_button.clicked.connect(self._open_settings)

        header_layout.addLayout(title_box)
        header_layout.addStretch()
        header_layout.addWidget(self.api_status)
        header_layout.addSpacing(8)
        header_layout.addWidget(settings_button)
        root_layout.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(10)
        splitter.addWidget(self._build_chat_panel())
        splitter.addWidget(self._build_practice_panel())
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 4)
        splitter.setSizes([720, 420])

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.addWidget(splitter)
        root_layout.addWidget(content, 1)

        self.setCentralWidget(root)
        self.statusBar().showMessage("课程与练习记录保存在本机")

    def _build_chat_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("ChatPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        heading = QLabel("和教练聊聊")
        heading.setObjectName("PanelTitle")
        helper = QLabel("可以询问姿势、和弦、节拍或今天该练什么。")
        helper.setObjectName("MutedText")
        layout.addWidget(heading)
        layout.addWidget(helper)

        self.chat_history = QTextBrowser()
        self.chat_history.setObjectName("ChatHistory")
        self.chat_history.setOpenExternalLinks(False)
        layout.addWidget(self.chat_history, 1)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        self.message_input = QPlainTextEdit()
        self.message_input.setPlaceholderText("输入问题，例如：今天应该先练什么？")
        self.message_input.setFixedHeight(74)
        self.message_input.installEventFilter(self)
        self.send_button = QPushButton("发送")
        self.send_button.setObjectName("PrimaryButton")
        self.send_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward)
        )
        self.send_button.setFixedSize(96, 42)
        self.send_button.setToolTip("发送消息（Ctrl+Enter）")
        self.send_button.clicked.connect(self._send_message)
        input_row.addWidget(self.message_input, 1)
        input_row.addWidget(self.send_button, 0, Qt.AlignmentFlag.AlignBottom)
        layout.addLayout(input_row)
        return panel

    def _build_practice_panel(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        panel = QFrame()
        panel.setObjectName("PracticePanel")
        panel.setMinimumWidth(340)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(12)

        heading_row = QHBoxLayout()
        heading = QLabel("今日练习")
        heading.setObjectName("PanelTitle")
        self.progress_text = QLabel()
        self.progress_text.setObjectName("MutedText")
        self.switch_progress_button = QPushButton("切换")
        self.switch_progress_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload)
        )
        self.switch_progress_button.setToolTip("切换或回退课程进度")
        self.switch_progress_button.clicked.connect(self._open_progress_dialog)
        heading_row.addWidget(heading)
        heading_row.addStretch()
        heading_row.addWidget(self.progress_text)
        heading_row.addWidget(self.switch_progress_button)
        layout.addLayout(heading_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        self.lesson_title = QLabel()
        self.lesson_title.setObjectName("LessonTitle")
        self.lesson_title.setWordWrap(True)
        self.lesson_goal = QLabel()
        self.lesson_goal.setWordWrap(True)
        self.lesson_goal.setObjectName("MutedText")
        layout.addWidget(self.lesson_title)
        layout.addWidget(self.lesson_goal)

        steps_label = QLabel("练习步骤")
        steps_label.setObjectName("SectionTitle")
        self.lesson_steps = QLabel()
        self.lesson_steps.setWordWrap(True)
        self.lesson_steps.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(steps_label)
        layout.addWidget(self.lesson_steps)

        criteria_label = QLabel("完成标准")
        criteria_label.setObjectName("SectionTitle")
        self.lesson_criteria = QLabel()
        self.lesson_criteria.setWordWrap(True)
        layout.addWidget(criteria_label)
        layout.addWidget(self.lesson_criteria)

        record_label = QLabel("记录本次练习")
        record_label.setObjectName("SectionTitle")
        layout.addWidget(record_label)

        duration_row = QHBoxLayout()
        duration_row.addWidget(QLabel("实际时长"))
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 300)
        self.duration_input.setSuffix(" 分钟")
        duration_row.addStretch()
        duration_row.addWidget(self.duration_input)
        layout.addLayout(duration_row)

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("备注：哪里顺利，哪里还不熟（可选）")
        self.complete_button = QPushButton("完成本次练习")
        self.complete_button.setObjectName("PrimaryButton")
        self.complete_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        )
        self.complete_button.clicked.connect(self._complete_lesson)
        layout.addWidget(self.notes_input)
        layout.addWidget(self.complete_button)

        history_label = QLabel("最近记录")
        history_label.setObjectName("SectionTitle")
        layout.addWidget(history_label)
        self.practice_history = QListWidget()
        self.practice_history.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.practice_history.setMinimumHeight(150)
        self.practice_history.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.practice_history, 1)

        scroll.setWidget(panel)
        return scroll

    def eventFilter(self, watched, event) -> bool:
        if watched is self.message_input and event.type() == QEvent.Type.KeyPress:
            key_event = event
            if isinstance(key_event, QKeyEvent):
                if (
                    key_event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter}
                    and key_event.modifiers() & Qt.KeyboardModifier.ControlModifier
                ):
                    self._send_message()
                    return True
        return super().eventFilter(watched, event)

    def _load_messages(self) -> None:
        messages = self.repository.list_messages(self.dashboard.student.id, limit=50)
        if messages:
            self._chat_items = [(item.role, item.content, False) for item in messages]
        else:
            self._chat_items = [
                (
                    "assistant",
                    "你好，我是你的吉他入门教练。右侧已经准备好第一节练习。你可以先告诉我：你使用的是民谣吉他、古典吉他还是电吉他？",
                    False,
                )
            ]
        self._render_chat()

    def _render_chat(self) -> None:
        parts = [
            "<html><body style='font-family:Microsoft YaHei UI,Segoe UI; color:#202521;'>"
        ]
        for role, content, is_error in self._chat_items:
            safe_content = html.escape(content).replace("\n", "<br>")
            if role == "user":
                label = "你"
                align = "right"
                background = "#e4f0ea"
                border = "#c9ded2"
            else:
                label = "教练"
                align = "left"
                background = "#faece5" if is_error else "#f1f3f1"
                border = "#edcdbd" if is_error else "#dfe4df"
            parts.append(
                f"<div align='{align}' style='margin:10px 4px;'>"
                f"<div style='color:#707b74;font-size:12px;margin-bottom:4px;'>{label}</div>"
                f"<div style='background:{background};border:1px solid {border};"
                "padding:10px 12px;line-height:1.55;'>"
                f"{safe_content}</div></div>"
            )
        parts.append("</body></html>")
        self.chat_history.setHtml("".join(parts))
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _append_chat(self, role: str, content: str, is_error: bool = False) -> None:
        self._chat_items.append((role, content, is_error))
        self._render_chat()

    def _send_message(self) -> None:
        if self._chat_thread is not None:
            return
        message = self.message_input.toPlainText().strip()
        if not message:
            self.statusBar().showMessage("请先输入问题", 3000)
            return

        self.message_input.clear()
        self._append_chat("user", message)
        self._stream_reply_index = None
        self._stream_buffer = ""
        self._set_chat_busy(True)

        thread = QThread(self)
        worker = ChatWorker(self.agent, message, self.dashboard.student.id)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.chunk_received.connect(self._on_chat_chunk)
        worker.succeeded.connect(self._on_chat_success)
        worker.failed.connect(self._on_chat_error)
        worker.completed.connect(thread.quit)
        worker.completed.connect(worker.deleteLater)
        thread.finished.connect(self._on_chat_finished)
        self._chat_thread = thread
        self._chat_worker = worker
        thread.start()

    def _set_chat_busy(self, busy: bool) -> None:
        self.send_button.setDisabled(busy)
        self.message_input.setDisabled(busy)
        self.switch_progress_button.setDisabled(busy)
        self.send_button.setText("思考中" if busy else "发送")
        if busy:
            self.statusBar().showMessage("正在连接 DeepSeek…")

    def _on_chat_success(self, response: AgentResponse) -> None:
        if self._stream_reply_index is None:
            self._append_chat("assistant", response.reply)
        else:
            self._chat_items[self._stream_reply_index] = (
                "assistant",
                response.reply,
                False,
            )
            self._stream_render_timer.stop()
            self._render_chat()
        self.statusBar().showMessage(response.progress_note or "回复完成", 5000)

    def _on_chat_chunk(self, chunk: str) -> None:
        self._stream_buffer += chunk
        if self._stream_reply_index is None:
            self._stream_reply_index = len(self._chat_items)
            self._chat_items.append(("assistant", self._stream_buffer, False))
        else:
            self._chat_items[self._stream_reply_index] = (
                "assistant",
                self._stream_buffer,
                False,
            )
        self.send_button.setText("回复中")
        self.statusBar().showMessage("正在接收 DeepSeek 回复…")
        if not self._stream_render_timer.isActive():
            self._stream_render_timer.start()

    def _on_chat_error(self, message: str) -> None:
        if self._stream_reply_index is not None:
            self._stream_render_timer.stop()
            partial = f"{self._stream_buffer.rstrip()}{INTERRUPTED_REPLY_SUFFIX}"
            self._chat_items[self._stream_reply_index] = (
                "assistant",
                partial,
                False,
            )
        self._append_chat("assistant", f"暂时无法回复：{message}", True)
        self.statusBar().showMessage("聊天请求失败，本地课程仍可正常使用", 6000)

    def _on_chat_finished(self) -> None:
        if self._chat_thread is not None:
            self._chat_thread.deleteLater()
        self._chat_thread = None
        self._chat_worker = None
        self._stream_reply_index = None
        self._stream_buffer = ""
        self._set_chat_busy(False)
        self.message_input.setFocus()

    def _refresh_dashboard(self, dashboard: DashboardState) -> None:
        self.dashboard = dashboard
        self.progress_bar.setRange(0, dashboard.total_lessons)
        self.progress_bar.setValue(dashboard.completed_count)
        self.progress_text.setText(
            f"{dashboard.completed_count}/{dashboard.total_lessons} 节"
        )

        lesson = dashboard.current_lesson
        if lesson is None:
            self.lesson_title.setText("基础课程已完成")
            self.lesson_goal.setText("可以在聊天区告诉教练你的薄弱点，继续安排复习或进阶练习。")
            self.lesson_steps.setText("复习练习记录，选择最需要巩固的内容。")
            self.lesson_criteria.setText("能稳定、放松地完成基础和弦与节拍练习。")
            self.duration_input.setValue(dashboard.student.practice_minutes)
            self.complete_button.setDisabled(True)
            self.notes_input.setDisabled(True)
        else:
            self.lesson_title.setText(lesson.title)
            self.lesson_goal.setText(lesson.goal)
            self.lesson_steps.setText(_numbered_text(lesson.practice_steps))
            self.lesson_criteria.setText(_bullet_text(lesson.success_criteria))
            self.duration_input.setValue(lesson.duration_minutes)
            self.complete_button.setDisabled(False)
            self.notes_input.setDisabled(False)

        self.practice_history.clear()
        if not dashboard.recent_practice:
            item = QListWidgetItem("完成一次练习后，记录会显示在这里。")
            item.setForeground(Qt.GlobalColor.gray)
            self.practice_history.addItem(item)
        else:
            for record in dashboard.recent_practice:
                timestamp = record.created_at.strftime("%m-%d %H:%M")
                text = f"{record.lesson_title}  ·  {record.duration_minutes} 分钟\n{timestamp}"
                if record.notes:
                    text += f"  ·  {record.notes}"
                item = QListWidgetItem(text)
                item.setToolTip(record.notes or record.lesson_title)
                self.practice_history.addItem(item)

    def _complete_lesson(self) -> None:
        lesson = self.dashboard.current_lesson
        if lesson is None:
            return
        try:
            next_dashboard = self.course_service.complete_current_lesson(
                self.dashboard.student.id,
                self.duration_input.value(),
                self.notes_input.text(),
            )
            next_lesson = next_dashboard.current_lesson
            if next_lesson is None:
                message = f"已记录“{lesson.title}”。恭喜你完成全部基础课程！"
            else:
                message = (
                    f"已记录“{lesson.title}”。下一节是“{next_lesson.title}”，"
                    f"建议练习 {next_lesson.duration_minutes} 分钟。"
                )
            self.repository.add_message(self.dashboard.student.id, "assistant", message)
            self._append_chat("assistant", message)
            self.notes_input.clear()
            self._refresh_dashboard(next_dashboard)
            self.statusBar().showMessage("练习记录已保存到本机", 5000)
        except (DatabaseError, ValueError) as exc:
            QMessageBox.warning(self, "无法保存练习", str(exc))

    def _open_progress_dialog(self) -> None:
        current = self.dashboard.current_lesson
        dialog = CourseProgressDialog(
            self.course_service.lessons,
            current.id if current else None,
            self,
        )
        if dialog.exec() != CourseProgressDialog.DialogCode.Accepted:
            return

        lesson_id = dialog.selected_lesson_id()
        if lesson_id == (current.id if current else None):
            self.statusBar().showMessage("课程进度没有变化", 3000)
            return

        try:
            dashboard = self.course_service.set_current_lesson(
                self.dashboard.student.id,
                lesson_id,
            )
            next_lesson = dashboard.current_lesson
            if next_lesson is None:
                message = "课程进度已切换为：基础课程全部完成。练习历史已保留。"
            else:
                message = (
                    f"课程进度已切换到“{next_lesson.title}”。"
                    "这节课及之后的课程可重新完成，原练习历史仍然保留。"
                )
            self.repository.add_message(
                self.dashboard.student.id,
                "assistant",
                message,
            )
            self._append_chat("assistant", message)
            self.notes_input.clear()
            self._refresh_dashboard(dashboard)
            self.statusBar().showMessage("课程进度已更新", 5000)
        except (DatabaseError, ValueError) as exc:
            QMessageBox.warning(self, "无法切换进度", str(exc))

    def _open_settings(self) -> None:
        dialog = StudentSettingsDialog(self.dashboard.student, self)
        if dialog.exec() != StudentSettingsDialog.DialogCode.Accepted:
            return
        name, goal, minutes = dialog.values()
        try:
            dashboard = self.course_service.update_student(
                self.dashboard.student.id,
                name=name,
                goal=goal,
                practice_minutes=minutes,
            )
            self._refresh_dashboard(dashboard)
            self.statusBar().showMessage("学习设置已保存", 4000)
        except (DatabaseError, ValueError) as exc:
            QMessageBox.warning(self, "无法保存设置", str(exc))

    def closeEvent(self, event) -> None:
        if self._chat_thread is not None and self._chat_thread.isRunning():
            QMessageBox.information(
                self,
                "请稍候",
                "DeepSeek 正在回复。为避免丢失本次对话，请等待请求完成后再退出。",
            )
            event.ignore()
            return
        event.accept()


def _numbered_text(values: tuple[str, ...]) -> str:
    return "\n".join(f"{index}. {value}" for index, value in enumerate(values, 1))


def _bullet_text(values: tuple[str, ...]) -> str:
    return "\n".join(f"• {value}" for value in values)
