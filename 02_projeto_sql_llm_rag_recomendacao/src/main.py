"""Demo do esqueleto — módulo 02."""

from pathlib import Path

from sql_rag import carregar_schema, responder

DB = Path(__file__).resolve().parent.parent / "data" / "loja.db"


def main() -> None:
    try:
        schema = carregar_schema(DB)
        print("Tabelas:", {nome: len(t.colunas) for nome, t in schema.items()})
        resposta = responder(DB, "Quais os 3 produtos com maior receita?")
        print(resposta)
    except NotImplementedError as exc:
        print(f"Ainda não implementado: {exc}")
        print("Sequência: TODO(2.1) → 2.2 → 2.3 → 2.4 → 2.5.")


if __name__ == "__main__":
    main()
