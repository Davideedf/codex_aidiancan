from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.api.schemas import AskRequest, AskResponse, UploadResponse
from app.core.config import Settings, get_settings
from app.rag.index import KnowledgeIndex
from app.services.agent import KnowledgeAgent
from app.services.llm import LLMClient

router = APIRouter(prefix="/api")


def get_index(settings: Settings = Depends(get_settings)) -> KnowledgeIndex:
    return KnowledgeIndex(settings.index_path)


def get_agent(
    settings: Settings = Depends(get_settings),
    index: KnowledgeIndex = Depends(get_index),
) -> KnowledgeAgent:
    return KnowledgeAgent(index=index, llm=LLMClient(settings))


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "ok": True,
        "app": settings.app_name,
        "llm_enabled": bool(settings.openai_api_key.strip()),
    }


@router.get("/documents")
def list_documents(index: KnowledgeIndex = Depends(get_index)) -> dict:
    return {"documents": index.list_documents()}


@router.post("/documents", response_model=UploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
    settings: Settings = Depends(get_settings),
    index: KnowledgeIndex = Depends(get_index),
) -> UploadResponse:
    uploaded = []
    for file in files:
        title = Path(file.filename or "untitled.txt").name
        content = await file.read()
        max_bytes = settings.max_upload_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail=f"{title} exceeds {settings.max_upload_mb} MB.")

        text = _decode_text(title, content)
        if not text.strip():
            raise HTTPException(status_code=400, detail=f"{title} is empty or unreadable.")

        saved_path = settings.documents_dir / title
        saved_path.write_bytes(content)
        uploaded.append(index.add_document(title=title, text=text))

    return UploadResponse(documents=uploaded)


@router.delete("/documents")
def clear_documents(index: KnowledgeIndex = Depends(get_index)) -> JSONResponse:
    index.clear()
    return JSONResponse({"ok": True})


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest, agent: KnowledgeAgent = Depends(get_agent)) -> dict:
    return await agent.ask(request.question, top_k=request.top_k)


def _decode_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in {".txt", ".md", ".csv", ".json", ".log"}:
        raise HTTPException(
            status_code=415,
            detail="当前 MVP 支持 txt、md、csv、json、log。PDF/Word 可后续接入解析器。",
        )

    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise HTTPException(status_code=400, detail=f"{filename} cannot be decoded as text.")
