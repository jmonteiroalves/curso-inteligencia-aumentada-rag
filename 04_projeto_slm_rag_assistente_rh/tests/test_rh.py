"""Smoke tests da referência do módulo 04."""

import copy
import unittest
from dataclasses import asdict
from pathlib import Path

from solucao.rh_rag import (
    ATRIBUTOS_PROIBIDOS,
    CAMPOS_ANONIMOS,
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


class TestRH(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.vaga = carregar_vaga(DATA / "vaga.json")
        cls.brutos = carregar_candidatos(DATA / "curriculos.json")
        cls.anonimos = [anonimizar_candidato(c) for c in cls.brutos]
        cls.resultados = ranking(cls.anonimos, cls.vaga)

    def test_anonimizacao_sem_pii(self) -> None:
        dados = asdict(self.anonimos[0])
        self.assertFalse(set(dados) & ATRIBUTOS_PROIBIDOS)
        self.assertEqual(set(dados), set(CAMPOS_ANONIMOS))

    def test_vaga_valida(self) -> None:
        validar_vaga(self.vaga)
        self.assertAlmostEqual(sum(c.peso for c in self.vaga.criterios), 1.0)

    def test_ranking_esperado(self) -> None:
        self.assertEqual(self.resultados[0].candidato_id, "c01")
        self.assertTrue(all(0 <= r.score <= 100 for r in self.resultados))
        self.assertEqual(len(self.resultados), 6)

    def test_evidencias_por_criterio(self) -> None:
        top = self.resultados[0]
        self.assertEqual(len(top.evidencias), len(self.vaga.criterios))
        self.assertTrue(all(ev.evidencia for ev in top.evidencias))

    def test_score_invariante_a_atributos_protegidos(self) -> None:
        alterado = copy.deepcopy(self.brutos[0])
        alterado["genero"] = "X"
        alterado["faixa_etaria"] = "50+"
        score_a = pontuar_candidato(anonimizar_candidato(self.brutos[0]), self.vaga).score
        score_b = pontuar_candidato(anonimizar_candidato(alterado), self.vaga).score
        self.assertEqual(score_a, score_b)

    def test_cinco_perguntas_sem_atributos_sensiveis(self) -> None:
        perguntas = gerar_perguntas(self.resultados[0], self.vaga)
        self.assertEqual(len(perguntas), 5)
        texto = " ".join(p.pergunta for p in perguntas).lower()
        for termo in ("gênero", "genero", "idade", "religião", "religiao", "deficiência"):
            self.assertNotIn(termo, texto)

    def test_auditoria_taxas(self) -> None:
        auditoria = auditar_vies(self.resultados, self.brutos, top_n=2)
        self.assertIn("genero", auditoria)
        self.assertIn("faixa_etaria", auditoria)
        for grupo in auditoria["genero"].values():
            self.assertIn("taxa", grupo)
            self.assertIn("total", grupo)


if __name__ == "__main__":
    unittest.main()
