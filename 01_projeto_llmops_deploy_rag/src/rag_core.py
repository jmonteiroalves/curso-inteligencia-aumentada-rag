"""Core do serviço RAG — esqueleto do aluno (módulo 01).

Foco: ingestão idempotente, contrato de consulta, citação e observabilidade.
Execute a partir da raiz do módulo para que os caminhos de dados funcionem.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import time
import unicodedata
import uuid
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

DIMENSAO = 256
MAX_CHARS = 420
OVERLAP = 70
MIN_SCORE = 0.18
VERSAO = "0.1.0"

STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "do", "da", "dos", "das", "em", "no", "na",
    "nos", "nas", "por", "para", "com", "sem", "que", "qual", "quais", "quando", "onde",
    "como", "quem", "e", "ou", "é", "são", "ser", "foi", "tem", "ter", "há", "ao", "aos",
    "se", "sua", "seu", "suas", "seus", "mais", "menos", "muito", "quanto", "quantos",
}

logger = logging.getLogger("curso.rag")


@dataclass(frozen=True)
class Documento:
    id: str
    titulo: str
    texto: str
    fonte: str
    checksum: str = ""

    @staticmethod
    def criar(id: str, titulo: str, texto: str, fonte: str) -> "Documento":
        checksum = hashlib.sha256(f"{titulo}\n{texto}".encode("utf-8")).hexdigest()[:16]
        return Documento(id=id, titulo=titulo, texto=texto, fonte=fonte, checksum=checksum)


@dataclass(frozen=True)
class Chunk:
    id: str
    doc_id: str
    texto: str
    fonte: str


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class QueryResult:
    pergunta: str
    resposta: str
    fontes: tuple[str, ...]
    score: float
    absteve: bool
    latencia_ms: float
    request_id: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def normalizar(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"[^a-z0-9\s]", " ", "".join(c for c in decomposto if not unicodedata.combining(c)))


def tokenizar(texto: str) -> list[str]:
    return [t for t in normalizar(texto).split() if len(t) > 2 and t not in STOPWORDS]


def embed(texto: str) -> list[float]:
    vetor = [0.0] * DIMENSAO
    for token, freq in Counter(tokenizar(texto)).items():
        digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
        indice = int.from_bytes(digest[:4], "big") % DIMENSAO
        sinal = 1.0 if digest[4] & 1 else -1.0
        vetor[indice] += sinal * (1.0 + math.log(freq))
    norma = math.sqrt(sum(v * v for v in vetor))
    return [v / norma for v in vetor] if norma else vetor


def cosseno(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def chunkar(texto: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP) -> list[str]:
    palavras = texto.split()
    chunks: list[str] = []
    atuais: list[str] = []
    for palavra in palavras:
        if atuais and len(" ".join([*atuais, palavra])) > max_chars:
            chunks.append(" ".join(atuais))
            cauda: list[str] = []
            for anterior in reversed(atuais):
                if len(" ".join([anterior, *cauda])) > overlap:
                    break
                cauda.insert(0, anterior)
            atuais = [*cauda, palavra]
        else:
            atuais.append(palavra)
    if atuais and (not chunks or " ".join(atuais) != chunks[-1]):
        chunks.append(" ".join(atuais))
    return chunks


class RagService:
    """Serviço em memória com ingestão idempotente e eventos observáveis."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir
        self.documentos: dict[str, Documento] = {}
        self.chunks: list[Chunk] = []
        self.vetores: list[list[float]] = []
        self.eventos: list[dict[str, object]] = []

    def carregar_diretorio(self, subdir: str = "base_conhecimento") -> dict[str, int]:
        """Lê Markdowns e delega para `ingest`."""
        if self.data_dir is None:
            raise ValueError("data_dir não configurado")
        documentos = []
        for caminho in sorted((self.data_dir / subdir).glob("*.md")):
            texto = caminho.read_text(encoding="utf-8").strip()
            titulo = texto.splitlines()[0].lstrip("# ").strip() if texto else caminho.stem
            documentos.append(Documento.criar(caminho.stem, titulo, texto, caminho.name))
        return self.ingest(documentos)

    def ingest(self, documentos: Iterable[Documento]) -> dict[str, int]:
        """Ingere um lote e devolve `novos`, `atualizados` e `ignorados`.

        TODO(1.2):
        - use `documento.id` como chave;
        - se o checksum não mudou, conte como ignorado;
        - se é novo, insira; se mudou, substitua;
        - reconstrua chunks/vetores **uma vez** ao final do lote;
        - nunca duplique chunks de um mesmo documento.
        """
        # TODO(1.2): implemente ingestão idempotente
        raise NotImplementedError("TODO(1.2): implemente ingestão idempotente")

    def _rebuild(self) -> None:
        self.chunks = []
        self.vetores = []
        for documento in sorted(self.documentos.values(), key=lambda d: d.id):
            for posicao, texto in enumerate(chunkar(documento.texto)):
                chunk = Chunk(f"{documento.id}:{posicao}", documento.id, texto, documento.fonte)
                self.chunks.append(chunk)
                self.vetores.append(embed(texto))

    def search(self, pergunta: str, top_k: int = 3, min_score: float = MIN_SCORE) -> list[Hit]:
        """Busca híbrida. TODO(1.3): cosseno + interseção lexical."""
        # TODO(1.3): implemente search
        raise NotImplementedError("TODO(1.3): implemente search")

    def query(self, pergunta: str, top_k: int = 3, request_id: str | None = None) -> QueryResult:
        """Executa a consulta e registra um evento estruturado.

        TODO(1.3): resposta extrativa com citações e abstenção.
        TODO(1.5): preencha tempo, request_id, top_k, score e fontes em `self.eventos`.
        """
        # TODO(1.3/1.5): implemente query
        raise NotImplementedError("TODO(1.3/1.5): implemente query")

    def health(self) -> dict[str, object]:
        return {
            "status": "ok" if self.chunks else "vazio",
            "versao": VERSAO,
            "documentos": len(self.documentos),
            "chunks": len(self.chunks),
        }
