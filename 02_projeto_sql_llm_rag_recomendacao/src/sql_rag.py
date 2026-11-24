"""SQL + RAG + recomendação — esqueleto do aluno (módulo 02).

Regra de ouro: o LLM pode *sugerir* SQL, mas jamais executá-lo sem validação.
Toda consulta é SELECT-only, contra tabelas conhecidas, com LIMIT e conexão read-only.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MAX_LINHAS = 50
TABELAS_PROIBIDAS = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|truncate|attach|detach|pragma|"
    r"vacuum|reindex|grant|revoke|load_extension)\b",
    re.IGNORECASE,
)
COMENTARIOS = re.compile(r"(--|/\*|\*/)")


@dataclass(frozen=True)
class Tabela:
    nome: str
    colunas: tuple[str, ...]


@dataclass(frozen=True)
class RespostaSQL:
    pergunta: str
    sql: str | None
    colunas: tuple[str, ...]
    linhas: tuple[tuple[Any, ...], ...]
    explicacao: str
    erro: str | None = None


@dataclass(frozen=True)
class Recomendacao:
    produto_id: int
    nome: str
    score: float
    motivos: tuple[str, ...]


PROMPT_TEXT_TO_SQL = """Você traduz perguntas para SQLite somente leitura.
Regras invioláveis:
- gere apenas SELECT;
- use somente as tabelas: {tabelas};
- nunca use PRAGMA, ATTACH, DDL ou DML;
- retorne no máximo 50 linhas;
- se faltar informação, peça esclarecimento em vez de inventar.
Pergunta: {pergunta}
SQL:"""


def carregar_schema(db_path: Path) -> dict[str, Tabela]:
    """Lê nomes de tabelas e colunas do SQLite.

    TODO(2.1): consulte `sqlite_master` e `PRAGMA table_info` de forma segura.
    Ignore tabelas internas (`sqlite_*`).
    """
    # TODO(2.1): implemente carregar_schema
    raise NotImplementedError("TODO(2.1): implemente carregar_schema")


def selecionar_tabelas(pergunta: str, schema: dict[str, Tabela], top_n: int = 4) -> list[str]:
    """Schema linking determinístico.

    TODO(2.2): pontue tabelas por tokens da pergunta e sinônimos de domínio
    (produto/preço/estoque → produtos; pedido/receita → pedidos+itens; etc.).
    Retorne as `top_n` mais relevantes, nunca uma tabela desconhecida.
    """
    # TODO(2.2): implemente selecionar_tabelas
    raise NotImplementedError("TODO(2.2): implemente selecionar_tabelas")


def gerar_sql(pergunta: str, tabelas: list[str] | None = None) -> str:
    """Gera SQL a partir de templates de intenção.

    TODO(2.3): cubra pelo menos:
    - receita por produto (pedidos pagos);
    - faturamento total;
    - produtos por preço/estoque;
    - pedidos por status;
    - nota média por produto.
    Este gerador é o fallback determinístico. Um LLM pode substituí-lo, mas a
    validação continua obrigatória.
    """
    # TODO(2.3): implemente gerar_sql
    raise NotImplementedError("TODO(2.3): implemente gerar_sql")


def validar_sql(
    sql: str, schema: dict[str, Tabela], max_linhas: int = MAX_LINHAS
) -> str:
    """Aplica guardrails e devolve SQL normalizado com LIMIT.

    TODO(2.3):
    - rejeite vazio, comentários, múltiplos statements e qualquer DML/DDL;
    - exija começar com SELECT;
    - extraia tabelas após FROM/JOIN e rejeite desconhecidas;
    - adicione `LIMIT {max_linhas}` se não houver limite.
    """
    # TODO(2.3): implemente validar_sql
    raise NotImplementedError("TODO(2.3): implemente validar_sql")


def executar_sql(
    db_path: Path, sql: str, max_linhas: int = MAX_LINHAS
) -> tuple[tuple[str, ...], tuple[tuple[Any, ...], ...]]:
    """Executa em conexão somente leitura.

    TODO(2.4): use URI `file:...?mode=ro`, `PRAGMA query_only=ON`,
    `fetchmany(max_linhas)` e feche a conexão em `finally`.
    """
    # TODO(2.4): implemente executar_sql
    raise NotImplementedError("TODO(2.4): implemente executar_sql")


def responder(db_path: Path, pergunta: str) -> RespostaSQL:
    """Orquestra schema linking → SQL → validação → execução → explicação.

    TODO(2.4): detecte intenção de recomendação e chame `recomendar`.
    Em erro de validação, retorne `RespostaSQL` com `erro` preenchido, sem executar.
    """
    # TODO(2.4): implemente responder
    raise NotImplementedError("TODO(2.4): implemente responder")


def recomendar(db_path: Path, cliente_id: int, top_n: int = 3) -> list[Recomendacao]:
    """Recomendação híbrida para um cliente.

    TODO(2.5):
    - exclua itens já comprados;
    - some co-compra (produtos presentes nos mesmos pedidos);
    - acrescente afinidade de categoria, nota média e faixa de preço;
    - devolva score e motivos explicáveis.
    """
    # TODO(2.5): implemente recomendar
    raise NotImplementedError("TODO(2.5): implemente recomendar")
