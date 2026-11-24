"""Classificador opcional com Ollama (módulo 03). Não usado nos testes offline."""

from __future__ import annotations

import json
import os
import urllib.request

try:
    from .automation import Classificacao, SOP
except ImportError:  # execução direta
    from automation import Classificacao, SOP

PROMPT = """Classifique a solicitação em UMA das intenções: {intencoes} ou desconhecido.
Responda SOMENTE JSON: {{"intencao": "...", "confianca": 0.0}}
Não invente intenção. Se estiver ambíguo, use desconhecido.
Solicitação: {texto}"""


def classificar_ollama(texto: str, sops: dict[str, SOP], timeout: int = 30) -> Classificacao | None:
    url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/generate"
    payload = {
        "model": os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:3b"),
        "prompt": PROMPT.format(intencoes=", ".join(sops), texto=texto),
        "format": "json",
        "stream": False,
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resposta = json.loads(resp.read().decode()).get("response", "{}")
            dados = json.loads(resposta)
    except (OSError, ValueError):
        return None
    intencao = dados.get("intencao")
    if intencao not in sops:
        return None
    try:
        confianca = max(0.0, min(1.0, float(dados.get("confianca", 0.0))))
    except (TypeError, ValueError):
        confianca = 0.0
    return Classificacao(intencao, confianca, origem="ollama")
