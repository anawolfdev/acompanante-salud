"""Acciones con las citas que usan igual la terminal y el bot de Telegram."""

from __future__ import annotations

from datetime import datetime

from acompanante import db
from acompanante.modelos import Cita
from acompanante.plantillas import preparacion_sugerida
from acompanante.textos import fecha_larga, hora_texto


def crear_cita(
    titulo: str,
    fecha_hora: datetime,
    tipo: str = "cita",
    lugar: str = "",
    preparacion: list[str] | None = None,
    notas: str = "",
    sin_sugerencias: bool = False,
) -> Cita:
    """Prepara una cita nueva con la preparación que le corresponde."""
    if not preparacion:
        preparacion = [] if sin_sugerencias else preparacion_sugerida(tipo)
    return Cita(
        titulo=titulo,
        fecha_hora=fecha_hora,
        tipo=tipo,
        lugar=lugar,
        preparacion=preparacion,
        notas=notas,
    )


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


def cambiar_cita(con, cita: Cita, nueva: Cita) -> Cita:
    """Guarda los datos nuevos de la cita.

    Si cambia la fecha o la hora, se olvidan los avisos ya enviados para que
    vuelvan a salir con los datos nuevos.
    """
    if nueva.fecha_hora != cita.fecha_hora:
        db.borrar_avisos_de_cita(con, cita.id)
    db.actualizar_cita(con, nueva)
    return nueva
