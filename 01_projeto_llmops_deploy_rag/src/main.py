"""Demo do esqueleto — módulo 01."""

from pathlib import Path

from rag_core import RagService

RAIZ = Path(__file__).resolve().parent.parent


def main() -> None:
    servico = RagService(RAIZ / "data")
    print("Health inicial:", servico.health())
    try:
        relatorio = servico.carregar_diretorio()
        print("Ingestão:", relatorio)
        print("Health:", servico.health())
        print(servico.query("Quantos usuários o plano Pro permite?").to_dict())
    except NotImplementedError as exc:
        print(f"\nAinda não implementado: {exc}")
        print("Sequência: TODO(1.2) → TODO(1.3) → TODO(1.5) → API/Docker.")


if __name__ == "__main__":
    main()
