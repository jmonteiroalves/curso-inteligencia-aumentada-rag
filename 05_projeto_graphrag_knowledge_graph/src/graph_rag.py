"""GraphRAG — esqueleto do aluno (módulo 05).

Pipeline:
textos -> entidades -> triplas -> grafo -> caminhos -> resposta + evidências.

Um gazetteer é usado como baseline determinístico de NER/entity linking. Em produção,
substitua a extração por um modelo, mas preserve o contrato de evidência e fonte.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

MAX_HOPS = 3


@dataclass(frozen=True)
class Entidade:
    nome: str
    tipo: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Tripla:
    sujeito: str
    relacao: str
    objeto: str
    fonte: str
    evidencia: str


@dataclass(frozen=True)
class Caminho:
    nos: tuple[str, ...]
    relacoes: tuple[str, ...]
    triplas: tuple[Tripla, ...]


@dataclass(frozen=True)
class Trecho:
    fonte: str
    texto: str
    score: float


@dataclass(frozen=True)
class RespostaGraph:
    pergunta: str
    resposta: str
    absteve: bool
    score: float
    caminhos: tuple[str, ...]
    evidencias: tuple[str, ...]
    fontes: tuple[str, ...]
    contexto_textual: tuple[Trecho, ...] = ()


def normalizar(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"[^a-z0-9\s]", " ", "".join(c for c in decomposto if not unicodedata.combining(c)))


def carregar_gazetteer(data_dir: Path) -> list[Entidade]:
    dados = json.loads((data_dir / "entidades.json").read_text(encoding="utf-8"))
    return [
        Entidade(item["nome"], item["tipo"], tuple(item.get("aliases", [item["nome"]])))
        for item in dados["entidades"]
    ]


def carregar_textos(data_dir: Path) -> list[tuple[str, str]]:
    return [
        (caminho.name, caminho.read_text(encoding="utf-8").strip())
        for caminho in sorted((data_dir / "textos").glob("*.txt"))
    ]


class KnowledgeGraph:
    """Grafo dirigido com adjacência de entrada/saída."""

    def __init__(self) -> None:
        self.entidades: dict[str, Entidade] = {}
        self.triplas: list[Tripla] = []
        self._saida: dict[str, list[Tripla]] = defaultdict(list)
        self._entrada: dict[str, list[Tripla]] = defaultdict(list)

    def adicionar_entidade(self, entidade: Entidade) -> None:
        self.entidades.setdefault(entidade.nome, entidade)

    def adicionar_tripla(self, tripla: Tripla) -> None:
        """TODO(5.3): deduplique por (sujeito, relação, objeto), indexe entrada/saída
        e garanta que os nós existam (tipo preservado)."""
        # TODO(5.3): implemente adicionar_tripla
        raise NotImplementedError("TODO(5.3): implemente adicionar_tripla")

    def vizinhos(self, nome: str) -> list[tuple[Tripla, str]]:
        if nome not in self.entidades:
            return []
        itens = [(t, "saida") for t in self._saida.get(nome, [])]
        itens += [(t, "entrada") for t in self._entrada.get(nome, [])]
        return itens

    def grau(self, nome: str) -> int:
        return len(self._saida.get(nome, [])) + len(self._entrada.get(nome, []))

    def comunidades(self) -> list[list[str]]:
        """TODO(5.6): componentes conectados ignorando direção."""
        # TODO(5.6): implemente comunidades
        raise NotImplementedError("TODO(5.6): implemente comunidades")


def extrair_entidades(texto: str, gazetteer: list[Entidade]) -> list[Entidade]:
    """TODO(5.1): encontre aliases/nomes no texto, canonicalize e ordene por posição."""
    # TODO(5.1): implemente extrair_entidades
    raise NotImplementedError("TODO(5.1): implemente extrair_entidades")


def extrair_triplas(texto: str, fonte: str, gazetteer: list[Entidade]) -> list[Tripla]:
    """TODO(5.2): aplique padrões de relação em cada frase.

    Relações mínimas: trabalha_em, lidera, usa, depende_de, integra, financia,
    parceira_de, fornece_para, mentora, participa_de, sede_em.
    Guarde a frase como evidência e o arquivo como fonte.
    """
    # TODO(5.2): implemente extrair_triplas
    raise NotImplementedError("TODO(5.2): implemente extrair_triplas")


def construir_grafo(data_dir: Path) -> KnowledgeGraph:
    """TODO(5.3): carregue textos/gazetteer, registre entidades e triplas."""
    # TODO(5.3): implemente construir_grafo
    raise NotImplementedError("TODO(5.3): implemente construir_grafo")


def caminhos(grafo: KnowledgeGraph, inicio: str, max_hops: int = MAX_HOPS) -> list[Caminho]:
    """TODO(5.4): enumere caminhos simples (sem repetir nó) até max_hops."""
    # TODO(5.4): implemente caminhos
    raise NotImplementedError("TODO(5.4): implemente caminhos")


def responder(grafo: KnowledgeGraph, pergunta: str) -> RespostaGraph:
    """TODO(5.4): use âncoras, tipo esperado e relações mencionadas para pontuar caminhos.

    Devolva resposta com caminho(s), evidências e fontes; abstenha se não houver caminho.
    """
    # TODO(5.4): implemente responder
    raise NotImplementedError("TODO(5.4): implemente responder")


def recuperar_contexto_textual(pergunta: str, data_dir: Path, top_k: int = 3) -> list[Trecho]:
    """TODO(5.5): ranqueie frases por sobreposição lexical com a pergunta."""
    # TODO(5.5): implemente recuperar_contexto_textual
    raise NotImplementedError("TODO(5.5): implemente recuperar_contexto_textual")


def responder_hibrido(grafo: KnowledgeGraph, pergunta: str, data_dir: Path) -> RespostaGraph:
    """TODO(5.5): combine o caminho do grafo com os melhores trechos textuais."""
    # TODO(5.5): implemente responder_hibrido
    raise NotImplementedError("TODO(5.5): implemente responder_hibrido")


def exportar_cypher(grafo: KnowledgeGraph) -> str:
    """TODO(5.6): gere MERGE idempotente para nós e arestas, com labels seguros."""
    # TODO(5.6): implemente exportar_cypher
    raise NotImplementedError("TODO(5.6): implemente exportar_cypher")
