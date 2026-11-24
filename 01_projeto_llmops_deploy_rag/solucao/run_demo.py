"""Demo da solução de referência — módulo 01."""

from pathlib import Path

from rag_core import RagService

RAIZ = Path(__file__).resolve().parent.parent


def main() -> None:
    servico = RagService(RAIZ / "data")
    print("Primeira ingestão:", servico.carregar_diretorio())
    print("Segunda ingestão:", servico.carregar_diretorio())
    print("Health:", servico.health())
    for pergunta in (
        "Quantos usuários o plano Pro permite?",
        "Qual é o SLA de um incidente P1?",
        "Qual é a política de reembolso de passagens?",
    ):
        resultado = servico.query(pergunta)
        print(f"\nP: {pergunta}")
        print(f"R: {resultado.resposta}")
        print(
            f"fontes={resultado.fontes} absteve={resultado.absteve} "
            f"latencia={resultado.latencia_ms}ms request={resultado.request_id}"
        )
    print(f"\nEventos observáveis: {len(servico.eventos)}")


if __name__ == "__main__":
    main()
