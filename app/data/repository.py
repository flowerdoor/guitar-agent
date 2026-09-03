from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable

from app.core.models import Message, PracticeRecord, Student


class DatabaseError(RuntimeError):
    """Raised when application data cannot be read or written."""


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    level TEXT NOT NULL,
    goal TEXT NOT NULL,
    practice_minutes INTEGER NOT NULL CHECK(practice_minutes BETWEEN 5 AND 180),
    current_stage INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS lesson_progress (
    student_id INTEGER NOT NULL,
    lesson_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('completed')),
    completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(student_id, lesson_id),
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS practice_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    lesson_id TEXT NOT NULL,
    lesson_title TEXT NOT NULL,
    task TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK(duration_minutes BETWEEN 1 AND 300),
    result TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_student_id ON messages(student_id, id);
CREATE INDEX IF NOT EXISTS idx_practice_student_id ON practice_records(student_id, id);
"""


class Repository:
    def __init__(self, database_path: Path):
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        try:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.executescript(SCHEMA)
                connection.commit()
        except (OSError, sqlite3.Error) as exc:
            raise DatabaseError(f"无法初始化数据库 {self.database_path}：{exc}") from exc

    def _connect(self) -> sqlite3.Connection:
        try:
            connection = sqlite3.connect(self.database_path, timeout=10)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            return connection
        except sqlite3.Error as exc:
            raise DatabaseError(f"无法连接数据库：{exc}") from exc

    def get_or_create_default_student(self) -> Student:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT * FROM students ORDER BY id LIMIT 1"
                ).fetchone()
                if row is None:
                    cursor = connection.execute(
                        """
                        INSERT INTO students(name, level, goal, practice_minutes, current_stage)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        ("同学", "零基础", "掌握基础和弦并完成第一首弹唱", 20, 1),
                    )
                    connection.commit()
                    row = connection.execute(
                        "SELECT * FROM students WHERE id = ?", (cursor.lastrowid,)
                    ).fetchone()
                return self._student_from_row(row)
        except sqlite3.Error as exc:
            raise DatabaseError(f"无法读取学生资料：{exc}") from exc

    def update_student(
        self, student_id: int, *, name: str, goal: str, practice_minutes: int
    ) -> Student:
        name = name.strip() or "同学"
        goal = goal.strip() or "掌握吉他基础"
        if not 5 <= practice_minutes <= 180:
            raise ValueError("每日练习时间必须在 5 到 180 分钟之间。")
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE students
                    SET name = ?, goal = ?, practice_minutes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (name, goal, practice_minutes, student_id),
                )
                connection.commit()
                row = connection.execute(
                    "SELECT * FROM students WHERE id = ?", (student_id,)
                ).fetchone()
                if row is None:
                    raise DatabaseError("找不到学生资料。")
                return self._student_from_row(row)
        except sqlite3.Error as exc:
            raise DatabaseError(f"无法更新学生资料：{exc}") from exc

    def set_current_stage(self, student_id: int, stage: int) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    "UPDATE students SET current_stage = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (stage, student_id),
                )
                connection.commit()
        except sqlite3.Error as exc:
            raise DatabaseError(f"无法更新课程阶段：{exc}") from exc

    def add_message(self, student_id: int, role: str, content: str) -> None:
        if role not in {"user", "assistant"}:
            raise ValueError("消息角色只能是 user 或 assistant。")
        try:
            with self._connect() as connection:
                connection.execute(
                    "INSERT INTO messages(student_id, role, content) VALUES (?, ?, ?)",
                    (student_id, role, content),
                )
                connection.commit()
        except sqlite3.Error as exc:
            raise DatabaseError(f"无法保存对话：{exc}") from exc

    def list_messages(self, student_id: int, limit: int = 50) -> tuple[Message, ...]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT role, content, created_at
                    FROM messages WHERE student_id = ?
                    ORDER BY id DESC LIMIT ?
                    """,
                    (student_id, limit),
                ).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError(f"无法读取对话历史：{exc}") from exc
        return tuple(
            Message(row["role"], row["content"], _parse_datetime(row["created_at"]))
            for row in reversed(rows)
        )

    def completed_lesson_ids(self, student_id: int) -> frozenset[str]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT lesson_id FROM lesson_progress WHERE student_id = ?",
                    (student_id,),
                ).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError(f"无法读取课程进度：{exc}") from exc
        return frozenset(str(row["lesson_id"]) for row in rows)

    def replace_lesson_progress(
        self,
        student_id: int,
        completed_lesson_ids: Iterable[str],
        current_stage: int,
    ) -> None:
        completed_ids = tuple(dict.fromkeys(completed_lesson_ids))
        try:
            with self._connect() as connection:
                connection.execute(
                    "DELETE FROM lesson_progress WHERE student_id = ?",
                    (student_id,),
                )
                connection.executemany(
                    """
                    INSERT INTO lesson_progress(student_id, lesson_id, status)
                    VALUES (?, ?, 'completed')
                    """,
                    ((student_id, lesson_id) for lesson_id in completed_ids),
                )
                cursor = connection.execute(
                    """
                    UPDATE students
                    SET current_stage = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (current_stage, student_id),
                )
                if cursor.rowcount != 1:
                    raise DatabaseError("找不到学生资料。")
                connection.commit()
        except sqlite3.Error as exc:
            raise DatabaseError(f"无法切换课程进度：{exc}") from exc

    def complete_lesson(
        self,
        student_id: int,
        *,
        lesson_id: str,
        lesson_title: str,
        task: str,
        duration_minutes: int,
        notes: str,
    ) -> None:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO lesson_progress(student_id, lesson_id, status)
                    VALUES (?, ?, 'completed')
                    """,
                    (student_id, lesson_id),
                )
                connection.execute(
                    """
                    INSERT INTO practice_records(
                        student_id, lesson_id, lesson_title, task,
                        duration_minutes, result, notes
                    ) VALUES (?, ?, ?, ?, ?, 'completed', ?)
                    """,
                    (
                        student_id,
                        lesson_id,
                        lesson_title,
                        task,
                        duration_minutes,
                        notes.strip(),
                    ),
                )
                connection.commit()
        except sqlite3.Error as exc:
            raise DatabaseError(f"无法保存练习记录：{exc}") from exc

    def list_practice_records(
        self, student_id: int, limit: int = 20
    ) -> tuple[PracticeRecord, ...]:
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT lesson_id, lesson_title, duration_minutes, result, notes, created_at
                    FROM practice_records WHERE student_id = ?
                    ORDER BY id DESC LIMIT ?
                    """,
                    (student_id, limit),
                ).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError(f"无法读取练习记录：{exc}") from exc
        return tuple(
            PracticeRecord(
                lesson_id=row["lesson_id"],
                lesson_title=row["lesson_title"],
                duration_minutes=row["duration_minutes"],
                result=row["result"],
                notes=row["notes"],
                created_at=_parse_datetime(row["created_at"]),
            )
            for row in rows
        )

    @staticmethod
    def _student_from_row(row: sqlite3.Row) -> Student:
        return Student(
            id=row["id"],
            name=row["name"],
            level=row["level"],
            goal=row["goal"],
            practice_minutes=row["practice_minutes"],
            current_stage=row["current_stage"],
        )


def _parse_datetime(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime.now()
