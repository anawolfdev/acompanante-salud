"""Entiende los mensajes que llegan al bot y prepara la respuesta.

Esta parte no habla con Telegram: recibe el texto y devuelve lo que hay que
contestar. Así se puede probar sin Internet.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from acompanante import acciones, db
from acompanante.config import Config
from acompanante.extraer import ErrorExtraccion, extraer_cita
from acompanante.ia import IANoDisponible
from acompanante.modelos import Cita, Tension
from acompanante.textos import (
    fecha_larga,
    hora_texto,
    parsear_fecha,
    parsear_fecha_hora,
    parsear_hora,
)

AYUDA = (
    "Puedo hacer estas cosas:\n"
    "1. /añadir Título | 12/11/2026 8:30 | Lugar: apuntar una cita nueva.\n"
    "2. /citas: ver todas tus citas futuras, con su número.\n"
    "3. /cambiar 3 12/11/2026 8:30: cambiar la fecha y la hora de la cita con ese número.\n"
    "4. /borrar 3: borrar la cita con ese número.\n"
    "5. /tension 130 85 72: apuntar una toma de tensión.\n"
    "6. /ayuda: volver a ver esta ayuda."
)

PROXIMAS_AHORA_CITAS = "Ahora se llama /citas"

NO_ENTENDIDO = "No te he entendido. Escribe /ayuda para ver lo que sé hacer."

TEXTO_TENSION = (
    "Para apuntar la tensión escribe: /tension 130 85 72. "
    "El primer número es la tensión alta, el segundo la baja y el tercero, "
    "si quieres, el pulso."
)
TEXTO_NUMEROS = (
    "Escribe la tensión y el pulso con números. "
    "Por ejemplo: /tension 130 85 72"
)

IA_NO_ACTIVADA = (
    "Todavía no puedo apuntar citas si me las escribes con una frase.\n"
    "Avisa a la persona que se encarga de esta aplicación.\n"
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
PREGUNTA_BORRAR = "¿La borro? Responde sí o no."
NO_BORRADA = "No la he borrado. No se ha borrado nada."
CITA_BORRADA = "Cita borrada."
BORRAR_SIN_NUMERO = (
    "No sé qué cita quieres borrar.\n"
    "Escribe el número después de /borrar. Por ejemplo: /borrar 3\n"
    "Para ver los números, escribe /citas."
)
PREGUNTA_CAMBIAR = "¿La cambio? Responde sí o no."
NO_CAMBIADA = "No la he cambiado. No se ha cambiado nada."
CAMBIO_SIN_DATOS = (
    "No sé qué cita quieres cambiar o cuándo.\n"
    "Escribe el número, la fecha y la hora después de /cambiar.\n"
    "Por ejemplo: /cambiar 3 12/11/2026 8:30\n"
    "Para ver los números, escribe /citas."
)
CAMBIO_FECHA_MAL = (
    "No he entendido la fecha o la hora.\n"
    "Escríbelas así: /cambiar 3 12/11/2026 8:30\n"
    "El número es el que sale en /citas."
)
ANADIR_SIN_DATOS = (
    "No sé qué cita quieres añadir o cuándo.\n"
    "Escribe el título, la fecha y la hora con este formato:\n"
    "/añadir Analítica | 12/11/2026 8:30 | Centro de salud\n"
    "El lugar es opcional."
)
ANADIR_FECHA_MAL = (
    "No he entendido la fecha o la hora.\n"
    "Escríbela así: 12/11/2026 8:30\n"
    "Por ejemplo: /añadir Analítica | 12/11/2026 8:30 | Centro de salud"
)

# Citas propuestas que esperan un "sí" o un "no". Se guardan en memoria
# porque solo hay una persona usando el bot.
_pendientes: dict[str, Cita] = {}

# Citas que esperan un "sí" o un "no" para borrarse.
_borrados_pendientes: dict[str, Cita] = {}

# Cambios de fecha y hora que esperan un "sí" o un "no":
# la cita como está y la cita como quedará.
_cambios_pendientes: dict[str, tuple[Cita, Cita]] = {}


def ahora_local(cfg: Config) -> datetime:
    return datetime.now(ZoneInfo(cfg.zona_horaria)).replace(tzinfo=None, second=0, microsecond=0)


def debe_responder(chat_id: str | int, cfg: Config) -> bool:
    """Solo se contesta al chat que está apuntado en TELEGRAM_CHAT_ID."""
    return bool(cfg.telegram_chat_id) and str(chat_id) == str(cfg.telegram_chat_id)


def _texto_citas(citas) -> str:
    if not citas:
        return "No tienes citas apuntadas."
    lineas = ["Estas son todas tus citas futuras:"]
    for cita in citas:
        lineas.append(acciones.linea_cita(cita))
    return "\n".join(lineas)


def _texto_no_existe(numero: int) -> str:
    return (
        f"No hay ninguna cita con el número {numero}.\n"
        "Escribe /citas para ver los números de tus citas."
    )


def _texto_borrado(cita: Cita) -> str:
    lineas = [
        "Vas a borrar esta cita:",
        acciones.linea_cita(cita),
        PREGUNTA_BORRAR,
    ]
    return "\n".join(lineas)


def _texto_cambio(cita: Cita, nueva: Cita) -> str:
    lineas = [
        "Vas a cambiar esta cita:",
        acciones.linea_cita(cita),
        "Quedará así:",
        acciones.linea_cita(nueva),
        PREGUNTA_CAMBIAR,
    ]
    return "\n".join(lineas)


def _texto_cita_cambiada(cita: Cita) -> str:
    return "\n".join(["Cita cambiada:", acciones.linea_cita(cita)])


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


def _responder_borrado(con, texto: str, chat_id) -> str:
    clave = _clave_chat(chat_id)
    _borrados_pendientes.pop(clave, None)
    _pendientes.pop(clave, None)

    partes = texto.strip().split()
    if len(partes) < 2:
        return BORRAR_SIN_NUMERO
    try:
        numero = int(partes[1])
    except ValueError:
        return BORRAR_SIN_NUMERO

    try:
        cita = acciones.cita_para_borrar(con, numero)
    except ValueError:
        return _texto_no_existe(numero)

    _borrados_pendientes[clave] = cita
    return _texto_borrado(cita)


def _responder_cambiar(con, texto: str, chat_id) -> str:
    clave = _clave_chat(chat_id)
    _cambios_pendientes.pop(clave, None)
    _borrados_pendientes.pop(clave, None)
    _pendientes.pop(clave, None)

    partes = texto.strip().split()
    if len(partes) < 4:
        return CAMBIO_SIN_DATOS
    try:
        numero = int(partes[1])
    except ValueError:
        return CAMBIO_SIN_DATOS

    try:
        fecha_hora = datetime.combine(parsear_fecha(partes[2]), parsear_hora(partes[3]))
    except ValueError:
        return CAMBIO_FECHA_MAL

    try:
        cita = acciones.cita_para_borrar(con, numero)
    except ValueError:
        return _texto_no_existe(numero)

    nueva = Cita(
        titulo=cita.titulo,
        fecha_hora=fecha_hora,
        tipo=cita.tipo,
        lugar=cita.lugar,
        preparacion=cita.preparacion,
        notas=cita.notas,
        id=cita.id,
    )
    _cambios_pendientes[clave] = (cita, nueva)
    return _texto_cambio(cita, nueva)


def _responder_anadir(texto: str, chat_id) -> str:
    clave = _clave_chat(chat_id)
    _pendientes.pop(clave, None)
    _borrados_pendientes.pop(clave, None)
    _cambios_pendientes.pop(clave, None)

    partes = texto.split("|")
    if not 2 <= len(partes) <= 3:
        return ANADIR_SIN_DATOS

    cabecera = partes[0].strip().split(None, 1)
    if len(cabecera) < 2 or not cabecera[1].strip():
        return ANADIR_SIN_DATOS
    titulo = cabecera[1].strip()

    if not partes[1].strip():
        return ANADIR_SIN_DATOS
    try:
        fecha_hora = parsear_fecha_hora(partes[1].strip())
    except ValueError:
        return ANADIR_FECHA_MAL

    lugar = partes[2].strip() if len(partes) == 3 else ""
    try:
        cita = acciones.crear_cita(titulo=titulo, fecha_hora=fecha_hora, lugar=lugar)
    except ValueError:
        return ANADIR_SIN_DATOS

    _pendientes[clave] = cita
    return _texto_propuesta(cita)


def _responder_frase(
    con, cfg: Config, texto: str, ahora: datetime, chat_id, imagen: bytes | None = None
) -> str:
    """Trata un mensaje que no es una orden como una cita nueva."""
    clave = _clave_chat(chat_id)

    pendiente_borrado = _borrados_pendientes.pop(clave, None)
    if pendiente_borrado is not None:
        if imagen is None and _primera_palabra(texto) in ("sí", "si", "s"):
            acciones.borrar_cita(con, pendiente_borrado)
            return CITA_BORRADA
        if imagen is None and _primera_palabra(texto) in ("no", "n"):
            return NO_BORRADA
        # Si escribe otra cosa o manda una foto, se olvida el borrado.

    pendiente_cambio = _cambios_pendientes.pop(clave, None)
    if pendiente_cambio is not None:
        cita, nueva = pendiente_cambio
        if imagen is None and _primera_palabra(texto) in ("sí", "si", "s"):
            acciones.cambiar_cita(con, cita, nueva)
            return _texto_cita_cambiada(nueva)
        if imagen is None and _primera_palabra(texto) in ("no", "n"):
            return NO_CAMBIADA
        # Si escribe otra cosa o manda una foto, se olvida el cambio.

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

    if orden.startswith("/") and orden != "/borrar":
        _borrados_pendientes.pop(_clave_chat(chat_id), None)
    if orden.startswith("/") and orden != "/cambiar":
        _cambios_pendientes.pop(_clave_chat(chat_id), None)
    if orden.startswith("/") and orden != "/añadir":
        _pendientes.pop(_clave_chat(chat_id), None)

    if orden == "/proximas":
        return PROXIMAS_AHORA_CITAS
    if orden == "/añadir":
        return _responder_anadir(texto, chat_id)
    if orden == "/citas":
        citas = sorted(db.listar_citas(con, desde=ahora), key=lambda cita: cita.fecha_hora)
        return _texto_citas(citas)
    if orden == "/cambiar":
        return _responder_cambiar(con, texto, chat_id)
    if orden == "/borrar":
        return _responder_borrado(con, texto, chat_id)
    if orden == "/tension":
        return _apuntar_tension(con, cfg, partes, ahora)
    if orden == "/ayuda":
        return AYUDA
    if orden.startswith("/") or not texto.strip():
        return NO_ENTENDIDO
    return _responder_frase(con, cfg, texto, ahora, chat_id)
