"""Demo do esqueleto — módulo 04."""

from pathlib import Path

from rh_rag import carregar_candidatos, carregar_vaga, validar_vaga

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    vaga = carregar_vaga(DATA / "vaga.json")
    candidatos = carregar_candidatos(DATA / "curriculos.json")
    print(f"Vaga: {vaga.titulo} | candidatos: {len(candidatos)}")
    try:
        validar_vaga(vaga)
        print("Vaga válida")
    except NotImplementedError as exc:
        print(f"\nAinda não implementado: {exc}")
        print("Sequência: TODO(4.1) → 4.2 → 4.3 → 4.4 → 4.5 → 4.6.")


if __name__ == "__main__":
    main()
