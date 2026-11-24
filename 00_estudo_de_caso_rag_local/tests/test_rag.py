"""Smoke tests da referência do módulo 00."""

import unittest
from pathlib import Path

from solucao.rag_solution import RAGIndex, carregar_documentos, chunk_text

DATA = Path(__file__).resolve().parent.parent / "data"


class TestRAGLocal(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.indice = RAGIndex(carregar_documentos(DATA)).index()

    def test_chunks_respeitam_tamanho_e_nao_cortam_palavras(self) -> None:
        self.assertGreater(len(self.indice.chunks), 5)
        for chunk in self.indice.chunks:
            self.assertLessEqual(len(chunk.texto), 460)
            self.assertEqual(chunk.texto, " ".join(chunk.texto.split()))

    def test_overlap_preserva_contexto(self) -> None:
        chunks = chunk_text("palavra " * 200, max_chars=100, overlap=30)
        self.assertGreater(len(chunks), 3)
        self.assertTrue(any(set(a.split()) & set(b.split()) for a, b in zip(chunks, chunks[1:])))

    def test_retrieval_encontra_fonte_correta(self) -> None:
        hits = self.indice.search("Qual o prazo de primeira resposta para P1?", top_k=3)
        self.assertIn("incidentes_suporte.md", {h.chunk.fonte for h in hits})

    def test_resposta_tem_citacao(self) -> None:
        resposta = self.indice.answer("Quantos dias de férias?")
        self.assertFalse(resposta.absteve)
        self.assertTrue(resposta.fontes)
        self.assertIn("[", resposta.texto)

    def test_abstem_fora_do_corpus(self) -> None:
        resposta = self.indice.answer("Qual é a capital da França?")
        self.assertTrue(resposta.absteve)
        self.assertEqual(resposta.fontes, ())


if __name__ == "__main__":
    unittest.main()
