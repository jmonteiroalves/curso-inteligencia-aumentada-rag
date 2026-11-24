"""Demo da solução de referência do módulo 00."""

from pathlib import Path

from rag_solution import RAGIndex, carregar_documentos


def main() -> None:
    data_dir = Path(__file__).resolve().parent.parent / "data"
    indice = RAGIndex(carregar_documentos(data_dir)).index()
    print(f"Índice: {len(indice.chunks)} chunks\n")

    perguntas = [
        "Quantos dias de férias um colaborador tem direito?",
        "Qual é o tempo de primeira resposta para um incidente P1?",
        "Quando um alerta de vibração é aberto?",
        "Qual a capital da França?",
    ]
    for pergunta in perguntas:
        resposta = indice.answer(pergunta)
        print(f"P: {pergunta}")
        print(f"R: {resposta.texto}")
        print(f"   fontes={resposta.fontes} absteve={resposta.absteve} score={resposta.score:.3f}\n")


if __name__ == "__main__":
    main()
