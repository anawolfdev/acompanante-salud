"""Guardado en SQLite. Un solo archivo, sin servidor."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from acompanante.modelos import Cita

FORMATO = "%Y-%m-%d %H:%M"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS citas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo        TEXT NOT NULL DEFAULT 'cita',
    titulo      TEXT NOT NULL,
    fecha_hora  TEXT NOT NULL,              -- 'AAAA-MM-DD HH:MM', hora de Madrid
    lugar       TEXT NOT NULL DEFAULT '',
    preparacion TEXT NOT NULL DEFAULT '[]', -- lista en JSON
    notas       TEXT NOT NULL DEFAULT '',
    creada_en   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS avisos_enviados (
    cita_id     INTEGER NOT NULL REFERENCES citas(id) ON DELETE CASCADE,
    tipo_aviso  TEXT NOT NULL,              -- 'previo' o 'dia'
    enviado_en  TEXT NOT NULL,
    PRIMARY KEY (cita_id, tipo_aviso)
);
"""


def conectar(ruta: str | Path) -> sqlite3.Connection:
    """Abre (o crea) la base de datos y se asegura de que existen las tablas."""
    ruta = str(ruta)
    if ruta != ":memory:":
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ruta)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(ESQUEMA)
    return con


def _fila_a_cita(fila: sqlite3.Row) -> Cita:
    return Cita(
        id=fila["id"],
        tipo=fila["tipo"],
        titulo=fila["titulo"],
        fecha_hora=datetime.strptime(fila["fecha_hora"], FORMATO),
        lugar=fila["lugar"],
        preparacion=json.loads(fila["preparacion"]),
        notas=fila["notas"],
    )


def guardar_cita(con: sqlite3.Connection, cita: Cita) -> int:
    cur = con.execute(
        "INSERT INTO citas (tipo, titulo, fecha_hora, lugar, preparacion, notas, creada_en)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            cita.tipo,
            cita.titulo,
            cita.fecha_hora.strftime(FORMATO),
            cita.lugar,
            json.dumps(cita.preparacion, ensure_ascii=False),
            cita.notas,
            datetime.now().strftime(FORMATO),
        ),
    )
    con.commit()
    cita.id = cur.lastrowid
    return cita.id


def listar_citas(con: sqlite3.Connection, desde: datetime | None = None) -> list[Cita]:
    """Citas ordenadas por fecha. Con 'desde', solo las que aún no han pasado."""
    if desde is None:
        filas = con.execute("SELECT * FROM citas ORDER BY fecha_hora").fetchall()
    else:
        filas = con.execute(
            "SELECT * FROM citas WHERE fecha_hora >= ? ORDER BY fecha_hora",
            (desde.strftime(FORMATO),),
        ).fetchall()
    return [_fila_a_cita(f) for f in filas]


def aviso_enviado(con: sqlite3.Connection, cita_id: int, tipo_aviso: str) -> bool:
    fila = con.execute(
        "SELECT 1 FROM avisos_enviados WHERE cita_id = ? AND tipo_aviso = ?",
        (cita_id, tipo_aviso),
    ).fetchone()
    return fila is not None


def marcar_aviso_enviado(con: sqlite3.Connection, cita_id: int, tipo_aviso: str, cuando: datetime) -> None:
    con.execute(
        "INSERT OR IGNORE INTO avisos_enviados (cita_id, tipo_aviso, enviado_en) VALUES (?, ?, ?)",
        (cita_id, tipo_aviso, cuando.strftime(FORMATO)),
    )
    con.commit()
