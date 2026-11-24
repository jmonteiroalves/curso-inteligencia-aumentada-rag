"""Avaliação do assistente de RH (módulo 04)."""

from __future__ import annotations

import copy
import json
from dataclasses import asdict
from pathlib import Path

from rh_rag import (
    ATRIBUTOS_PROIBIDOS,
    anonimizar_candidato,
    auditar_vies,
    carregar_candidatos,
    carregar_vaga,
    gerar_perguntas,
    pontuar_candidato,
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

    print("== Ranking ==")
    for r in resultados:
        print(f"{r.candidato_id:<4} {r.score:>5}/100 lacunas={len(r.lacunas)}")

    pii = set(asdict(anonimos[0])) & ATRIBUTOS_PROIBIDOS
    perguntas = gerar_perguntas(resultados[0], vaga)
    perguntas_texto = " ".join(p.pergunta for p in perguntas).lower()
    termos_sensiveis = ["gênero", "genero", "idade", "religião", "religiao", "estado civil", "deficiência"]

    base = copy.deepcopy(brutos[0])
    alterado = copy.deepcopy(brutos[0])
    alterado["genero"] = "X"
    alterado["faixa_etaria"] = "50+"
    score_base = pontuar_candidato(anonimizar_candidato(base), vaga).score
    score_alt = pontuar_candidato(anonimizar_candidato(alterado), vaga).score

    auditoria = auditar_vies(resultados, brutos, top_n=2)
    print("\n== Evidências do top-1 ==")
    for ev in resultados[0].evidencias:
        print(f"- {ev.criterio}: {ev.score:.2f} | {ev.evidencia[:100]}")
    print("\n== Perguntas ==")
    for p in perguntas:
        print(f"- [{p.tipo}] {p.pergunta}")
    print("\n== Auditoria ==")
    print(json.dumps(auditoria, ensure_ascii=False, indent=2))

    print("\n== Invariância a atributos protegidos ==")
    print(f"score original={score_base} alterado={score_alt}")

    falhas = []
    if resultados[0].candidato_id != "c01":
        falhas.append("top-1 inesperado")
    if pii:
        falhas.append(f"PII vazou: {pii}")
    if len(perguntas) != 5:
        falhas.append("perguntas != 5")
    if any(t in perguntas_texto for t in termos_sensiveis):
        falhas.append("pergunta contém atributo sensível")
    if score_base != score_alt:
        falhas.append("score mudou com atributo protegido")
    if not auditoria.get("genero"):
        falhas.append("auditoria de gênero ausente")

    print("\nLimitações: dataset sintético e minúsculo; auditoria descritiva não prova justiça.")
    if falhas:
        raise SystemExit("Falhas: " + "; ".join(falhas))
    print("Critérios de avaliação atingidos.")


if __name__ == "__main__":
    main()
