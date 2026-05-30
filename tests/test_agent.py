import asyncio

from app.core.config import Settings
from app.rag.index import KnowledgeIndex
from app.services.agent import KnowledgeAgent
from app.services.llm import LLMClient


def test_agent_uses_local_fallback_without_openai_key(tmp_path):
    settings = Settings(data_dir=tmp_path, openai_api_key="")
    index = KnowledgeIndex(settings.index_path)
    index.add_document("报销.md", "报销申请需要发票和审批单。")
    agent = KnowledgeAgent(index=index, llm=LLMClient(settings))

    response = asyncio.run(agent.ask("报销需要什么"))

    assert response["mode"] == "local"
    assert response["sources"]
    assert "发票" in response["answer"]
