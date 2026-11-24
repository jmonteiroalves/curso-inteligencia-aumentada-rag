"""Gera notas fiscais sintéticas (PNG/PDF) e o sidecar de OCR esperado.

Execute a partir da raiz do módulo:
    python3 data/gerar_notas.py
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent
DESTINO = RAIZ / "notas_fiscais"
DESTINO.mkdir(exist_ok=True)
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTE_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def fonte(tamanho: int, negrito: bool = False) -> ImageFont.FreeTypeFont:
    caminho = FONTE_BOLD if negrito else FONTE
    try:
        return ImageFont.truetype(caminho, tamanho)
    except OSError:
        return ImageFont.load_default()


NOTAS = [
    {
        "arquivo": "nf_1001.png",
        "numero": "1001",
        "fornecedor": "Nimbus Cloud Serviços Ltda.",
        "cnpj": "12.345.678/0001-90",
        "data": "2026-02-03",
        "categoria": "infraestrutura",
        "itens": [
            {"descricao": "Serviço de nuvem — fevereiro", "quantidade": 1, "preco_unitario": 1200.00, "subtotal": 1200.00},
            {"descricao": "Backup gerenciado", "quantidade": 2, "preco_unitario": 150.00, "subtotal": 300.00},
        ],
        "total": 1500.00,
        "imposto": 0.00,
        "moeda": "BRL",
    },
    {
        "arquivo": "nf_1002.png",
        "numero": "1002",
        "fornecedor": "Atlas Data Analytics Ltda.",
        "cnpj": "98.765.432/0001-10",
        "data": "2026-02-10",
        "categoria": "dados",
        "itens": [
            {"descricao": "Plataforma de dados — fevereiro", "quantidade": 1, "preco_unitario": 480.00, "subtotal": 480.00},
            {"descricao": "Suporte analítico", "quantidade": 3, "preco_unitario": 100.00, "subtotal": 300.00},
        ],
        "total": 780.00,
        "imposto": 0.00,
        "moeda": "BRL",
    },
    {
        "arquivo": "nf_1003.png",
        "numero": "1003",
        "fornecedor": "Nimbus Cloud Serviços Ltda.",
        "cnpj": "12.345.678/0001-90",
        "data": "2026-03-05",
        "categoria": "infraestrutura",
        "itens": [
            {"descricao": "Serviço de nuvem — março", "quantidade": 1, "preco_unitario": 1200.00, "subtotal": 1200.00},
            {"descricao": "Reserva de capacidade", "quantidade": 1, "preco_unitario": 1200.00, "subtotal": 1200.00},
        ],
        "total": 2450.00,
        "imposto": 0.00,
        "moeda": "BRL",
    },
]


def texto_ocr(nota: dict) -> str:
    linhas = [
        "NOTA FISCAL DE SERVIÇOS — DOCUMENTO FICTÍCIO",
        f"Número: {nota['numero']}",
        f"Fornecedor: {nota['fornecedor']}",
        f"CNPJ: {nota['cnpj']}",
        f"Data de emissão: {nota['data']}",
        "",
    ]
    for item in nota["itens"]:
        linhas.append(
            f"{item['descricao']} | qtd {item['quantidade']} | "
            f"unit R$ {item['preco_unitario']:.2f} | subtotal R$ {item['subtotal']:.2f}"
        )
    linhas.extend(
        [
            "",
            f"Total da nota: R$ {nota['total']:.2f}",
            f"Impostos: R$ {nota['imposto']:.2f}",
            "Pagamento: transferência bancária",
        ]
    )
    return "\n".join(linhas)


def desenhar(nota: dict) -> Image.Image:
    img = Image.new("RGB", (1240, 1650), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle((40, 40, 1200, 1610), outline="#1f3b57", width=4)
    draw.text((80, 80), "NOTA FISCAL DE SERVIÇOS", font=fonte(42, True), fill="#1f3b57")
    draw.text((80, 140), "DOCUMENTO FICTÍCIO — SEM VALOR LEGAL", font=fonte(20), fill="#b00020")
    y = 220
    campos = [
        ("Número", nota["numero"]),
        ("Fornecedor", nota["fornecedor"]),
        ("CNPJ", nota["cnpj"]),
        ("Emissão", nota["data"]),
        ("Categoria", nota["categoria"]),
    ]
    for rotulo, valor in campos:
        draw.text((80, y), f"{rotulo}:", font=fonte(22, True), fill="#111111")
        draw.text((260, y), valor, font=fonte(22), fill="#111111")
        y += 44
    y += 30
    draw.line((80, y, 1160, y), fill="#1f3b57", width=2)
    y += 20
    draw.text((80, y), "Itens", font=fonte(28, True), fill="#1f3b57")
    y += 50
    for item in nota["itens"]:
        draw.text((80, y), item["descricao"], font=fonte(22), fill="#111111")
        y += 34
        draw.text(
            (110, y),
            f"Qtd {item['quantidade']}  ×  R$ {item['preco_unitario']:.2f}   =   "
            f"R$ {item['subtotal']:.2f}",
            font=fonte(20),
            fill="#333333",
        )
        y += 56
    draw.line((80, y, 1160, y), fill="#999999", width=1)
    y += 30
    draw.text((720, y), f"Total: R$ {nota['total']:.2f}", font=fonte(32, True), fill="#1f3b57")
    y += 55
    draw.text((720, y), f"Impostos: R$ {nota['imposto']:.2f}", font=fonte(20), fill="#333333")
    draw.text((80, 1510), "Chave sintética: 0000-0000-0000", font=fonte(16), fill="#777777")
    draw.text((80, 1545), "Gerado para o curso de Inteligência Aumentada", font=fonte(16), fill="#777777")
    return img


def main() -> None:
    registros = []
    for nota in NOTAS:
        img = desenhar(nota)
        png = DESTINO / nota["arquivo"]
        img.save(png)
        img.save(DESTINO / nota["arquivo"].replace(".png", ".pdf"), "PDF")
        registros.append({**nota, "texto_ocr": texto_ocr(nota)})
    (DESTINO / "notas.json").write_text(
        json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Geradas {len(registros)} notas em {DESTINO}")


if __name__ == "__main__":
    main()
