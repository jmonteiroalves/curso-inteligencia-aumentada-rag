"""Referência funcional de SQL + RAG + recomendação (módulo 02)."""

from __future__ import annotations

import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
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


def _norm(texto: str) -> str:
    import unicodedata

    decomposto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def carregar_schema(db_path: Path) -> dict[str, Tabela]:
    with sqlite3.connect(db_path) as con:
        nomes = [
            row[0]
            for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        schema = {}
        for nome in nomes:
            colunas = tuple(row[1] for row in con.execute(f'PRAGMA table_info("{nome}")'))
            schema[nome] = Tabela(nome, colunas)
    return schema


def selecionar_tabelas(pergunta: str, schema: dict[str, Tabela], top_n: int = 4) -> list[str]:
    tokens = set(_norm(pergunta).split())
    sinonimos = {
        "produtos": {"produto", "produtos", "item", "itens", "preco", "estoque", "catalogo"},
        "categorias": {"categoria", "categorias", "tipo"},
        "clientes": {"cliente", "clientes", "comprador", "cidade", "segmento"},
        "pedidos": {"pedido", "pedidos", "venda", "vendas", "receita", "faturamento", "status"},
        "itens_pedido": {"item", "itens", "quantidade", "receita", "venda", "vendas"},
        "avaliacoes": {"avaliacao", "avaliacoes", "nota", "media", "review", "feedback"},
    }
    scores: dict[str, float] = defaultdict(float)
    for nome, tabela in schema.items():
        alvo = set(_norm(nome + " " + " ".join(tabela.colunas)).split())
        scores[nome] += 2.0 * len(tokens & alvo)
        scores[nome] += 3.0 * len(tokens & sinonimos.get(nome, set()))
    if {"receita", "faturamento", "venda", "vendas", "pedido", "pedidos"} & tokens:
        for nome in ("produtos", "itens_pedido", "pedidos"):
            if nome in schema:
                scores[nome] += 4.0
    if {"avaliacao", "avaliacoes", "nota", "notas"} & tokens:
        for nome in ("avaliacoes", "produtos"):
            if nome in schema:
                scores[nome] += 2.0
    ordenadas = sorted(
        (nome for nome in schema if scores[nome] > 0), key=lambda n: (-scores[n], n)
    )
    return (ordenadas or ["produtos"])[:top_n]


def _numero_depois(pergunta: str, padrao: str, default: float) -> float:
    match = re.search(padrao + r"[^\d]{0,15}(\d+(?:[.,]\d+)?)", pergunta, re.IGNORECASE)
    if not match:
        return default
    return float(match.group(1).replace(",", "."))


def gerar_sql(pergunta: str, tabelas: list[str] | None = None) -> str:
    p = _norm(pergunta)
    if "recomend" in p:
        raise ValueError("Intenção de recomendação deve usar recomendar()")

    if "faturamento total" in p or "receita total" in p:
        return (
            "SELECT ROUND(SUM(i.quantidade * i.preco_unitario), 2) AS faturamento_total "
            "FROM pedidos ped JOIN itens_pedido i ON i.pedido_id = ped.id "
            "WHERE ped.status = 'pago'"
        )
    if "receita" in p or "mais vendido" in p or "maior faturamento" in p:
        return (
            "SELECT p.nome, ROUND(SUM(i.quantidade * i.preco_unitario), 2) AS receita "
            "FROM produtos p JOIN itens_pedido i ON i.produto_id = p.id "
            "JOIN pedidos ped ON ped.id = i.pedido_id "
            "WHERE ped.status = 'pago' "
            "GROUP BY p.id, p.nome ORDER BY receita DESC LIMIT 3"
        )
    if "nota" in p and ("media" in p or "avaliacao" in p):
        return (
            "SELECT p.nome, ROUND(AVG(a.nota), 2) AS nota_media, COUNT(a.id) AS avaliacoes "
            "FROM produtos p LEFT JOIN avaliacoes a ON a.produto_id = p.id "
            "GROUP BY p.id, p.nome ORDER BY nota_media DESC, avaliacoes DESC"
        )
    if "pedido" in p and "status" in p:
        return "SELECT status, COUNT(*) AS quantidade FROM pedidos GROUP BY status ORDER BY quantidade DESC"
    if "estoque" in p and ("preco" in p or "custa" in p or "abaixo" in p):
        preco = _numero_depois(pergunta, r"(?:menos de|abaixo de|ate|preco menor que)", 200.0)
        estoque = _numero_depois(pergunta, r"(?:estoque acima de|estoque maior que|mais de)", 10.0)
        return (
            "SELECT nome, preco, estoque FROM produtos "
            f"WHERE ativo = 1 AND preco < {preco:.2f} AND estoque > {estoque:.0f} "
            "ORDER BY preco ASC"
        )
    if "cliente" in p and "cidade" in p:
        return "SELECT cidade, COUNT(*) AS clientes FROM clientes GROUP BY cidade ORDER BY clientes DESC"
    return (
        "SELECT nome, preco, estoque FROM produtos "
        "WHERE ativo = 1 ORDER BY nome"
    )


def validar_sql(sql: str, schema: dict[str, Tabela], max_linhas: int = MAX_LINHAS) -> str:
    original = sql.strip()
    if not original:
        raise ValueError("SQL vazio")
    if COMENTARIOS.search(original):
        raise ValueError("Comentários não são permitidos")
    if ";" in original.rstrip(";"):
        raise ValueError("Múltiplos statements não são permitidos")
    sql_limpo = original.rstrip(";").strip()
    if not re.match(r"^select\b", sql_limpo, re.IGNORECASE):
        raise ValueError("Apenas SELECT é permitido")
    if TABELAS_PROIBIDAS.search(sql_limpo):
        raise ValueError("Comando potencialmente destrutivo bloqueado")
    tabelas = re.findall(r"\b(?:from|join)\s+\"?([a-zA-Z_][\w]*)\"?", sql_limpo, re.IGNORECASE)
    desconhecidas = [t for t in tabelas if t.lower() not in schema]
    if desconhecidas:
        raise ValueError(f"Tabela(s) não permitida(s): {desconhecidas}")
    if not re.search(r"\blimit\s+\d+\b", sql_limpo, re.IGNORECASE):
        sql_limpo += f" LIMIT {max_linhas}"
    return sql_limpo


def executar_sql(
    db_path: Path, sql: str, max_linhas: int = MAX_LINHAS
) -> tuple[tuple[str, ...], tuple[tuple[Any, ...], ...]]:
    uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        con.execute("PRAGMA query_only = ON")
        cursor = con.execute(sql)
        colunas = tuple(desc[0] for desc in cursor.description or ())
        linhas = tuple(cursor.fetchmany(max_linhas))
        return colunas, linhas
    finally:
        con.close()


def _formatar_linhas(colunas: tuple[str, ...], linhas: tuple[tuple[Any, ...], ...]) -> str:
    if not linhas:
        return "A consulta não retornou linhas."
    return "; ".join(
        ", ".join(f"{col}={valor}" for col, valor in zip(colunas, linha)) for linha in linhas[:5]
    )


def responder(db_path: Path, pergunta: str) -> RespostaSQL:
    schema = carregar_schema(db_path)
    if "recomend" in _norm(pergunta):
        match = re.search(r"cliente\s+(\d+)", pergunta, re.IGNORECASE)
        if not match:
            return RespostaSQL(pergunta, None, (), (), "Informe o ID do cliente.", "cliente ausente")
        recs = recomendar(db_path, int(match.group(1)))
        linhas = tuple((r.produto_id, r.nome, round(r.score, 2), "; ".join(r.motivos)) for r in recs)
        return RespostaSQL(
            pergunta,
            "RECOMENDADOR HÍBRIDO",
            ("produto_id", "nome", "score", "motivos"),
            linhas,
            f"Recomendações explicáveis para o cliente {match.group(1)}.",
        )

    tabelas = selecionar_tabelas(pergunta, schema)
    try:
        bruto = gerar_sql(pergunta, tabelas)
        seguro = validar_sql(bruto, schema)
        colunas, linhas = executar_sql(db_path, seguro)
    except (ValueError, sqlite3.Error) as exc:
        return RespostaSQL(pergunta, None, (), (), "Consulta bloqueada.", str(exc))

    return RespostaSQL(
        pergunta,
        seguro,
        colunas,
        linhas,
        f"Tabelas consideradas: {', '.join(tabelas)}. {_formatar_linhas(colunas, linhas)}",
    )


def recomendar(db_path: Path, cliente_id: int, top_n: int = 3) -> list[Recomendacao]:
    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        cliente = con.execute("SELECT id FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
        if not cliente:
            raise ValueError(f"Cliente {cliente_id} não encontrado")

        comprados = {
            row["produto_id"]
            for row in con.execute(
                "SELECT DISTINCT i.produto_id FROM pedidos p "
                "JOIN itens_pedido i ON i.pedido_id = p.id "
                "WHERE p.cliente_id = ? AND p.status != 'cancelado'",
                (cliente_id,),
            )
        }
        categorias = Counter()
        for pid in comprados:
            row = con.execute("SELECT categoria_id FROM produtos WHERE id = ?", (pid,)).fetchone()
            if row:
                categorias[row["categoria_id"]] += 1

        coocorrencia: Counter[int] = Counter()
        for pedido in con.execute(
            "SELECT DISTINCT pedido_id FROM itens_pedido WHERE produto_id IN "
            f"({','.join('?' * len(comprados)) or 'NULL'})",
            tuple(comprados),
        ):
            for row in con.execute(
                "SELECT produto_id FROM itens_pedido WHERE pedido_id = ?", (pedido["pedido_id"],)
            ):
                if row["produto_id"] not in comprados:
                    coocorrencia[row["produto_id"]] += 1

        produtos = con.execute(
            "SELECT p.id, p.nome, p.categoria_id, p.preco, "
            "COALESCE(AVG(a.nota), 0) AS nota, COUNT(a.id) AS qtd_avaliacoes "
            "FROM produtos p LEFT JOIN avaliacoes a ON a.produto_id = p.id "
            "WHERE p.ativo = 1 GROUP BY p.id"
        ).fetchall()

    if comprados:
        precos = [p["preco"] for p in produtos if p["id"] in comprados]
        preco_medio = sum(precos) / len(precos)
    else:
        preco_medio = 150.0

    candidatos: list[Recomendacao] = []
    for produto in produtos:
        pid = produto["id"]
        if pid in comprados:
            continue
        motivos: list[str] = []
        score = 0.0
        if coocorrencia[pid]:
            score += 3.0 * coocorrencia[pid]
            motivos.append(f"co-comprado em {coocorrencia[pid]} pedido(s)")
        if categorias[produto["categoria_id"]]:
            score += 1.5 * categorias[produto["categoria_id"]]
            motivos.append("categoria já comprada")
        if produto["nota"] >= 4.5:
            score += 0.8
            motivos.append("avaliação alta")
        elif produto["nota"] >= 4.0:
            score += 0.4
            motivos.append("boa avaliação")
        distancia = abs(produto["preco"] - preco_medio) / max(1.0, preco_medio)
        score += max(0.0, 0.6 - distancia * 0.6)
        if not motivos:
            motivos.append("afinidade de preço")
        candidatos.append(
            Recomendacao(pid, produto["nome"], round(score, 3), tuple(motivos))
        )

    candidatos.sort(key=lambda r: (-r.score, r.produto_id))
    return candidatos[:top_n]
