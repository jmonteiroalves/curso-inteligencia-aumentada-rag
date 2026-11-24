"""API FastAPI — esqueleto do aluno (módulo 01).

Rode com:
    uvicorn src.app:app --app-dir . --reload
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from .rag_core import Documento, RagService
except ImportError:  # execução direta: python3 src/app.py / uvicorn src.app --app-dir .
    from rag_core import Documento, RagService

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
service = RagService(DATA_DIR)
app = FastAPI(title="Aurora RAG API", version="0.1.0")


class DocumentoIn(BaseModel):
    id: str = Field(min_length=1)
    titulo: str = Field(min_length=1)
    texto: str = Field(min_length=20)
    fonte: str = Field(min_length=1)


class IngestRequest(BaseModel):
    documentos: list[DocumentoIn] = Field(min_length=1, max_length=100)


class IngestResponse(BaseModel):
    novos: int
    atualizados: int
    ignorados: int
    chunks: int


class QueryRequest(BaseModel):
    pergunta: str = Field(min_length=3, max_length=500)
    top_k: int = Field(default=3, ge=1, le=10)


class QueryResponse(BaseModel):
    request_id: str
    resposta: str
    fontes: list[str]
    score: float
    absteve: bool
    latencia_ms: float


@app.get("/health")
def health() -> dict[str, object]:
    """TODO(1.1): carregue o corpus no startup (lifespan) e devolva `service.health()`."""
    return service.health()


@app.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest) -> IngestResponse:
    """TODO(1.2): converta `DocumentoIn` em `Documento.criar` e chame o serviço."""
    raise HTTPException(status_code=501, detail="TODO(1.2): ingestão não implementada")


@app.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest) -> QueryResponse:
    """TODO(1.1/1.3): valide e delegue para `service.query`."""
    raise HTTPException(status_code=501, detail="TODO(1.3): consulta não implementada")
