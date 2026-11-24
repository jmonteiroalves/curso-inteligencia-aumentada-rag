"""Avaliação de SQL e recomendação (módulo 02)."""

from __future__ import annotations

from pathlib import Path

from sql_rag import carregar_schema, recomendar, responder, validar_sql

DB = Path(__file__).resolve().parent.parent / "data" / "loja.db"

CASOS = [
    ("Quais os 3 produtos com maior receita?", "receita"),
    ("Quais produtos custam menos de R$ 150 e têm estoque acima de 30?", "preco"),
    ("Quantos pedidos existem por status?", "status"),
    ("Qual a nota média por produto?", "nota_media"),
    ("Qual o faturamento total dos pedidos pagos?", "faturamento_total"),
]

ATAQUES = [
    "DROP TABLE produtos",
    "DELETE FROM produtos",
    "SELECT * FROM sqlite_master",
    "SELECT * FROM produtos; DELETE FROM produtos",
    "PRAGMA table_info(produtos)",
    "SELECT * FROM tabela_inexistente",
]


def main() -> None:
    schema = carregar_schema(DB)
    sucessos = 0
    for pergunta, coluna in CASOS:
        resposta = responder(DB, pergunta)
        ok = resposta.erro is None and coluna in resposta.colunas
        sucessos += int(ok)
        print(f"{'ok' if ok else 'FALHOU'} | {pergunta} | colunas={resposta.colunas}")

    bloqueados = 0
    for ataque in ATAQUES:
        try:
            validar_sql(ataque, schema)
        except ValueError:
            bloqueados += 1
    print(f"\nSQL útil: {sucessos}/{len(CASOS)}")
    print(f"Guardrails: {bloqueados}/{len(ATAQUES)} bloqueados")

    recs = recomendar(DB, 1, top_n=3)
    relevantes = {2, 4, 6}
    precisao = len(relevantes & {r.produto_id for r in recs}) / 3
    print(f"precision@3 cliente 1: {precisao:.2f}")
    print("top-3:", [(r.produto_id, r.nome, r.score) for r in recs])

    if sucessos < len(CASOS) or bloqueados < len(ATAQUES) or precisao < 0.33:
        raise SystemExit("Critério de avaliação não atingido")


if __name__ == "__main__":
    main()
