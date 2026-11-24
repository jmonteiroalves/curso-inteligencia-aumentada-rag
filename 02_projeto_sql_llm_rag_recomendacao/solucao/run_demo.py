"""Demo da solução de referência — módulo 02."""

from pathlib import Path

from sql_rag import carregar_schema, recomendar, responder

DB = Path(__file__).resolve().parent.parent / "data" / "loja.db"


def main() -> None:
    print("Tabelas:", {nome: len(t.colunas) for nome, t in carregar_schema(DB).items()})
    perguntas = [
        "Quais os 3 produtos com maior receita?",
        "Quais produtos custam menos de R$ 150 e têm estoque acima de 30?",
        "Quantos pedidos existem por status?",
        "Qual a nota média por produto?",
        "Qual o faturamento total dos pedidos pagos?",
        "Recomende produtos para o cliente 1",
    ]
    for pergunta in perguntas:
        resposta = responder(DB, pergunta)
        print(f"\nP: {pergunta}")
        print(f"SQL: {resposta.sql}")
        print(f"Linhas: {resposta.linhas}")
        if resposta.erro:
            print(f"ERRO: {resposta.erro}")

    print("\nRecomendações cliente 1:")
    for rec in recomendar(DB, 1, top_n=3):
        print(f"- {rec.nome} score={rec.score} motivos={rec.motivos}")


if __name__ == "__main__":
    main()
