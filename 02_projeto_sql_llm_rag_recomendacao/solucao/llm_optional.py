"""Adaptador opcional para gerar SQL com Ollama (módulo 02).

O SQL retornado NUNCA deve ser executado sem `validar_sql`. O curso usa o gerador
determinístico por padrão para que a solução rode offline.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request

PROMPT = """Você é um engenheiro de dados. Gere apenas SQLite SELECT para a pergunta.
Regras: uma única instrução; sem DDL/DML; sem comentários; use apenas as tabelas listadas;
no máximo 50 linhas.
Tabelas e colunas:
{schema}
Pergunta: {pergunta}
Responda somente com o SQL, sem markdown."""


def gerar_sql_ollama(pergunta: str, schema: str, timeout: int = 30) -> str | None:
    url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/generate"
    modelo = os.getenv("OLLAMA_CHAT_MODEL", "llama3.2:3b")
    payload = json.dumps(
        {"model": modelo, "prompt": PROMPT.format(schema=schema, pergunta=pergunta), "stream": False}
    ).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            texto = json.loads(resp.read().decode()).get("response", "")
    except (OSError, ValueError):
        return None
    match = re.search(r"```(?:sql)?\s*(.*?)```", texto, re.DOTALL | re.IGNORECASE)
    return (match.group(1) if match else texto).strip() or None
