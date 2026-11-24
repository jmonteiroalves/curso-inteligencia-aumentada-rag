"""Recria o SQLite sintético a partir de data/seed.sql."""

from pathlib import Path
import sqlite3

RAIZ = Path(__file__).resolve().parent
DESTINO = RAIZ / "loja.db"


def main() -> None:
    if DESTINO.exists():
        DESTINO.unlink()
    sql = (RAIZ / "seed.sql").read_text(encoding="utf-8")
    with sqlite3.connect(DESTINO) as con:
        con.executescript(sql)
    print(f"Banco criado: {DESTINO} ({DESTINO.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
