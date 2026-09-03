from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from app.core.models import Lesson


class CourseProgressDialog(QDialog):
    def __init__(
        self,
        lessons: tuple[Lesson, ...],
        current_lesson_id: str | None,
        parent=None,
    ):
        super().__init__(parent)
        self.lessons = lessons
        self.setWindowTitle("切换课程进度")
        self.setMinimumWidth(460)
        self.setModal(True)

        title = QLabel("选择当前课程")
        title.setObjectName("DialogTitle")

        self.lesson_select = QComboBox()
        for lesson in lessons:
            self.lesson_select.addItem(
                f"第 {lesson.order} 课  ·  {lesson.title}",
                lesson.id,
            )
        self.lesson_select.addItem("基础课程已全部完成", None)

        selected_index = len(lessons)
        if current_lesson_id is not None:
            for index, lesson in enumerate(lessons):
                if lesson.id == current_lesson_id:
                    selected_index = index
                    break
        self.lesson_select.setCurrentIndex(selected_index)

        self.effect_text = QLabel()
        self.effect_text.setObjectName("MutedText")
        self.effect_text.setWordWrap(True)
        self.lesson_select.currentIndexChanged.connect(self._update_effect_text)
        self._update_effect_text(selected_index)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("应用")
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)
        layout.addWidget(title)
        layout.addWidget(self.lesson_select)
        layout.addWidget(self.effect_text)
        layout.addSpacing(4)
        layout.addWidget(self.buttons)

    def selected_lesson_id(self) -> str | None:
        return self.lesson_select.currentData()

    def _update_effect_text(self, index: int) -> None:
        if index >= len(self.lessons):
            text = "所有基础课程将标记为已完成。已有练习历史不会删除。"
        else:
            lesson = self.lessons[index]
            text = (
                f"第 {lesson.order} 课之前的课程将标记为已完成；"
                "当前课及之后的课程将标记为未完成。已有练习历史不会删除。"
            )
        self.effect_text.setText(text)
