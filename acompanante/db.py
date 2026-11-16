"""Guardado en SQLite. Un solo archivo, sin servidor."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

from acompanante.modelos import Cita, EntradaHistorial, Medicacion, Tarea, Tension
from acompanante.textos import DIAS

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

CREATE TABLE IF NOT EXISTS tareas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo      TEXT NOT NULL,
    dias        TEXT NOT NULL,              -- 'lunes,jueves'
    hora        TEXT NOT NULL,              -- 'HH:MM'
    activa      INTEGER NOT NULL DEFAULT 1,
    creada_en   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS avisos_tareas_enviados (
    tarea_id    INTEGER NOT NULL REFERENCES tareas(id) ON DELETE CASCADE,
    fecha       TEXT NOT NULL,              -- 'AAAA-MM-DD'
    enviado_en  TEXT NOT NULL,
    PRIMARY KEY (tarea_id, fecha)
);

CREATE TABLE IF NOT EXISTS tensiones (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_hora  TEXT NOT NULL,              -- 'AAAA-MM-DD HH:MM', hora de Madrid
    alta        INTEGER NOT NULL,           -- sistólica
    baja        INTEGER NOT NULL,           -- diastólica
    pulso       INTEGER,                    -- opcional
    nota        TEXT NOT NULL DEFAULT '',
    creada_en   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS medicaciones (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    dosis       TEXT NOT NULL,
    pauta       TEXT NOT NULL,
    activa      INTEGER NOT NULL DEFAULT 1,
    creada_en   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historial (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    descripcion TEXT NOT NULL,
    fecha       TEXT NOT NULL,              -- 'AAAA-MM-DD'
    creada_en   TEXT NOT NULL
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


def obtener_cita(con: sqlite3.Connection, cita_id: int) -> Cita:
    fila = con.execute("SELECT * FROM citas WHERE id = ?", (cita_id,)).fetchone()
    if fila is None:
        raise ValueError(f"No hay ninguna cita con el número {cita_id}")
    return _fila_a_cita(fila)


def actualizar_cita(con: sqlite3.Connection, cita: Cita) -> None:
    con.execute(
        "UPDATE citas SET tipo = ?, titulo = ?, fecha_hora = ?, lugar = ?, preparacion = ?, notas = ?"
        " WHERE id = ?",
        (
            cita.tipo,
            cita.titulo,
            cita.fecha_hora.strftime(FORMATO),
            cita.lugar,
            json.dumps(cita.preparacion, ensure_ascii=False),
            cita.notas,
            cita.id,
        ),
    )
    con.commit()


def borrar_cita(con: sqlite3.Connection, cita_id: int) -> None:
    con.execute("DELETE FROM citas WHERE id = ?", (cita_id,))
    con.commit()


def borrar_avisos_de_cita(con: sqlite3.Connection, cita_id: int) -> None:
    """Olvida los avisos ya enviados, para que vuelvan a salir."""
    con.execute("DELETE FROM avisos_enviados WHERE cita_id = ?", (cita_id,))
    con.commit()


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


def _fila_a_tarea(fila: sqlite3.Row) -> Tarea:
    return Tarea(
        id=fila["id"],
        titulo=fila["titulo"],
        dias=[DIAS.index(nombre) for nombre in fila["dias"].split(",") if nombre],
        hora=datetime.strptime(fila["hora"], "%H:%M").time(),
        activa=bool(fila["activa"]),
    )


def guardar_tarea(con: sqlite3.Connection, tarea: Tarea) -> int:
    cur = con.execute(
        "INSERT INTO tareas (titulo, dias, hora, activa, creada_en) VALUES (?, ?, ?, ?, ?)",
        (
            tarea.titulo,
            ",".join(DIAS[dia] for dia in tarea.dias),
            tarea.hora.strftime("%H:%M"),
            1 if tarea.activa else 0,
            datetime.now().strftime(FORMATO),
        ),
    )
    con.commit()
    tarea.id = cur.lastrowid
    return tarea.id


def obtener_tarea(con: sqlite3.Connection, tarea_id: int) -> Tarea:
    fila = con.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,)).fetchone()
    if fila is None:
        raise ValueError(f"No hay ninguna tarea con el número {tarea_id}")
    return _fila_a_tarea(fila)


def listar_tareas(con: sqlite3.Connection, solo_activas: bool = False) -> list[Tarea]:
    if solo_activas:
        filas = con.execute("SELECT * FROM tareas WHERE activa = 1 ORDER BY id").fetchall()
    else:
        filas = con.execute("SELECT * FROM tareas ORDER BY id").fetchall()
    return [_fila_a_tarea(fila) for fila in filas]


def pausar_tarea(con: sqlite3.Connection, tarea_id: int) -> None:
    con.execute("UPDATE tareas SET activa = 0 WHERE id = ?", (tarea_id,))
    con.commit()


def aviso_tarea_enviado(con: sqlite3.Connection, tarea_id: int, fecha: date) -> bool:
    fila = con.execute(
        "SELECT 1 FROM avisos_tareas_enviados WHERE tarea_id = ? AND fecha = ?",
        (tarea_id, fecha.strftime("%Y-%m-%d")),
    ).fetchone()
    return fila is not None


def marcar_aviso_tarea_enviado(
    con: sqlite3.Connection, tarea_id: int, fecha: date, cuando: datetime
) -> None:
    con.execute(
        "INSERT OR IGNORE INTO avisos_tareas_enviados (tarea_id, fecha, enviado_en) VALUES (?, ?, ?)",
        (tarea_id, fecha.strftime("%Y-%m-%d"), cuando.strftime(FORMATO)),
    )
    con.commit()


def _fila_a_tension(fila: sqlite3.Row) -> Tension:
    return Tension(
        id=fila["id"],
        fecha_hora=datetime.strptime(fila["fecha_hora"], FORMATO),
        alta=fila["alta"],
        baja=fila["baja"],
        pulso=fila["pulso"],
        nota=fila["nota"],
    )


def guardar_tension(con: sqlite3.Connection, tension: Tension) -> int:
    cur = con.execute(
        "INSERT INTO tensiones (fecha_hora, alta, baja, pulso, nota, creada_en)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (
            tension.fecha_hora.strftime(FORMATO),
            tension.alta,
            tension.baja,
            tension.pulso,
            tension.nota,
            datetime.now().strftime(FORMATO),
        ),
    )
    con.commit()
    tension.id = cur.lastrowid
    return tension.id


def obtener_tension(con: sqlite3.Connection, tension_id: int) -> Tension:
    fila = con.execute(
        "SELECT * FROM tensiones WHERE id = ?", (tension_id,)
    ).fetchone()
    if fila is None:
        raise ValueError(f"No hay ninguna toma de tensión con el número {tension_id}")
    return _fila_a_tension(fila)


def actualizar_tension(con: sqlite3.Connection, tension: Tension) -> None:
    con.execute(
        "UPDATE tensiones SET fecha_hora = ?, alta = ?, baja = ?, pulso = ?, nota = ?"
        " WHERE id = ?",
        (
            tension.fecha_hora.strftime(FORMATO),
            tension.alta,
            tension.baja,
            tension.pulso,
            tension.nota,
            tension.id,
        ),
    )
    con.commit()


def listar_tensiones(con: sqlite3.Connection, limite: int = 10) -> list[Tension]:
    """Las últimas tomas, de la más reciente a la más antigua."""
    filas = con.execute(
        "SELECT * FROM tensiones ORDER BY fecha_hora DESC, id DESC LIMIT ?",
        (limite,),
    ).fetchall()
    return [_fila_a_tension(fila) for fila in filas]


def borrar_tension(con: sqlite3.Connection, tension_id: int) -> None:
    con.execute("DELETE FROM tensiones WHERE id = ?", (tension_id,))
    con.commit()


def _fila_a_medicacion(fila: sqlite3.Row) -> Medicacion:
    return Medicacion(
        id=fila["id"],
        nombre=fila["nombre"],
        dosis=fila["dosis"],
        pauta=fila["pauta"],
        activa=bool(fila["activa"]),
    )


def guardar_medicacion(con: sqlite3.Connection, medicacion: Medicacion) -> int:
    cur = con.execute(
        "INSERT INTO medicaciones (nombre, dosis, pauta, activa, creada_en)"
        " VALUES (?, ?, ?, ?, ?)",
        (
            medicacion.nombre,
            medicacion.dosis,
            medicacion.pauta,
            1 if medicacion.activa else 0,
            datetime.now().strftime(FORMATO),
        ),
    )
    con.commit()
    medicacion.id = cur.lastrowid
    return medicacion.id


def obtener_medicacion(con: sqlite3.Connection, medicacion_id: int) -> Medicacion:
    fila = con.execute(
        "SELECT * FROM medicaciones WHERE id = ?", (medicacion_id,)
    ).fetchone()
    if fila is None:
        raise ValueError(f"No hay ningún medicamento con el número {medicacion_id}")
    return _fila_a_medicacion(fila)


def listar_medicaciones(
    con: sqlite3.Connection, solo_activas: bool = True
) -> list[Medicacion]:
    if solo_activas:
        filas = con.execute(
            "SELECT * FROM medicaciones WHERE activa = 1 ORDER BY id"
        ).fetchall()
    else:
        filas = con.execute("SELECT * FROM medicaciones ORDER BY id").fetchall()
    return [_fila_a_medicacion(fila) for fila in filas]


def actualizar_medicacion(con: sqlite3.Connection, medicacion: Medicacion) -> None:
    con.execute(
        "UPDATE medicaciones SET nombre = ?, dosis = ?, pauta = ?, activa = ?"
        " WHERE id = ?",
        (
            medicacion.nombre,
            medicacion.dosis,
            medicacion.pauta,
            1 if medicacion.activa else 0,
            medicacion.id,
        ),
    )
    con.commit()


def borrar_medicacion(con: sqlite3.Connection, medicacion_id: int) -> None:
    con.execute("DELETE FROM medicaciones WHERE id = ?", (medicacion_id,))
    con.commit()


def _fila_a_entrada_historial(fila: sqlite3.Row) -> EntradaHistorial:
    return EntradaHistorial(
        id=fila["id"],
        descripcion=fila["descripcion"],
        fecha=datetime.strptime(fila["fecha"], "%Y-%m-%d").date(),
    )


def guardar_entrada_historial(con: sqlite3.Connection, entrada: EntradaHistorial) -> int:
    cur = con.execute(
        "INSERT INTO historial (descripcion, fecha, creada_en) VALUES (?, ?, ?)",
        (
            entrada.descripcion,
            entrada.fecha.strftime("%Y-%m-%d"),
            datetime.now().strftime(FORMATO),
        ),
    )
    con.commit()
    entrada.id = cur.lastrowid
    return entrada.id


def obtener_entrada_historial(
    con: sqlite3.Connection, entrada_id: int
) -> EntradaHistorial:
    fila = con.execute(
        "SELECT * FROM historial WHERE id = ?", (entrada_id,)
    ).fetchone()
    if fila is None:
        raise ValueError(f"No hay ninguna entrada del historial con el número {entrada_id}")
    return _fila_a_entrada_historial(fila)


def listar_historial(con: sqlite3.Connection) -> list[EntradaHistorial]:
    """Todas las entradas, de la más reciente a la más antigua."""
    filas = con.execute(
        "SELECT * FROM historial ORDER BY fecha DESC, id DESC"
    ).fetchall()
    return [_fila_a_entrada_historial(fila) for fila in filas]


def actualizar_entrada_historial(
    con: sqlite3.Connection, entrada: EntradaHistorial
) -> None:
    con.execute(
        "UPDATE historial SET descripcion = ?, fecha = ? WHERE id = ?",
        (entrada.descripcion, entrada.fecha.strftime("%Y-%m-%d"), entrada.id),
    )
    con.commit()


def borrar_entrada_historial(con: sqlite3.Connection, entrada_id: int) -> None:
    con.execute("DELETE FROM historial WHERE id = ?", (entrada_id,))
    con.commit()
