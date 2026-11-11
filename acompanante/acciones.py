"""Acciones con las citas que usan igual la terminal y el bot de Telegram."""

from __future__ import annotations

from acompanante import db
from acompanante.modelos import Cita
from acompanante.textos import fecha_larga, hora_texto


def linea_cita(cita: Cita) -> str:
    """Una cita en una línea, con su número entre corchetes."""
    texto = (
        f"[{cita.id}] {fecha_larga(cita.fecha_hora)} a las "
        f"{hora_texto(cita.fecha_hora)}: {cita.titulo}"
    )
    if cita.lugar:
        texto += f" ({cita.lugar})"
    return texto


def cita_para_borrar(con, numero: int) -> Cita:
    """Busca la cita que se quiere borrar. Avisa si ese número no existe."""
    return db.obtener_cita(con, numero)


def borrar_cita(con, cita: Cita) -> None:
    """Borra la cita cuando la persona ya ha dicho que sí."""
    db.borrar_cita(con, cita.id)
