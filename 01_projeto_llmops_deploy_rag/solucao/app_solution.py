"""API FastAPI funcional do módulo 01."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

try:
    from .rag_core import Documento, RagService
except ImportError:  # execução via uvicorn solucao.app_solution:app
    from rag_core import Documento, RagService

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
service = RagService(DATA_DIR)


@asynccontextmanager
async def lifespan(_: FastAPI):
    service.carregar_diretorio()
    yield


app = FastAPI(title="Aurora RAG API", version="0.1.0", lifespan=lifespan)


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
    return service.health()


@app.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest) -> IngestResponse:
    documentos = [
        Documento.criar(d.id, d.titulo, d.texto, d.fonte) for d in payload.documentos
    ]
    return IngestResponse(**service.ingest(documentos))


@app.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest, request: Request) -> QueryResponse:
    rid = request.headers.get("x-request-id")
    resultado = service.query(payload.pergunta, payload.top_k, rid)
    return QueryResponse(
        request_id=resultado.request_id,
        resposta=resultado.resposta,
        fontes=list(resultado.fontes),
        score=resultado.score,
        absteve=resultado.absteve,
        latencia_ms=resultado.latencia_ms,
    )
