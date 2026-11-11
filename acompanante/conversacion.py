"""Entiende los mensajes que llegan al bot y prepara la respuesta.

Esta parte no habla con Telegram: recibe el texto y devuelve lo que hay que
contestar. Así se puede probar sin Internet.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from acompanante import db
from acompanante.config import Config
from acompanante.extraer import ErrorExtraccion, extraer_cita
from acompanante.ia import IANoDisponible
from acompanante.modelos import Cita, Tension
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

IA_NO_ACTIVADA = (
    "Apuntar citas con una frase no está activada.\n"
    "Pídeselo a la persona que cuida de la aplicación.\n"
    "Mientras tanto, puedes escribir /ayuda."
)
IA_FALLO = (
    "Ahora mismo no puedo entender la frase.\n"
    "Inténtalo otra vez en un momento.\n"
    "También puedes escribir /ayuda."
)
FALTAN_DATOS = (
    "No sé el día o la hora de la cita.\n"
    "Escríbela otra vez con el día y la hora.\n"
    "Por ejemplo: analítica el 12/11/2026 a las 8:30."
)
PREGUNTA_GUARDAR = "¿La guardo? Responde sí o no."
NO_GUARDADA = "No la he guardado. No se ha apuntado nada."
NO_LEIDO_PAPEL = (
    "No consigo leer bien el papel.\n"
    "Prueba con más luz, o escríbeme la cita."
)

# Citas propuestas que esperan un "sí" o un "no". Se guardan en memoria
# porque solo hay una persona usando el bot.
_pendientes: dict[str, Cita] = {}


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


def _texto_propuesta(cita: Cita) -> str:
    lineas = [
        "He entendido esta cita:",
        cita.titulo,
        f"{fecha_larga(cita.fecha_hora)} a las {hora_texto(cita.fecha_hora)}",
    ]
    if cita.lugar:
        lineas.append(f"Lugar: {cita.lugar}")
    if cita.preparacion:
        lineas.append("Preparación:")
        for posicion, paso in enumerate(cita.preparacion, start=1):
            lineas.append(f"{posicion}. {paso}")
    lineas.append(PREGUNTA_GUARDAR)
    return "\n".join(lineas)


def _texto_cita_guardada(cita: Cita) -> str:
    lineas = [
        "Cita guardada:",
        f"{fecha_larga(cita.fecha_hora)} a las {hora_texto(cita.fecha_hora)}: {cita.titulo}",
    ]
    if cita.lugar:
        lineas.append(f"Lugar: {cita.lugar}")
    return "\n".join(lineas)


def _primera_palabra(texto: str) -> str:
    limpio = texto.strip().lower()
    if not limpio:
        return ""
    return limpio.split()[0].strip(".,;:!¡¿?\"'")


def _clave_chat(chat_id) -> str:
    return "local" if chat_id is None else str(chat_id)


def _responder_frase(
    con, cfg: Config, texto: str, ahora: datetime, chat_id, imagen: bytes | None = None
) -> str:
    """Trata un mensaje que no es una orden como una cita nueva."""
    clave = _clave_chat(chat_id)
    pendiente = _pendientes.get(clave)

    if pendiente is not None:
        if imagen is None and _primera_palabra(texto) in ("sí", "si", "s"):
            db.guardar_cita(con, pendiente)
            del _pendientes[clave]
            return _texto_cita_guardada(pendiente)
        if imagen is None and _primera_palabra(texto) in ("no", "n"):
            del _pendientes[clave]
            return NO_GUARDADA
        # Si escribe otra cosa o manda una foto, se entiende como una cita nueva.
        del _pendientes[clave]

    if cfg.ia_proveedor in ("", "ninguno"):
        return IA_NO_ACTIVADA

    try:
        propuesta = extraer_cita(texto, cfg, ahora=ahora, imagen=imagen)
    except (IANoDisponible, ErrorExtraccion):
        return NO_LEIDO_PAPEL if imagen is not None else IA_FALLO

    if propuesta.faltan_datos:
        return NO_LEIDO_PAPEL if imagen is not None else FALTAN_DATOS

    cita = Cita(
        titulo=propuesta.titulo,
        fecha_hora=propuesta.fecha_hora,
        tipo=propuesta.tipo,
        lugar=propuesta.lugar,
        preparacion=propuesta.preparacion,
    )
    _pendientes[clave] = cita
    return _texto_propuesta(cita)


def responder(
    con,
    cfg: Config,
    texto: str,
    ahora: datetime | None = None,
    chat_id=None,
    imagen: bytes | None = None,
) -> str:
    """Devuelve la respuesta a un mensaje. Guarda la tensión o la cita si hace falta.

    'imagen' son los bytes de una foto del papel de la cita, si la hay.
    """
    if ahora is None:
        ahora = ahora_local(cfg)

    if imagen is not None:
        return _responder_frase(con, cfg, texto, ahora, chat_id, imagen=imagen)

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
    if orden.startswith("/") or not texto.strip():
        return NO_ENTENDIDO
    return _responder_frase(con, cfg, texto, ahora, chat_id)
