from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)


class Source(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    score: float
    position: int
    snippet: str


class AskResponse(BaseModel):
    answer: str
    mode: str
    sources: list[Source]


class DocumentInfo(BaseModel):
    document_id: str
    title: str
    chunks: int


class UploadResponse(BaseModel):
    documents: list[DocumentInfo]
