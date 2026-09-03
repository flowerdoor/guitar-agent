from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from app.core.agent import GuitarAgent
from app.data.repository import DatabaseError
from app.services.deepseek import DeepSeekError


class ChatWorker(QObject):
    chunk_received = Signal(str)
    succeeded = Signal(object)
    failed = Signal(str)
    completed = Signal()

    def __init__(self, agent: GuitarAgent, message: str, student_id: int):
        super().__init__()
        self.agent = agent
        self.message = message
        self.student_id = student_id

    @Slot()
    def run(self) -> None:
        try:
            response = self.agent.stream_chat(
                self.message,
                self.student_id,
                self.chunk_received.emit,
            )
            self.succeeded.emit(response)
        except (DeepSeekError, DatabaseError, ValueError) as exc:
            self.failed.emit(str(exc))
        except Exception:
            self.failed.emit("发生了未预期错误，请稍后重试。")
        finally:
            self.completed.emit()
