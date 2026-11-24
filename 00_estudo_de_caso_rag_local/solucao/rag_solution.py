"""Referência funcional do RAG local (módulo 00).

Implementação determinística, sem LLM e sem dependências externas.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

DIMENSAO_EMBEDDING = 256
MAX_CHARS_CHUNK = 450
OVERLAP_CHARS = 80
MIN_SCORE = 0.18

STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "do", "da", "dos", "das", "em", "no", "na",
    "nos", "nas", "por", "para", "com", "sem", "que", "qual", "quais", "quando", "onde",
    "como", "quem", "e", "ou", "é", "são", "ser", "foi", "tem", "ter", "há", "ao", "aos",
    "se", "sua", "seu", "suas", "seus", "mais", "menos", "muito", "quanto", "quantos",
}


@dataclass(frozen=True)
class Document:
    id: str
    titulo: str
    texto: str
    fonte: str


@dataclass(frozen=True)
class Chunk:
    id: str
    doc_id: str
    texto: str
    fonte: str
    posicao: int


@dataclass(frozen=True)
class SearchHit:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class Answer:
    texto: str
    fontes: tuple[str, ...]
    absteve: bool
    score: float


def normalizar(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9\s]", " ", sem_acento)


def tokenizar(texto: str) -> list[str]:
    return [t for t in normalizar(texto).split() if len(t) > 2 and t not in STOPWORDS]


def carregar_documentos(data_dir: Path) -> list[Document]:
    documentos: list[Document] = []
    for caminho in sorted(data_dir.glob("*.md")):
        texto = caminho.read_text(encoding="utf-8").strip()
        primeira = texto.splitlines()[0] if texto else caminho.stem
        titulo = primeira.lstrip("# ").strip() or caminho.stem
        documentos.append(Document(caminho.stem, titulo, texto, caminho.name))
    if not documentos:
        raise FileNotFoundError(f"Nenhum Markdown encontrado em {data_dir}")
    return documentos


def chunk_text(
    texto: str,
    max_chars: int = MAX_CHARS_CHUNK,
    overlap: int = OVERLAP_CHARS,
) -> list[str]:
    """Janela deslizante por palavras, sem cortar tokens."""
    palavras = texto.split()
    if not palavras:
        return []
    if max_chars <= overlap:
        raise ValueError("max_chars deve ser maior que overlap")

    chunks: list[str] = []
    atuais: list[str] = []
    for palavra in palavras:
        candidato = " ".join([*atuais, palavra])
        if atuais and len(candidato) > max_chars:
            chunks.append(" ".join(atuais))
            cauda: list[str] = []
            for anterior in reversed(atuais):
                tentativa = " ".join([anterior, *cauda])
                if len(tentativa) > overlap:
                    break
                cauda.insert(0, anterior)
            atuais = [*cauda, palavra]
        else:
            atuais.append(palavra)
    if atuais and (not chunks or " ".join(atuais) != chunks[-1]):
        chunks.append(" ".join(atuais))
    return chunks


def embed_text(texto: str, dimensao: int = DIMENSAO_EMBEDDING) -> list[float]:
    """Feature hashing com sinal e normalização L2."""
    vetor = [0.0] * dimensao
    for token, frequencia in Counter(tokenizar(texto)).items():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        indice = int.from_bytes(digest[:4], "big") % dimensao
        sinal = 1.0 if digest[4] & 1 else -1.0
        vetor[indice] += sinal * (1.0 + math.log(frequencia))
    norma = math.sqrt(sum(v * v for v in vetor))
    if norma:
        vetor = [v / norma for v in vetor]
    return vetor


def similaridade_cosseno(a: Sequence[float], b: Sequence[float]) -> float:
    norma_a = math.sqrt(sum(x * x for x in a))
    norma_b = math.sqrt(sum(x * x for x in b))
    if not norma_a or not norma_b:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (norma_a * norma_b)


class RAGIndex:
    def __init__(
        self,
        documentos: Iterable[Document],
        max_chars: int = MAX_CHARS_CHUNK,
        overlap: int = OVERLAP_CHARS,
    ) -> None:
        self.documentos = list(documentos)
        self.max_chars = max_chars
        self.overlap = overlap
        self.chunks: list[Chunk] = []
        self.vetores: list[list[float]] = []

    def index(self) -> "RAGIndex":
        self.chunks = []
        self.vetores = []
        for documento in self.documentos:
            for posicao, texto in enumerate(
                chunk_text(documento.texto, self.max_chars, self.overlap)
            ):
                chunk = Chunk(
                    id=f"{documento.id}:{posicao}",
                    doc_id=documento.id,
                    texto=texto,
                    fonte=documento.fonte,
                    posicao=posicao,
                )
                self.chunks.append(chunk)
                self.vetores.append(embed_text(texto))
        return self

    def search(
        self, pergunta: str, top_k: int = 3, min_score: float = MIN_SCORE
    ) -> list[SearchHit]:
        if not self.chunks:
            raise RuntimeError("Chame .index() antes de buscar")
        tokens_pergunta = set(tokenizar(pergunta))
        vetor_pergunta = embed_text(pergunta)
        hits: list[SearchHit] = []
        for chunk, vetor in zip(self.chunks, self.vetores):
            tokens_chunk = set(tokenizar(chunk.texto))
            lexical = (
                len(tokens_pergunta & tokens_chunk) / len(tokens_pergunta)
                if tokens_pergunta
                else 0.0
            )
            score = 0.7 * max(0.0, similaridade_cosseno(vetor_pergunta, vetor)) + 0.3 * lexical
            if score >= min_score:
                hits.append(SearchHit(chunk, score))
        hits.sort(key=lambda h: (-h.score, h.chunk.id))
        return hits[:top_k]

    def answer(
        self, pergunta: str, top_k: int = 3, min_score: float = MIN_SCORE
    ) -> Answer:
        hits = self.search(pergunta, top_k=top_k, min_score=min_score)
        if not hits:
            return Answer(
                "Não encontrei evidência suficiente no corpus para responder.",
                (),
                True,
                0.0,
            )

        tokens_pergunta = set(tokenizar(pergunta))
        candidatas: list[tuple[float, str, str]] = []
        for hit in hits[:2]:
            frases = re.split(r"(?<=[.!?])\s+", hit.chunk.texto.replace("\n", " "))
            for frase in frases:
                tokens = set(tokenizar(frase))
                overlap = len(tokens_pergunta & tokens) / max(1, len(tokens_pergunta))
                if overlap:
                    candidatas.append((overlap + 0.05 * hit.score, frase.strip(), hit.chunk.fonte))
        candidatas.sort(key=lambda item: -item[0])

        selecionadas: list[tuple[str, str]] = []
        usados = 0
        for _, frase, fonte in candidatas:
            if not frase or any(frase == f for f, _ in selecionadas):
                continue
            if usados + len(frase) > 420 and selecionadas:
                break
            selecionadas.append((frase, fonte))
            usados += len(frase)
            if len(selecionadas) == 2:
                break
        if not selecionadas:
            selecionadas = [(hits[0].chunk.texto[:400], hits[0].chunk.fonte)]

        fontes = tuple(dict.fromkeys(fonte for _, fonte in selecionadas))
        texto = " ".join(f"[{fonte}] {frase}" for frase, fonte in selecionadas)
        return Answer(texto, fontes, False, hits[0].score)


def responder(pergunta: str, data_dir: Path) -> Answer:
    """Atalho usado pelos demos e testes."""
    indice = RAGIndex(carregar_documentos(data_dir)).index()
    return indice.answer(pergunta)
