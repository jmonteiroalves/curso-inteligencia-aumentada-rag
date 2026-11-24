"""Geração opcional de perguntas com SLM local (módulo 04).

A saída deve ser revisada por uma pessoa. O prompt recebe apenas a visão anonimizada
e as evidências; não inclui nome, gênero, idade ou outros atributos protegidos.
"""

from __future__ import annotations

import json
import os
import urllib.request

try:
    from .rh_rag import ResultadoMatching, Vaga
except ImportError:  # execução direta
    from rh_rag import ResultadoMatching, Vaga

PROMPT = """Você é um recrutador técnico. Gere 5 perguntas de entrevista comportamental/técnica
baseadas APENAS nas evidências abaixo. Cada pergunta deve citar um critério.
Não pergunte gênero, idade, raça, religião, estado civil, deficiência ou vida pessoal.
Responda SOMENTE JSON: {{"perguntas": ["...", "...", "...", "...", "..."]}}
Vaga: {vaga}
Critérios e evidências:
{evidencias}
Lacunas: {lacunas}
"""


def gerar_perguntas_ollama(
    resultado: ResultadoMatching, vaga: Vaga, timeout: int = 45
) -> list[str] | None:
    evidencias = "\n".join(
        f"- {e.criterio} (score {e.score}): {e.evidencia}" for e in resultado.evidencias
    )
    prompt = PROMPT.format(
        vaga=vaga.titulo, evidencias=evidencias, lacunas=", ".join(resultado.lacunas) or "nenhuma"
    )
    payload = {
        "model": os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:3b"),
        "prompt": prompt,
        "format": "json",
        "stream": False,
    }
    req = urllib.request.Request(
        os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            dados = json.loads(json.loads(resp.read().decode()).get("response", "{}"))
    except (OSError, ValueError):
        return None
    perguntas = dados.get("perguntas")
    if not isinstance(perguntas, list) or len(perguntas) != 5:
        return None
    return [str(p) for p in perguntas]
