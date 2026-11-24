"""Núcleo do RAG local — esqueleto do aluno.

CONTRATO
--------
Este módulo deve transformar documentos Markdown em chunks, indexá-los por similaridade e
responder perguntas **somente** com evidências recuperadas. Não há LLM nesta etapa.

ANALOGIA
--------
- `Document` é o livro.
- `Chunk` é a ficha de estudo.
- `embed_text` é o mapa de proximidade semântica.
- `RAGIndex.search` é o bibliotecário pegando as fichas mais próximas.
- `RAGIndex.answer` é o parecer final, com nota de rodapé.

COMO VALIDAR
------------
Execute ``python3 src/main.py`` e, depois de cada TODO, compare com
``python3 solucao/run_demo.py``. Não copie a solução antes de tentar.
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
    """Documento de origem, carregado do disco."""

    id: str
    titulo: str
    texto: str
    fonte: str


@dataclass(frozen=True)
class Chunk:
    """Unidade recuperável. `fonte` é o que aparecerá na citação."""

    id: str
    doc_id: str
    texto: str
    fonte: str
    posicao: int


@dataclass(frozen=True)
class SearchHit:
    """Resultado de busca com score normalizado em [0, 1]."""

    chunk: Chunk
    score: float


@dataclass(frozen=True)
class Answer:
    """Resposta apoiada em evidências ou abstenção explícita."""

    texto: str
    fontes: tuple[str, ...]
    absteve: bool
    score: float


def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e apenas letras/números/espaços."""
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9\s]", " ", sem_acento)


def tokenizar(texto: str) -> list[str]:
    """Tokenização simples para o corpus sintético em português."""
    return [t for t in normalizar(texto).split() if len(t) > 2 and t not in STOPWORDS]


def carregar_documentos(data_dir: Path) -> list[Document]:
    """Carrega todos os `.md` do diretório, usando o primeiro `#` como título."""
    documentos: list[Document] = []
    for caminho in sorted(data_dir.glob("*.md")):
        texto = caminho.read_text(encoding="utf-8").strip()
        primeira = texto.splitlines()[0] if texto else caminho.stem
        titulo = primeira.lstrip("# ").strip() or caminho.stem
        documentos.append(
            Document(id=caminho.stem, titulo=titulo, texto=texto, fonte=caminho.name)
        )
    if not documentos:
        raise FileNotFoundError(f"Nenhum Markdown encontrado em {data_dir}")
    return documentos


def chunk_text(
    texto: str,
    max_chars: int = MAX_CHARS_CHUNK,
    overlap: int = OVERLAP_CHARS,
) -> list[str]:
    """Divide o texto em janelas de palavras com overlap.

    Regras:
    - nenhuma palavra pode ser cortada;
    - cada chunk deve ter no máximo `max_chars` (salvo palavra isolada maior);
    - o próximo chunk começa com o final do anterior (até `overlap` chars);
    - não produza chunks vazios ou idênticos consecutivos.

    TODO(0.1): implemente a janela deslizante por palavras.
    """
    # TODO(0.1): implemente chunk_text
    raise NotImplementedError("TODO(0.1): implemente chunk_text")


def embed_text(texto: str, dimensao: int = DIMENSAO_EMBEDDING) -> list[float]:
    """Gera um embedding determinístico via feature hashing.

    Passos:
    1. tokenize e conte frequências;
    2. para cada token, use `hashlib.blake2b` para escolher índice e sinal;
    3. some `1 + log(frequência)` na dimensão escolhida;
    4. normalize o vetor em L2 (norma 1) para que o cosseno seja estável.

    TODO(0.2): implemente o hashing e a normalização.
    """
    # TODO(0.2): implemente embed_text
    raise NotImplementedError("TODO(0.2): implemente embed_text")


def similaridade_cosseno(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosseno entre dois vetores; retorna 0 se algum tiver norma zero."""
    norma_a = math.sqrt(sum(x * x for x in a))
    norma_b = math.sqrt(sum(x * x for x in b))
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (norma_a * norma_b)


class RAGIndex:
    """Índice em memória: chunks, vetores e busca híbrida determinística."""

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
        """Cria chunks, calcula embeddings e deixa o índice pronto para busca.

        TODO(0.2): popule `self.chunks` e `self.vetores` de forma alinhada.
        Gere IDs estáveis como ``f"{doc.id}:{posicao}"``.
        """
        # TODO(0.2): implemente RAGIndex.index
        raise NotImplementedError("TODO(0.2): implemente RAGIndex.index")

    def search(self, pergunta: str, top_k: int = 3, min_score: float = MIN_SCORE) -> list[SearchHit]:
        """Retorna os melhores chunks acima de `min_score`.

        Score sugerido: ``0.7 * cosseno + 0.3 * overlap_lexical``.
        O overlap lexical é a fração de tokens da pergunta presentes no chunk.

        TODO(0.3): implemente a busca e a ordenação.
        """
        # TODO(0.3): implemente RAGIndex.search
        raise NotImplementedError("TODO(0.3): implemente RAGIndex.search")

    def answer(self, pergunta: str, top_k: int = 3, min_score: float = MIN_SCORE) -> Answer:
        """Responde de forma extrativa, citando fontes, ou abstém.

        TODO(0.4):
        - recupere hits;
        - se não houver hit ou o melhor score < min_score, retorne abstenção;
        - selecione até 2 frases com maior sobreposição de tokens;
        - prefixe cada frase com ``[fonte]`` e deduplique fontes;
        - nunca invente uma fonte.
        """
        # TODO(0.4): implemente RAGIndex.answer
        raise NotImplementedError("TODO(0.4): implemente RAGIndex.answer")


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parent.parent
    docs = carregar_documentos(raiz / "data")
    print(f"Corpus carregado: {len(docs)} documentos")
    for doc in docs:
        print(f"- {doc.fonte}: {doc.titulo} ({len(doc.texto)} chars)")
    print("\nPróximo passo: implemente TODO(0.1) em chunk_text.")
