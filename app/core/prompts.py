from __future__ import annotations

from app.core.models import Lesson, Student


SYSTEM_PROMPT = """你是一名耐心、严谨的吉他初学者教练，服务对象可能完全没有音乐基础。

必须遵守以下教学规则：
1. 每次只集中讲一个主要重点，使用简单中文，并解释必要术语。
2. 回答应给出可执行练习，写明时间、次数、完成标准和常见错误。
3. 优先保证姿势放松、声音清晰和节拍稳定，再增加难度。
4. 只能依据用户提供的文字判断；没有音频或视频时，绝不能声称听到或看到演奏。
5. 若用户描述剧烈疼痛、麻木、肿胀或关节不适，应让其立即停止练习并休息，必要时寻求专业医疗建议。
6. 结合学生已完成课程和当前课程回答，不要一次布置超出其水平的大量内容。
7. 保持鼓励但不夸大效果。回答控制在适合聊天阅读的长度。
8. 当提供了知识库参考资料时，优先以资料为依据；资料没有覆盖的问题，不要把猜测说成资料中的事实。

推荐回答结构：今天的重点、练习步骤、完成标准、常见错误、练完后反馈什么。"""


def build_student_context(
    student: Student,
    current_lesson: Lesson | None,
    completed_count: int,
    total_lessons: int,
) -> str:
    if current_lesson is None:
        lesson_text = "基础课程已全部完成，可以帮助学生复习薄弱点或制定进阶计划。"
    else:
        steps = "；".join(current_lesson.practice_steps)
        criteria = "；".join(current_lesson.success_criteria)
        mistakes = "；".join(current_lesson.common_mistakes)
        lesson_text = (
            f"当前课程：{current_lesson.title}\n"
            f"课程目标：{current_lesson.goal}\n"
            f"建议时长：{current_lesson.duration_minutes} 分钟\n"
            f"练习步骤：{steps}\n"
            f"完成标准：{criteria}\n"
            f"常见错误：{mistakes}"
        )

    return (
        "以下是当前学生状态，只用于本次教学：\n"
        f"称呼：{student.name}\n"
        f"水平：{student.level}\n"
        f"目标：{student.goal}\n"
        f"每日练习：{student.practice_minutes} 分钟\n"
        f"课程进度：{completed_count}/{total_lessons}\n"
        f"{lesson_text}"
    )
