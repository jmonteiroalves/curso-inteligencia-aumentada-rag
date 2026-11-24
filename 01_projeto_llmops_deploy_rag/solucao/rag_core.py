"""Referência funcional do core RAG/LLMOps (módulo 01)."""

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
        return Documento(id, titulo, texto, fonte, checksum)


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
    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir
        self.documentos: dict[str, Documento] = {}
        self.chunks: list[Chunk] = []
        self.vetores: list[list[float]] = []
        self.eventos: list[dict[str, object]] = []

    def carregar_diretorio(self, subdir: str = "base_conhecimento") -> dict[str, int]:
        if self.data_dir is None:
            raise ValueError("data_dir não configurado")
        documentos = []
        for caminho in sorted((self.data_dir / subdir).glob("*.md")):
            texto = caminho.read_text(encoding="utf-8").strip()
            titulo = texto.splitlines()[0].lstrip("# ").strip() if texto else caminho.stem
            documentos.append(Documento.criar(caminho.stem, titulo, texto, caminho.name))
        return self.ingest(documentos)

    def ingest(self, documentos: Iterable[Documento]) -> dict[str, int]:
        contagem = {"novos": 0, "atualizados": 0, "ignorados": 0}
        for documento in documentos:
            if not documento.checksum:
                documento = Documento.criar(
                    documento.id, documento.titulo, documento.texto, documento.fonte
                )
            existente = self.documentos.get(documento.id)
            if existente and existente.checksum == documento.checksum:
                contagem["ignorados"] += 1
                continue
            if existente:
                contagem["atualizados"] += 1
            else:
                contagem["novos"] += 1
            self.documentos[documento.id] = documento
        self._rebuild()
        self.eventos.append({"evento": "ingestao", **contagem, "chunks": len(self.chunks)})
        logger.info(json.dumps(self.eventos[-1], ensure_ascii=False))
        return {**contagem, "chunks": len(self.chunks)}

    def _rebuild(self) -> None:
        self.chunks = []
        self.vetores = []
        for documento in sorted(self.documentos.values(), key=lambda d: d.id):
            for posicao, texto in enumerate(chunkar(documento.texto)):
                chunk = Chunk(f"{documento.id}:{posicao}", documento.id, texto, documento.fonte)
                self.chunks.append(chunk)
                self.vetores.append(embed(texto))

    def search(self, pergunta: str, top_k: int = 3, min_score: float = MIN_SCORE) -> list[Hit]:
        if not self.chunks:
            return []
        q = set(tokenizar(pergunta))
        vetor_q = embed(pergunta)
        hits: list[Hit] = []
        for chunk, vetor in zip(self.chunks, self.vetores):
            tokens = set(tokenizar(chunk.texto))
            lexical = len(q & tokens) / len(q) if q else 0.0
            score = 0.7 * max(0.0, cosseno(vetor_q, vetor)) + 0.3 * lexical
            if score >= min_score:
                hits.append(Hit(chunk, score))
        hits.sort(key=lambda h: (-h.score, h.chunk.id))
        return hits[:top_k]

    def query(self, pergunta: str, top_k: int = 3, request_id: str | None = None) -> QueryResult:
        inicio = time.perf_counter()
        rid = request_id or f"req_{uuid.uuid4().hex[:10]}"
        hits = self.search(pergunta, top_k=top_k)
        if not hits:
            resultado = QueryResult(
                pergunta,
                "Não encontrei evidência suficiente na base para responder.",
                (),
                0.0,
                True,
                0.0,
                rid,
            )
        else:
            q = set(tokenizar(pergunta))
            candidatas: list[tuple[float, str, str]] = []
            for hit in hits[:2]:
                for frase in re.split(r"(?<=[.!?])\s+", hit.chunk.texto.replace("\n", " ")):
                    overlap = len(q & set(tokenizar(frase))) / max(1, len(q))
                    if overlap:
                        candidatas.append((overlap + hit.score * 0.05, frase.strip(), hit.chunk.fonte))
            candidatas.sort(key=lambda c: -c[0])
            escolhidas: list[tuple[str, str]] = []
            for _, frase, fonte in candidatas:
                if frase not in {f for f, _ in escolhidas}:
                    escolhidas.append((frase, fonte))
                if len(escolhidas) == 2:
                    break
            if not escolhidas:
                escolhidas = [(hits[0].chunk.texto[:350], hits[0].chunk.fonte)]
            fontes = tuple(dict.fromkeys(f for _, f in escolhidas))
            texto = " ".join(f"[{fonte}] {frase}" for frase, fonte in escolhidas)
            resultado = QueryResult(
                pergunta, texto, fontes, hits[0].score, False, 0.0, rid
            )

        latencia = (time.perf_counter() - inicio) * 1000
        resultado = QueryResult(
            resultado.pergunta,
            resultado.resposta,
            resultado.fontes,
            round(resultado.score, 4),
            resultado.absteve,
            round(latencia, 3),
            rid,
        )
        evento = {
            "evento": "consulta",
            "request_id": rid,
            "pergunta": pergunta,
            "top_k": top_k,
            "fontes": list(resultado.fontes),
            "score": resultado.score,
            "latencia_ms": resultado.latencia_ms,
            "absteve": resultado.absteve,
        }
        self.eventos.append(evento)
        logger.info(json.dumps(evento, ensure_ascii=False))
        return resultado

    def health(self) -> dict[str, object]:
        return {
            "status": "ok" if self.chunks else "vazio",
            "versao": VERSAO,
            "documentos": len(self.documentos),
            "chunks": len(self.chunks),
        }
