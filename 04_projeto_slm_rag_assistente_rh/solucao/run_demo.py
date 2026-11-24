"""Demo da solução de referência — módulo 04."""

from pathlib import Path

from rh_rag import (
    anonimizar_candidato,
    auditar_vies,
    carregar_candidatos,
    carregar_vaga,
    gerar_perguntas,
    ranking,
    validar_vaga,
)

DATA = Path(__file__).resolve().parent.parent / "data"


def main() -> None:
    vaga = carregar_vaga(DATA / "vaga.json")
    brutos = carregar_candidatos(DATA / "curriculos.json")
    validar_vaga(vaga)
    anonimos = [anonimizar_candidato(c) for c in brutos]
    resultados = ranking(anonimos, vaga)

    print(f"Vaga: {vaga.titulo} | {len(vaga.criterios)} critérios")
    for resultado in resultados:
        print(f"\n{resultado.candidato_id}: {resultado.score}/100 lacunas={resultado.lacunas}")
        for ev in resultado.evidencias:
            print(f"  - {ev.criterio}: {ev.score:.2f} | {ev.evidencia[:110]}")

    top = resultados[0]
    print(f"\nPerguntas para {top.candidato_id}:")
    for pergunta in gerar_perguntas(top, vaga):
        print(f"  [{pergunta.tipo}] {pergunta.pergunta}")

    print("\nAuditoria de seleção (top 2):")
    print(auditar_vies(resultados, brutos, top_n=2))


if __name__ == "__main__":
    main()
