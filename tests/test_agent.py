from pathlib import Path

import pytest

from app.core.agent import GuitarAgent, INTERRUPTED_REPLY_SUFFIX
from app.core.course_service import CourseService
from app.core.knowledge import KnowledgeRetriever
from app.core.lessons import load_lessons
from app.data.repository import Repository
from app.services.deepseek import DeepSeekError


LESSONS_FILE = Path(__file__).resolve().parents[1] / "lessons" / "lessons.json"


class FakeChatClient:
    def __init__(self, reply="今天先练习正确持琴 15 分钟。"):
        self.reply = reply
        self.messages = None

    def chat(self, messages):
        self.messages = messages
        return self.reply


class FailingChatClient:
    def chat(self, messages):
        raise DeepSeekError("模拟网络失败")


class FakeStreamingChatClient(FakeChatClient):
    def stream_chat(self, messages):
        self.messages = messages
        yield "今天先练"
        yield "正确持琴。"


class PartialFailingStreamingClient(FakeChatClient):
    def stream_chat(self, messages):
        self.messages = messages
        yield "已经收到的部分"
        raise DeepSeekError("模拟流式连接中断")


def make_agent(tmp_path, chat_client):
    repository = Repository(tmp_path / "guitar.db")
    repository.initialize()
    lessons = load_lessons(LESSONS_FILE)
    course_service = CourseService(repository, lessons)
    student = course_service.get_dashboard().student
    return repository, student, GuitarAgent(repository, course_service, chat_client)


def test_agent_builds_context_and_saves_conversation(tmp_path):
    client = FakeChatClient()
    repository, student, agent = make_agent(tmp_path, client)

    response = agent.chat("我今天练什么？", student.id)

    assert response.reply == client.reply
    assert response.suggested_lesson_id == "lesson-01-posture"
    assert client.messages[0]["role"] == "system"
    assert "剧烈疼痛" in client.messages[0]["content"]
    assert "当前课程：认识吉他与正确持琴" in client.messages[1]["content"]
    assert client.messages[-1] == {"role": "user", "content": "我今天练什么？"}
    history = repository.list_messages(student.id)
    assert [(item.role, item.content) for item in history] == [
        ("user", "我今天练什么？"),
        ("assistant", client.reply),
    ]


def test_failed_api_call_keeps_user_message(tmp_path):
    repository, student, agent = make_agent(tmp_path, FailingChatClient())

    with pytest.raises(DeepSeekError, match="模拟网络失败"):
        agent.chat("这条消息不能丢", student.id)

    history = repository.list_messages(student.id)
    assert len(history) == 1
    assert history[0].content == "这条消息不能丢"


def test_empty_message_is_rejected_without_writing(tmp_path):
    repository, student, agent = make_agent(tmp_path, FakeChatClient())

    with pytest.raises(ValueError, match="请输入"):
        agent.chat("   ", student.id)

    assert repository.list_messages(student.id) == ()


def test_agent_streams_chunks_and_saves_complete_reply(tmp_path):
    client = FakeStreamingChatClient()
    repository, student, agent = make_agent(tmp_path, client)
    chunks = []

    response = agent.stream_chat("开始练习", student.id, chunks.append)

    assert chunks == ["今天先练", "正确持琴。"]
    assert response.reply == "今天先练正确持琴。"
    history = repository.list_messages(student.id)
    assert [(item.role, item.content) for item in history] == [
        ("user", "开始练习"),
        ("assistant", "今天先练正确持琴。"),
    ]


def test_interrupted_stream_persists_partial_reply(tmp_path):
    repository, student, agent = make_agent(
        tmp_path, PartialFailingStreamingClient()
    )
    chunks = []

    with pytest.raises(DeepSeekError, match="模拟流式连接中断"):
        agent.stream_chat("继续", student.id, chunks.append)

    assert chunks == ["已经收到的部分"]
    history = repository.list_messages(student.id)
    assert history[-1].content == f"已经收到的部分{INTERRUPTED_REPLY_SUFFIX}"


def test_agent_adds_retrieved_knowledge_without_saving_it_as_history(tmp_path):
    client = FakeChatClient()
    repository, student, agent = make_agent(tmp_path, client)
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "tablature.md").write_text(
        "# 六线谱教程\n\n## 基础\n\n0 代表空弦音，左手不按弦。\n",
        encoding="utf-8",
    )
    agent.knowledge_retriever = KnowledgeRetriever.from_directory(knowledge_dir)

    agent.chat("吉他谱中的 0 是什么意思？", student.id)

    knowledge_message = next(
        message["content"]
        for message in client.messages
        if message["role"] == "system" and "本次检索到的参考资料" in message["content"]
    )
    assert "空弦音" in knowledge_message
    assert "六线谱教程 / 基础" in knowledge_message
    assert len(repository.list_messages(student.id)) == 2
