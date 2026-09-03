from app.core.knowledge import KnowledgeRetriever


def test_markdown_knowledge_is_chunked_and_retrieved_by_section(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "tablature.md").write_text(
        """# 六线谱教程

来源：https://example.test/tablature

## 基础

0 代表空弦音，左手不按弦，右手弹奏相应的弦。

## 扫弦

扫弦可以用箭头表示方向，要从慢速节拍开始练习。
""",
        encoding="utf-8",
    )

    retriever = KnowledgeRetriever.from_directory(knowledge_dir)
    matches = retriever.search("吉他谱里的 0 是什么意思")

    assert retriever.chunk_count == 2
    assert matches[0].section == "基础"
    assert "空弦音" in matches[0].text
    context = retriever.format_context(matches[:1])
    assert "六线谱教程 / 基础" in context
    assert "https://example.test/tablature" in context


def test_search_returns_no_context_for_unrelated_question(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "one.md").write_text(
        "# 六线谱教程\n\n## 基础\n\n空弦音的记号是 0。\n",
        encoding="utf-8",
    )

    retriever = KnowledgeRetriever.from_directory(knowledge_dir)

    assert retriever.search("怎样烤面包") == ()


def test_notation_symbol_with_represents_phrase_prioritizes_exact_explanation(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "notation.md").write_text(
        """# 六线谱教程

## 右手指法

右手也会使用数字 0 和 1 记录练习次数。

## 基础

0 代表空弦音，左手不按弦，右手弹奏相应的弦。
""",
        encoding="utf-8",
    )

    retriever = KnowledgeRetriever.from_directory(knowledge_dir)

    assert retriever.search("吉他谱里的 0 代表什么")[0].section == "基础"
