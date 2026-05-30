from __future__ import annotations

from typing import Any

import httpx

from app.core.config import Settings


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.openai_api_key.strip())

    async def answer(self, question: str, context: str) -> str:
        if not self.enabled:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        payload = {
            "model": self.settings.openai_model,
            "instructions": (
                "你是企业知识库问答 Agent。只依据给定资料回答；"
                "如果资料不足，明确说不知道，并提示需要补充哪类资料。"
                "回答要简洁、可执行，并尽量引用资料中的名称或条款。"
            ),
            "input": (
                f"用户问题：\n{question}\n\n"
                f"可用企业知识库资料：\n{context}\n\n"
                "请用中文回答，并在最后给出“依据：”列出使用到的资料标题。"
            ),
        }

        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                f"{self.settings.openai_base_url.rstrip('/')}/responses",
                headers={
                    "Authorization": f"Bearer {self.settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        return _extract_output_text(data)


def _extract_output_text(data: dict[str, Any]) -> str:
    if data.get("output_text"):
        return str(data["output_text"]).strip()

    parts: list[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if text:
                parts.append(str(text))
    return "\n".join(parts).strip() or "模型没有返回可读文本。"
