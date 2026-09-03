from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Protocol

from app.core.course_service import CourseService
from app.core.knowledge import KnowledgeRetriever
from app.core.models import AgentResponse
from app.core.prompts import SYSTEM_PROMPT, build_student_context
from app.data.repository import Repository


INTERRUPTED_REPLY_SUFFIX = "\n\n（回复因连接中断，内容可能不完整。）"


class ChatClient(Protocol):
    def chat(self, messages: list[dict[str, str]]) -> str: ...


class GuitarAgent:
    def __init__(
        self,
        repository: Repository,
        course_service: CourseService,
        chat_client: ChatClient,
        knowledge_retriever: KnowledgeRetriever | None = None,
    ):
        self.repository = repository
        self.course_service = course_service
        self.chat_client = chat_client
        self.knowledge_retriever = knowledge_retriever

    def chat(self, user_message: str, student_id: int) -> AgentResponse:
        messages, dashboard = self._prepare_request(user_message, student_id)
        reply = self.chat_client.chat(messages)
        self.repository.add_message(student_id, "assistant", reply)
        return self._response(reply, dashboard)

    def stream_chat(
        self,
        user_message: str,
        student_id: int,
        on_chunk: Callable[[str], None],
    ) -> AgentResponse:
        messages, dashboard = self._prepare_request(user_message, student_id)
        chunks: list[str] = []
        stream_method = getattr(self.chat_client, "stream_chat", None)
        try:
            stream: Iterator[str]
            if callable(stream_method):
                stream = iter(stream_method(messages))
            else:
                stream = iter((self.chat_client.chat(messages),))

            for chunk in stream:
                if not chunk:
                    continue
                chunks.append(chunk)
                on_chunk(chunk)
        except Exception:
            if chunks:
                partial_reply = "".join(chunks).rstrip()
                self.repository.add_message(
                    student_id,
                    "assistant",
                    f"{partial_reply}{INTERRUPTED_REPLY_SUFFIX}",
                )
            raise

        reply = "".join(chunks).strip()
        if not reply:
            raise ValueError("DeepSeek 没有返回可显示的内容。")
        self.repository.add_message(student_id, "assistant", reply)
        return self._response(reply, dashboard)

    def _prepare_request(self, user_message: str, student_id: int):
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("请输入你想问的问题。")

        dashboard = self.course_service.get_dashboard(student_id)
        history = self.repository.list_messages(student_id, limit=12)
        self.repository.add_message(student_id, "user", user_message)

        messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "system",
                "content": build_student_context(
                    dashboard.student,
                    dashboard.current_lesson,
                    dashboard.completed_count,
                    dashboard.total_lessons,
                ),
            },
        ]
        if self.knowledge_retriever is not None:
            knowledge_context = self.knowledge_retriever.format_context(
                self.knowledge_retriever.search(user_message)
            )
            if knowledge_context:
                messages.append({"role": "system", "content": knowledge_context})
        messages.extend(
            {"role": item.role, "content": item.content} for item in history
        )
        messages.append({"role": "user", "content": user_message})

        return messages, dashboard

    @staticmethod
    def _response(reply, dashboard) -> AgentResponse:
        lesson = dashboard.current_lesson
        return AgentResponse(
            reply=reply,
            suggested_lesson_id=lesson.id if lesson else None,
            practice_task=lesson.practice_task if lesson else None,
            progress_note=f"已完成 {dashboard.completed_count}/{dashboard.total_lessons} 节基础课",
        )
