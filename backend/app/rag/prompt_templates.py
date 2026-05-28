from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    version: str
    system: str
    user: str


PROMPT_TEMPLATES: dict[tuple[str, str], PromptTemplate] = {
    (
        "rag_default",
        "v1",
    ): PromptTemplate(
        name="rag_default",
        version="v1",
        system=(
            "你是企业知识库问答助手。你的回答必须严格基于提供的上下文。"
            "如果上下文中没有明确依据，请回复：知识库中未找到明确依据。"
            "关键结论必须附引用编号，不得编造制度、流程或金额。"
        ),
        user=(
            "已知上下文：\n{context}\n\n"
            "用户问题：{question}\n\n"
            "请基于上下文回答，必须附引用编号，例如：[1][2]。"
        ),
    ),
    (
        "rag_structured",
        "v1",
    ): PromptTemplate(
        name="rag_structured",
        version="v1",
        system=(
            "你是企业知识库问答助手。你的回答必须严格基于提供的上下文。"
            "如果上下文中没有明确依据，请回复：知识库中未找到明确依据。"
            "关键结论必须附引用编号，不得编造制度、流程或金额。"
            "输出必须是结构化 Markdown，遵循固定栏目。"
        ),
        user=(
            "已知上下文：\n{context}\n\n"
            "用户问题：{question}\n\n"
            "请输出以下 Markdown 格式（不要添加其它标题）：\n"
            "## 结论\n"
            "- 用 1-3 条简要结论回答问题，每条结论必须带引用编号。\n\n"
            "## 依据\n"
            "- 列出支持结论的要点，可用子项补充细节，并在句末标注引用编号。\n\n"
            "## 引用\n"
            "- [1] 文档名 - 页码/段落（如果可用）\n"
            "- [2] 文档名 - 页码/段落（如果可用）\n\n"
            "规则：只能基于上下文作答。引用编号必须与上下文片段顺序一致。"
        ),
    ),
}


def get_prompt_template(name: str | None, version: str | None) -> PromptTemplate:
    key = (name or settings.prompt_template_name, version or settings.prompt_template_version)
    template = PROMPT_TEMPLATES.get(key)
    if template is None:
        template = PROMPT_TEMPLATES[("rag_default", "v1")]
    return template


def build_messages(question: str, context: str) -> list[dict[str, str]]:
    template = get_prompt_template(None, None)
    return [
        {"role": "system", "content": template.system},
        {
            "role": "user",
            "content": template.user.format(context=context, question=question),
        },
    ]
