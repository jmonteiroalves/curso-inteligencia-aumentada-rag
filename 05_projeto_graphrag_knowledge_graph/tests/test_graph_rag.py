"""Smoke tests da referência do módulo 05."""

import unittest
from pathlib import Path

from solucao.graph_rag import (
    Tripla,
    caminhos,
    construir_grafo,
    exportar_cypher,
    extrair_entidades,
    extrair_triplas,
    carregar_gazetteer,
    responder,
    responder_hibrido,
    resumo_comunidades,
)

DATA = Path(__file__).resolve().parent.parent / "data"


class TestGraphRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.grafo = construir_grafo(DATA)
        cls.gazetteer = carregar_gazetteer(DATA)

    def test_entidades_sem_duplicatas(self) -> None:
        texto = (DATA / "textos" / "01_pessoas.txt").read_text(encoding="utf-8")
        entidades = extrair_entidades(texto, self.gazetteer)
        nomes = [e.nome for e in entidades]
        self.assertEqual(len(nomes), len(set(nomes)))
        self.assertIn("Marina Costa", nomes)

    def test_triplas_com_evidencia(self) -> None:
        texto = "Marina Costa lidera o Projeto Aurora RAG."
        triplas = extrair_triplas(texto, "teste.txt", self.gazetteer)
        self.assertTrue(triplas)
        self.assertEqual(triplas[0].relacao, "lidera")
        self.assertEqual(triplas[0].fonte, "teste.txt")
        self.assertIn("Marina Costa", triplas[0].evidencia)

    def test_grafo_basico(self) -> None:
        self.assertGreaterEqual(len(self.grafo.entidades), 20)
        self.assertGreaterEqual(len(self.grafo.triplas), 15)
        self.assertGreater(self.grafo.grau("Aurora Tech"), 0)

    def test_duplicata_nao_aumenta_grafo(self) -> None:
        antes = len(self.grafo.triplas)
        self.grafo.adicionar_tripla(
            Tripla("Marina Costa", "lidera", "Projeto Aurora RAG", "dup.txt", "duplicada")
        )
        self.assertEqual(len(self.grafo.triplas), antes)

    def test_consulta_multi_hop(self) -> None:
        r = responder(self.grafo, "Quem lidera o projeto que usa Qdrant?")
        self.assertFalse(r.absteve)
        self.assertEqual(r.resposta, "Marina Costa")
        self.assertTrue(any("<-[usa]-" in c for c in r.caminhos))
        self.assertIn("01_pessoas.txt", r.fontes)

    def test_instituto(self) -> None:
        r = responder(self.grafo, "Qual instituto financia o projeto que usa LangGraph?")
        self.assertEqual(r.resposta, "Instituto Horizonte")

    def test_empresa_parceira(self) -> None:
        r = responder(self.grafo, "Quem trabalha na empresa parceira da Nimbus Cloud?")
        self.assertEqual({"Marina Costa", "Rafael Alves", "Lucas Ferreira"}, set(r.resposta.split(", ")))

    def test_tecnologia(self) -> None:
        r = responder(self.grafo, "Qual tecnologia o projeto liderado por Beatriz Nunes usa?")
        self.assertEqual(r.resposta, "Kafka")

    def test_mentoria(self) -> None:
        r = responder(self.grafo, "Quem Marina Costa mentora e onde essa pessoa trabalha?")
        self.assertEqual(r.resposta, "Aurora Tech")

    def test_hibrido_tem_contexto(self) -> None:
        r = responder_hibrido(self.grafo, "Quem lidera o projeto que usa Qdrant?", DATA)
        self.assertTrue(r.contexto_textual)
        self.assertGreaterEqual(len(r.fontes), 2)

    def test_cypher_idempotente_e_comunidades(self) -> None:
        cypher = exportar_cypher(self.grafo)
        self.assertGreaterEqual(cypher.count("MERGE"), len(self.grafo.entidades) + len(self.grafo.triplas))
        comunidades = resumo_comunidades(self.grafo)
        self.assertEqual(sum(int(c["tamanho"]) for c in comunidades), len(self.grafo.entidades))

    def test_caminhos_limitados(self) -> None:
        todos = caminhos(self.grafo, "Marina Costa", max_hops=2)
        self.assertTrue(all(len(c.relacoes) <= 2 for c in todos))


if __name__ == "__main__":
    unittest.main()
