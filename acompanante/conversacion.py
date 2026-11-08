"""Entiende los mensajes que llegan al bot y prepara la respuesta.

Esta parte no habla con Telegram: recibe el texto y devuelve lo que hay que
contestar. Así se puede probar sin Internet.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from acompanante import db
from acompanante.config import Config
from acompanante.modelos import Tension
from acompanante.textos import fecha_larga, hora_texto

AYUDA = (
    "Puedo hacer estas cosas:\n"
    "1. /proximas: ver tus próximas 5 citas.\n"
    "2. /tension 130 85 72: apuntar una toma de tensión.\n"
    "3. /ayuda: volver a ver esta ayuda."
)

NO_ENTENDIDO = "No te he entendido. Escribe /ayuda para ver lo que sé hacer."

TEXTO_TENSION = "Para apuntar la tensión escribe: /tension 130 85 72"
TEXTO_NUMEROS = (
    "La tensión y el pulso tienen que ser números enteros. "
    "Por ejemplo: /tension 130 85 72"
)


def ahora_local(cfg: Config) -> datetime:
    return datetime.now(ZoneInfo(cfg.zona_horaria)).replace(tzinfo=None, second=0, microsecond=0)


def debe_responder(chat_id: str | int, cfg: Config) -> bool:
    """Solo se contesta al chat que está apuntado en TELEGRAM_CHAT_ID."""
    return bool(cfg.telegram_chat_id) and str(chat_id) == str(cfg.telegram_chat_id)


def _texto_proximas(citas) -> str:
    if not citas:
        return "No tienes citas apuntadas."
    lineas = ["Tus próximas citas:"]
    for posicion, cita in enumerate(citas, start=1):
        linea = (
            f"{posicion}. {fecha_larga(cita.fecha_hora)} a las "
            f"{hora_texto(cita.fecha_hora)}: {cita.titulo}"
        )
        if cita.lugar:
            linea += f" ({cita.lugar})"
        lineas.append(linea)
    return "\n".join(lineas)


def _apuntar_tension(con, cfg: Config, partes: list[str], ahora: datetime) -> str:
    if len(partes) not in (3, 4):
        return TEXTO_TENSION
    try:
        alta = int(partes[1])
        baja = int(partes[2])
        pulso = int(partes[3]) if len(partes) == 4 else None
    except ValueError:
        return TEXTO_NUMEROS

    try:
        tension = Tension(fecha_hora=ahora, alta=alta, baja=baja, pulso=pulso)
    except ValueError as error:
        return str(error)

    db.guardar_tension(con, tension)
    respuesta = f"Apuntado: {alta} de alta, {baja} de baja"
    if pulso is not None:
        respuesta += f", pulso {pulso}"
    return respuesta


def responder(con, cfg: Config, texto: str, ahora: datetime | None = None) -> str:
    """Devuelve la respuesta a un mensaje. Guarda la tensión si hace falta."""
    if ahora is None:
        ahora = ahora_local(cfg)

    partes = texto.strip().split()
    orden = partes[0].lower() if partes else ""
    if orden.startswith("/") and "@" in orden:
        orden = orden.split("@", 1)[0]

    if orden == "/proximas":
        citas = sorted(db.listar_citas(con, desde=ahora), key=lambda cita: cita.fecha_hora)[:5]
        return _texto_proximas(citas)
    if orden == "/tension":
        return _apuntar_tension(con, cfg, partes, ahora)
    if orden == "/ayuda":
        return AYUDA
    return NO_ENTENDIDO
