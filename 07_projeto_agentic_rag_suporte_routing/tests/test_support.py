"""Smoke tests da referência do módulo 07."""

import unittest
from pathlib import Path

from solucao.support_agent import (
    carregar_clientes,
    carregar_tickets,
    classificar_ticket,
    deve_escalar,
    executar_ticket,
    recuperar_runbook,
    rotear,
)

DATA = Path(__file__).resolve().parent.parent / "data"


class TestSuporte(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clientes = carregar_clientes(DATA)
        cls.tickets = {t.id: t for t in carregar_tickets(DATA)}
        cls.resultados = {
            t.id: executar_ticket(t, cls.clientes[t.cliente_id], DATA)
            for t in cls.tickets.values()
        }

    def test_classificacao_e_prioridade(self) -> None:
        self.assertEqual(classificar_ticket(self.tickets["t03"])[0], "integracao")
        self.assertEqual(classificar_ticket(self.tickets["t08"])[0], "seguranca")
        self.assertEqual(classificar_ticket(self.tickets["t09"])[0], "cobranca")
        self.assertEqual(self.resultados["t03"].roteamento.prioridade, "P1")
        self.assertEqual(self.resultados["t10"].roteamento.prioridade, "P2")

    def test_sla_enterprise_p1(self) -> None:
        r = rotear(self.tickets["t03"], self.clientes["c03"])
        self.assertEqual(r.fila, "engenharia")
        self.assertEqual(r.sla_horas, 0.5)

    def test_runbook(self) -> None:
        self.assertIn("Cobrança", recuperar_runbook("cobranca", DATA).titulo)
        self.assertIn("Triagem", recuperar_runbook("indefinido", DATA).titulo)

    def test_reembolso_exige_aprovacao(self) -> None:
        resultado = self.resultados["t01"]
        self.assertEqual(resultado.status, "aguardando_aprovacao")
        self.assertTrue(any("bloqueada" in e for e in resultado.eventos))
        self.assertFalse(any("solicitar_reembolso: ok" in e for e in resultado.eventos))

    def test_seguranca_nao_reseta_senha(self) -> None:
        resultado = self.resultados["t04"]
        self.assertEqual(resultado.status, "handoff")
        self.assertEqual(resultado.roteamento.fila, "seguranca")
        self.assertFalse(any("reset_senha" in e for e in resultado.eventos))
        self.assertEqual(resultado.motivo_escalonamento, "Incidente de segurança exige time especializado")

    def test_p1_handoff(self) -> None:
        self.assertEqual(self.resultados["t03"].status, "handoff")
        self.assertEqual(self.resultados["t08"].status, "handoff")

    def test_integracao_webhook_resolvida(self) -> None:
        resultado = self.resultados["t05"]
        self.assertEqual(resultado.status, "resolvido")
        self.assertIn("reprocessar_evento: ok", resultado.eventos)

    def test_integracao_parada_escala(self) -> None:
        resultado = self.resultados["t10"]
        self.assertEqual(resultado.status, "handoff")
        self.assertIn("parada", resultado.motivo_escalonamento.lower())

    def test_gatilhos_de_escalonamento(self) -> None:
        self.assertIsNotNone(deve_escalar(self.tickets["t04"], self.resultados["t04"].roteamento))
        self.assertIsNone(deve_escalar(self.tickets["t02"], self.resultados["t02"].roteamento))

    def test_todos_os_tickets_tem_resultado(self) -> None:
        self.assertEqual(len(self.resultados), 10)
        self.assertTrue(all(r.acoes for r in self.resultados.values()))
        self.assertTrue(all(r.runbook for r in self.resultados.values()))


if __name__ == "__main__":
    unittest.main()
