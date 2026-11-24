"""Visão opcional com Ollama (módulo 08).

Não é executado pelos testes. O sidecar é o gabarito offline; um modelo de visão pode
ser usado para comparar a extração e detectar alucinações de valores.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.request
from pathlib import Path

PROMPT = """Extraia a nota fiscal da imagem e responda SOMENTE JSON:
{
  "numero": "string",
  "fornecedor": "string",
  "cnpj": "string",
  "data": "YYYY-MM-DD",
  "itens": [{"descricao": "string", "quantidade": 0, "preco_unitario": 0.0, "subtotal": 0.0}],
  "total": 0.0,
  "imposto": 0.0
}
Não invente valores. Se não conseguir ler, retorne {"erro": "motivo"}.
"""


def extrair_com_ollama(imagem: Path, timeout: int = 90) -> dict | None:
    try:
        conteudo = base64.b64encode(imagem.read_bytes()).decode("ascii")
    except OSError:
        return None
    payload = {
        "model": os.getenv("OLLAMA_VISION_MODEL", "llava:7b"),
        "prompt": PROMPT,
        "images": [conteudo],
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
            bruto = json.loads(resp.read().decode()).get("response", "{}")
            dados = json.loads(bruto)
    except (OSError, ValueError):
        return None
    if not isinstance(dados, dict) or "erro" in dados:
        return None
    return dados
