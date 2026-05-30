from __future__ import annotations

from dataclasses import asdict

from app.rag.index import KnowledgeIndex, SearchResult
from app.services.llm import LLMClient


class KnowledgeAgent:
    def __init__(self, index: KnowledgeIndex, llm: LLMClient):
        self.index = index
        self.llm = llm

    async def ask(self, question: str, top_k: int = 5) -> dict:
        results = self.index.search(question, top_k=top_k)
        if not results:
            return {
                "answer": "知识库里暂时没有检索到相关资料。请先上传企业文档，或换一种更具体的问法。",
                "mode": "local",
                "sources": [],
            }

        context = _format_context(results)
        if self.llm.enabled:
            try:
                answer = await self.llm.answer(question, context)
                mode = "llm"
            except Exception as exc:  # Keep the product usable if the model call fails.
                answer = _fallback_answer(question, results)
                mode = f"local_fallback: {exc.__class__.__name__}"
        else:
            answer = _fallback_answer(question, results)
            mode = "local"

        return {
            "answer": answer,
            "mode": mode,
            "sources": [_source_payload(result) for result in results],
        }


def _format_context(results: list[SearchResult]) -> str:
    blocks = []
    for index, result in enumerate(results, start=1):
        blocks.append(
            f"[{index}] 标题：{result.title}\n"
            f"片段位置：{result.position + 1}\n"
            f"相关度：{result.score}\n"
            f"内容：\n{result.text}"
        )
    return "\n\n---\n\n".join(blocks)


def _fallback_answer(question: str, results: list[SearchResult]) -> str:
    best = results[0]
    snippets = "\n\n".join(f"- {result.text[:360]}" for result in results[:3])
    return (
        f"我在知识库中找到了与“{question}”相关的资料，但当前未配置 OPENAI_API_KEY，"
        "所以先给出检索式摘要：\n\n"
        f"{snippets}\n\n"
        f"最相关来源：{best.title}"
    )


def _source_payload(result: SearchResult) -> dict:
    payload = asdict(result)
    payload["snippet"] = result.text[:240]
    payload.pop("text", None)
    return payload
