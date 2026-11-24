"""Demo do esqueleto do módulo 00.

Rode a partir da pasta do módulo:
    python3 src/main.py
"""

from pathlib import Path

from rag import RAGIndex, carregar_documentos


def main() -> None:
    data_dir = Path(__file__).resolve().parent.parent / "data"
    documentos = carregar_documentos(data_dir)
    print(f"Documentos: {len(documentos)}")

    indice = RAGIndex(documentos)
    try:
        indice.index()
    except NotImplementedError as exc:
        print(f"\nAinda não implementado: {exc}")
        print("Abra src/rag.py e comece pelo TODO(0.1), depois reinicie o pipeline.")
        return

    for pergunta in (
        "Quantos dias de férias eu tenho?",
        "Qual o prazo de resposta de um incidente P1?",
        "Qual a capital da França?",
    ):
        resposta = indice.answer(pergunta)
        print(f"\nP: {pergunta}")
        print(f"R: {resposta.texto}")
        print(f"Fontes: {resposta.fontes} | absteve={resposta.absteve} | score={resposta.score:.3f}")


if __name__ == "__main__":
    main()
