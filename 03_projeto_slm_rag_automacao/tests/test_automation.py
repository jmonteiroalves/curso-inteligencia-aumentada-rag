"""Smoke tests da referência do módulo 03."""

import unittest
from pathlib import Path

from solucao.automation import (
    PlanoAcao,
    Solicitacao,
    carregar_solicitacoes,
    carregar_sops,
    classificar,
    executar,
    montar_plano,
    recuperar_sop,
    simular,
    validar_plano,
)

DATA = Path(__file__).resolve().parent.parent / "data"


class TestAutomacao(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sops = carregar_sops(DATA)
        cls.solicitacoes = carregar_solicitacoes(DATA)

    def test_classificacao_rotulada(self) -> None:
        acertos = 0
        for solicitacao in self.solicitacoes:
            acertos += int(classificar(solicitacao, self.sops).intencao == solicitacao.intencao_esperada)
        self.assertGreaterEqual(acertos, 7)

    def test_ambiguo_escala(self) -> None:
        s08 = next(s for s in self.solicitacoes if s.id == "s08")
        self.assertEqual(classificar(s08, self.sops).intencao, "desconhecido")

    def test_retrieval_sop(self) -> None:
        s01 = next(s for s in self.solicitacoes if s.id == "s01")
        sop, _ = recuperar_sop(s01.texto, self.sops)
        self.assertEqual(sop.arquivo, "reembolso.md")

    def test_aprovacao_acima_do_limite(self) -> None:
        caro = Solicitacao("x", "Reembolso de hotel R$ 620 com nota fiscal", valor=620.0)
        plano, resultado = executar(caro, self.sops)
        self.assertTrue(plano.requer_aprovacao)
        self.assertEqual(resultado.status, "aguardando_aprovacao")
        self.assertNotIn("criar_reembolso", plano.ferramentas)
        self.assertIn("escalar_gestor", plano.ferramentas)
        self.assertFalse(resultado.sucesso)

    def test_ferramenta_inventada_rejeitada(self) -> None:
        solicitacao = self.solicitacoes[0]
        sop = self.sops["reembolso"]
        plano = montar_plano(solicitacao, classificar(solicitacao, self.sops), sop)
        invalido = PlanoAcao(
            plano.solicitacao_id,
            plano.intencao,
            plano.sop_id,
            plano.confianca,
            plano.passos,
            ("validar_despesa", "transferir_dinheiro"),
            False,
            None,
            plano.risco,
        )
        with self.assertRaises(ValueError):
            validar_plano(invalido, self.sops)

    def test_simulacao_nao_executa_mutacao_sem_aprovacao(self) -> None:
        caro = Solicitacao("x", "Reembolso R$ 620", valor=620.0)
        plano, resultado = executar(caro, self.sops)
        self.assertFalse(any("criar_reembolso: ok" in e for e in resultado.eventos))
        self.assertEqual(resultado.status, "aguardando_aprovacao")


if __name__ == "__main__":
    unittest.main()
