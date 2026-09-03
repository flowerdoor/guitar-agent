from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from app.config import ConfigError, load_config
from app.core.agent import GuitarAgent
from app.core.course_service import CourseService
from app.core.knowledge import KnowledgeRetriever
from app.core.lessons import LessonLoadError, load_lessons
from app.data.repository import DatabaseError, Repository
from app.paths import get_app_paths
from app.services.deepseek import DeepSeekClient
from app.ui.main_window import MainWindow


def run() -> int:
    application = QApplication.instance() or QApplication(sys.argv)
    application.setApplicationName("弦上教练")
    application.setOrganizationName("GuitarCoach")

    paths = get_app_paths()
    try:
        config = load_config(paths.config_file)
        lessons = load_lessons(paths.lessons_file)
        repository = Repository(paths.database_file)
        repository.initialize()
        course_service = CourseService(repository, lessons)
        agent = GuitarAgent(
            repository,
            course_service,
            DeepSeekClient(config),
            KnowledgeRetriever.from_directory(paths.knowledge_dir),
        )
        window = MainWindow(
            agent,
            course_service,
            repository,
            api_configured=config.api_configured,
            config_path=paths.config_file,
        )
    except (ConfigError, LessonLoadError, DatabaseError) as exc:
        QMessageBox.critical(
            None,
            "弦上教练无法启动",
            f"{exc}\n\n请修正问题后重新启动应用。",
        )
        return 1

    window.show()
    return application.exec()
