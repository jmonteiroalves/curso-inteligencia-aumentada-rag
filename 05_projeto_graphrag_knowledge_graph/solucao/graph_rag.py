"""Referência funcional de GraphRAG (módulo 05)."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, replace
from pathlib import Path

MAX_HOPS = 3

REL_KEYWORDS = {
    "lidera": {"lidera", "liderado", "lider", "lideranca", "coordena"},
    "usa": {"usa", "utiliza", "adota", "tecnologia"},
    "trabalha_em": {"trabalha", "trabalham", "empregado", "empregada", "equipe", "funcionario"},
    "participa_de": {"participa", "participam", "participacao"},
    "financia": {"financia", "financiado", "financiamento"},
    "parceira_de": {"parceira", "parceiro", "parceria"},
    "mentora": {"mentora", "mentorado", "mentoria"},
    "sede_em": {"sede", "cidade", "onde"},
    "depende_de": {"depende", "dependencia"},
    "integra": {"integra", "integracao"},
    "fornece_para": {"fornece", "fornecedor", "fornecimento"},
}

LABELS = {
    "PESSOA": "Pessoa",
    "ORGANIZACAO": "Organizacao",
    "PROJETO": "Projeto",
    "TECNOLOGIA": "Tecnologia",
    "CIDADE": "Cidade",
}


@dataclass(frozen=True)
class Entidade:
    nome: str
    tipo: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Tripla:
    sujeito: str
    relacao: str
    objeto: str
    fonte: str
    evidencia: str


@dataclass(frozen=True)
class Caminho:
    nos: tuple[str, ...]
    relacoes: tuple[str, ...]
    triplas: tuple[Tripla, ...]

    def formatado(self) -> str:
        partes = [self.nos[0]]
        for i, (relacao, no) in enumerate(zip(self.relacoes, self.nos[1:])):
            tripla = self.triplas[i]
            if tripla.sujeito == self.nos[i] and tripla.objeto == no:
                partes.append(f"-[{relacao}]-> {no}")
            else:
                partes.append(f"<-[{relacao}]- {no}")
        return " ".join(partes)


@dataclass(frozen=True)
class Trecho:
    fonte: str
    texto: str
    score: float


@dataclass(frozen=True)
class RespostaGraph:
    pergunta: str
    resposta: str
    absteve: bool
    score: float
    caminhos: tuple[str, ...]
    evidencias: tuple[str, ...]
    fontes: tuple[str, ...]
    contexto_textual: tuple[Trecho, ...] = ()


def normalizar(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    return re.sub(r"[^a-z0-9\s]", " ", "".join(c for c in decomposto if not unicodedata.combining(c)))


def carregar_gazetteer(data_dir: Path) -> list[Entidade]:
    dados = json.loads((data_dir / "entidades.json").read_text(encoding="utf-8"))
    return [
        Entidade(item["nome"], item["tipo"], tuple(item.get("aliases", [item["nome"]])))
        for item in dados["entidades"]
    ]


def carregar_textos(data_dir: Path) -> list[tuple[str, str]]:
    return [
        (caminho.name, caminho.read_text(encoding="utf-8").strip())
        for caminho in sorted((data_dir / "textos").glob("*.txt"))
    ]


class KnowledgeGraph:
    def __init__(self) -> None:
        self.entidades: dict[str, Entidade] = {}
        self.triplas: list[Tripla] = []
        self._saida: dict[str, list[Tripla]] = defaultdict(list)
        self._entrada: dict[str, list[Tripla]] = defaultdict(list)

    def adicionar_entidade(self, entidade: Entidade) -> None:
        self.entidades.setdefault(entidade.nome, entidade)

    def adicionar_tripla(self, tripla: Tripla) -> None:
        chave = (tripla.sujeito, tripla.relacao, tripla.objeto)
        if any((t.sujeito, t.relacao, t.objeto) == chave for t in self.triplas):
            return
        self.triplas.append(tripla)
        self._saida[tripla.sujeito].append(tripla)
        self._entrada[tripla.objeto].append(tripla)

    def vizinhos(self, nome: str) -> list[tuple[Tripla, str]]:
        if nome not in self.entidades:
            return []
        itens = [(t, "saida") for t in self._saida.get(nome, [])]
        itens += [(t, "entrada") for t in self._entrada.get(nome, [])]
        return itens

    def grau(self, nome: str) -> int:
        return len(self._saida.get(nome, [])) + len(self._entrada.get(nome, []))

    def comunidades(self) -> list[list[str]]:
        adj: dict[str, set[str]] = defaultdict(set)
        for nome in self.entidades:
            adj[nome]
        for t in self.triplas:
            adj[t.sujeito].add(t.objeto)
            adj[t.objeto].add(t.sujeito)
        vistos: set[str] = set()
        componentes: list[list[str]] = []
        for nome in sorted(adj):
            if nome in vistos:
                continue
            fila = deque([nome])
            vistos.add(nome)
            componente = []
            while fila:
                atual = fila.popleft()
                componente.append(atual)
                for vizinho in adj[atual]:
                    if vizinho not in vistos:
                        vistos.add(vizinho)
                        fila.append(vizinho)
            componentes.append(sorted(componente))
        return sorted(componentes, key=lambda c: (-len(c), c))


def _padroes(gazetteer: list[Entidade]) -> list[tuple[str, re.Pattern[str]]]:
    aliases = sorted(
        {alias for ent in gazetteer for alias in (ent.aliases or (ent.nome,))},
        key=len,
        reverse=True,
    )
    E = "(?:" + "|".join(re.escape(alias) for alias in aliases) + ")"
    definicoes = [
        ("trabalha_em", rf"(?P<s>{E})\s+(?:trabalha|atua)\s+(?:na|no|em)\s+(?P<o>{E})"),
        ("lidera", rf"(?P<s>{E})\s+(?:lidera|coordena)\s+(?:o|a)?\s*(?P<o>{E})"),
        ("usa", rf"(?P<s>{E})\s+(?:usa|utiliza|adota)\s+(?:o|a)?\s*(?P<o>{E})"),
        ("depende_de", rf"(?P<s>{E})\s+depende\s+(?:do|da|de)\s+(?P<o>{E})"),
        ("integra", rf"(?P<s>{E})\s+integra\s+(?:o|a)?\s*(?P<o>{E})"),
        ("financia", rf"(?P<s>{E})\s+financia\s+(?:o|a)?\s*(?P<o>{E})"),
        ("parceira_de", rf"(?P<s>{E})\s+é\s+parceir[ao]\s+d[ao]\s+(?P<o>{E})"),
        ("fornece_para", rf"(?P<s>{E})\s+fornece\s+.*?\s+para\s+(?:a|o)?\s*(?P<o>{E})"),
        ("mentora", rf"(?P<s>{E})\s+mentora\s+(?:o|a)?\s*(?P<o>{E})"),
        ("participa_de", rf"(?P<s>{E})\s+participa\s+(?:do|da|de)\s+(?P<o>{E})"),
        ("sede_em", rf"(?P<s>{E})\s+tem\s+sede\s+(?:em|no|na)\s+(?P<o>{E})"),
    ]
    return [(rel, re.compile(padrao, re.IGNORECASE | re.UNICODE)) for rel, padrao in definicoes]


def _mapa_aliases(gazetteer: list[Entidade]) -> dict[str, Entidade]:
    return {
        alias.lower(): entidade
        for entidade in gazetteer
        for alias in (entidade.aliases or (entidade.nome,))
    }


def extrair_entidades(texto: str, gazetteer: list[Entidade]) -> list[Entidade]:
    achados: list[tuple[int, Entidade]] = []
    vistos: set[str] = set()
    for entidade in gazetteer:
        for alias in entidade.aliases or (entidade.nome,):
            posicao = texto.lower().find(alias.lower())
            if posicao >= 0 and entidade.nome not in vistos:
                achados.append((posicao, entidade))
                vistos.add(entidade.nome)
                break
    return [entidade for _, entidade in sorted(achados, key=lambda item: item[0])]


def extrair_triplas(texto: str, fonte: str, gazetteer: list[Entidade]) -> list[Tripla]:
    frases = [f.strip() for f in re.split(r"(?<=[.!?])\s+", texto.replace("\n", " ")) if f.strip()]
    alias_map = _mapa_aliases(gazetteer)
    triplas: list[Tripla] = []
    vistos: set[tuple[str, str, str]] = set()
    for frase in frases:
        for relacao, padrao in _padroes(gazetteer):
            for match in padrao.finditer(frase):
                sujeito_bruto = match.group("s")
                objeto_bruto = match.group("o")
                sujeito = alias_map.get(sujeito_bruto.lower(), Entidade(sujeito_bruto, "DESCONHECIDO"))
                objeto = alias_map.get(objeto_bruto.lower(), Entidade(objeto_bruto, "DESCONHECIDO"))
                if sujeito.nome == objeto.nome:
                    continue
                chave = (sujeito.nome, relacao, objeto.nome)
                if chave in vistos:
                    continue
                vistos.add(chave)
                triplas.append(Tripla(sujeito.nome, relacao, objeto.nome, fonte, frase))
    return triplas


def construir_grafo(data_dir: Path) -> KnowledgeGraph:
    gazetteer = carregar_gazetteer(data_dir)
    grafo = KnowledgeGraph()
    for fonte, texto in carregar_textos(data_dir):
        for entidade in extrair_entidades(texto, gazetteer):
            grafo.adicionar_entidade(entidade)
        for tripla in extrair_triplas(texto, fonte, gazetteer):
            grafo.adicionar_tripla(tripla)
    for entidade in gazetteer:
        if entidade.nome in grafo.entidades:
            grafo.adicionar_entidade(entidade)
    return grafo


def caminhos(grafo: KnowledgeGraph, inicio: str, max_hops: int = MAX_HOPS) -> list[Caminho]:
    if inicio not in grafo.entidades:
        return []
    resultados: list[Caminho] = []

    def dfs(no: str, nos: list[str], triplas: list[Tripla]) -> None:
        if triplas:
            resultados.append(
                Caminho(tuple(nos), tuple(t.relacao for t in triplas), tuple(triplas))
            )
        if len(triplas) >= max_hops:
            return
        for tripla, direcao in grafo.vizinhos(no):
            proximo = tripla.objeto if direcao == "saida" else tripla.sujeito
            if proximo in nos:
                continue
            dfs(proximo, [*nos, proximo], [*triplas, tripla])

    dfs(inicio, [inicio], [])
    return resultados


def _tipos_esperados(pergunta: str) -> set[str]:
    p = normalizar(pergunta)
    if "tecnologia" in p:
        return {"TECNOLOGIA"}
    if "instituto" in p:
        return {"ORGANIZACAO"}
    if "onde" in p:
        if "trabalha" in p:
            return {"ORGANIZACAO"}
        return {"ORGANIZACAO", "CIDADE"}
    if "quem" in p:
        return {"PESSOA"}
    if "projeto" in p or "plataforma" in p:
        return {"PROJETO"}
    if "cidade" in p:
        return {"CIDADE"}
    return {"PESSOA", "ORGANIZACAO", "PROJETO", "TECNOLOGIA", "CIDADE"}


def _score_caminho(caminho: Caminho, pergunta: str, grafo: KnowledgeGraph) -> float:
    q_tokens = set(normalizar(pergunta).split())
    esperados = _tipos_esperados(pergunta)
    score = 0.0
    for relacao in caminho.relacoes:
        if REL_KEYWORDS.get(relacao, set()) & q_tokens:
            score += 2.5
        else:
            score -= 0.5
    fim = grafo.entidades.get(caminho.nos[-1])
    if fim and fim.tipo in esperados:
        score += 6.0
    score += 0.4 * (len(caminho.relacoes) - 1)
    if len(caminho.relacoes) > 2:
        score -= 0.3 * (len(caminho.relacoes) - 2)
    return round(score, 3)


def responder(grafo: KnowledgeGraph, pergunta: str) -> RespostaGraph:
    gazetteer = list(grafo.entidades.values())
    ancoras = extrair_entidades(pergunta, gazetteer)
    if not ancoras:
        return RespostaGraph(pergunta, "Não encontrei uma entidade-âncora para consultar o grafo.", True, 0.0, (), (), ())

    pontuados: list[tuple[float, Caminho]] = []
    for ancora in ancoras:
        for caminho in caminhos(grafo, ancora.nome, max_hops=MAX_HOPS):
            if caminho.nos[-1] == ancora.nome:
                continue
            score = _score_caminho(caminho, pergunta, grafo)
            if score >= 6.0:
                pontuados.append((score, caminho))
    if not pontuados:
        return RespostaGraph(pergunta, "Não encontrei um caminho com evidência suficiente.", True, 0.0, (), (), ())

    pontuados.sort(key=lambda item: (-item[0], len(item[1].nos), item[1].formatado()))
    melhor = pontuados[0][0]
    selecionados: list[Caminho] = []
    vistos: set[str] = set()
    for score, caminho in pontuados:
        if score < melhor - 1e-9:
            break
        fim = caminho.nos[-1]
        if fim not in vistos:
            selecionados.append(caminho)
            vistos.add(fim)

    respostas = [c.nos[-1] for c in selecionados]
    fontes = tuple(dict.fromkeys(t.fonte for c in selecionados for t in c.triplas))
    evidencias = tuple(
        dict.fromkeys(
            f"{t.sujeito} --{t.relacao}--> {t.objeto} [{t.fonte}]"
            for c in selecionados
            for t in c.triplas
        )
    )
    return RespostaGraph(
        pergunta=pergunta,
        resposta=", ".join(respostas),
        absteve=False,
        score=round(melhor, 3),
        caminhos=tuple(c.formatado() for c in selecionados),
        evidencias=evidencias,
        fontes=fontes,
    )


def recuperar_contexto_textual(pergunta: str, data_dir: Path, top_k: int = 3) -> list[Trecho]:
    q_tokens = set(normalizar(pergunta).split())
    if not q_tokens:
        return []
    trechos: list[Trecho] = []
    for fonte, texto in carregar_textos(data_dir):
        frases = [
            frase.strip()
            for paragrafo in re.split(r"\n\s*\n", texto)
            for frase in re.split(r"(?<=[.!?])\s+", " ".join(paragrafo.split()))
            if frase.strip()
        ]
        for frase in frases:
            tokens = set(normalizar(frase).split())
            if not tokens:
                continue
            score = len(q_tokens & tokens) / math.sqrt(len(q_tokens) * len(tokens))
            if score > 0:
                trechos.append(Trecho(fonte, frase.strip(), round(score, 3)))
    trechos.sort(key=lambda t: (-t.score, t.fonte, t.texto))
    return trechos[:top_k]


def responder_hibrido(grafo: KnowledgeGraph, pergunta: str, data_dir: Path) -> RespostaGraph:
    base = responder(grafo, pergunta)
    contexto = recuperar_contexto_textual(pergunta, data_dir, top_k=3)
    fontes = tuple(dict.fromkeys([*base.fontes, *(t.fonte for t in contexto[:2])]))
    if base.absteve and contexto:
        return replace(
            base,
            resposta=f"Evidência textual: {contexto[0].texto}",
            absteve=False,
            fontes=fontes,
            contexto_textual=tuple(contexto),
        )
    return replace(base, fontes=fontes, contexto_textual=tuple(contexto))


def exportar_cypher(grafo: KnowledgeGraph) -> str:
    def esc(valor: str) -> str:
        return valor.replace("\\", "\\\\").replace("'", "\\'")

    linhas = ["// Gerado pelo curso GraphRAG. Idempotente: pode executar mais de uma vez."]
    for entidade in sorted(grafo.entidades.values(), key=lambda e: (e.tipo, e.nome)):
        label = LABELS.get(entidade.tipo, "Entidade")
        linhas.append(
            f"MERGE (n:{label} {{nome: '{esc(entidade.nome)}'}}) "
            f"SET n.tipo = '{esc(entidade.tipo)}';"
        )
    for tripla in sorted(grafo.triplas, key=lambda t: (t.sujeito, t.relacao, t.objeto)):
        sujeito = grafo.entidades.get(tripla.sujeito)
        objeto = grafo.entidades.get(tripla.objeto)
        if not sujeito or not objeto:
            continue
        label_s = LABELS.get(sujeito.tipo, "Entidade")
        label_o = LABELS.get(objeto.tipo, "Entidade")
        relacao = re.sub(r"[^A-Z0-9_]", "_", tripla.relacao.upper())
        linhas.append(
            f"MATCH (a:{label_s} {{nome: '{esc(tripla.sujeito)}'}}), "
            f"(b:{label_o} {{nome: '{esc(tripla.objeto)}'}}) "
            f"MERGE (a)-[:{relacao}]->(b);"
        )
    return "\n".join(linhas)


def resumo_comunidades(grafo: KnowledgeGraph) -> list[dict[str, object]]:
    resumos = []
    for membros in grafo.comunidades():
        tipos = Counter(grafo.entidades[m].tipo for m in membros if m in grafo.entidades)
        internas = [t for t in grafo.triplas if t.sujeito in membros and t.objeto in membros]
        resumos.append(
            {
                "membros": membros,
                "tamanho": len(membros),
                "tipos": dict(tipos),
                "arestas_internas": len(internas),
                "maior_grau": max(membros, key=lambda m: grafo.grau(m)),
            }
        )
    return resumos
