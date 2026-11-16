"""Entiende los mensajes que llegan al bot y prepara la respuesta.

Esta parte no habla con Telegram: recibe el texto y devuelve lo que hay que
contestar. Así se puede probar sin Internet.
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from acompanante import acciones, db
from acompanante.config import Config
from acompanante.extraer import ErrorExtraccion, extraer_cita
from acompanante.ia import IANoDisponible
from acompanante.modelos import Cita, EntradaHistorial, Medicacion, Tension
from acompanante.textos import (
    fecha_larga,
    hora_texto,
    parsear_fecha,
    parsear_fecha_hora,
    parsear_hora,
)


class Respuesta(str):
    """Texto de respuesta y, si hace falta, botones o varios mensajes."""

    def __new__(cls, texto: str, botones=None, mensajes=None):
        respuesta = super().__new__(cls, texto)
        respuesta.botones = botones or []
        respuesta.mensajes = mensajes or []
        return respuesta


def _boton(texto: str, datos: str) -> dict:
    return {"text": texto, "callback_data": datos}


AYUDA = (
    "Puedo hacer estas cosas:\n"
    "1. añadir: apuntar una cita nueva.\n"
    "2. citas: ver tus citas y sus botones.\n"
    "3. tension 130 85 72: apuntar una toma de tensión. Puedes añadir la fecha y la hora al final.\n"
    "4. tensiones: ver tus tomas de tensión y sus botones.\n"
    "5. medicacion: ver tus medicamentos y sus botones.\n"
    "6. medicacion añadir: apuntar un medicamento.\n"
    "7. historial: ver tu historial de salud y sus botones.\n"
    "8. historial añadir: apuntar algo en tu historial de salud.\n"
    "9. ayuda: volver a ver esta ayuda."
)

PROXIMAS_AHORA_CITAS = "Ahora se llama citas"

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

SIN_TENSION = "No tienes ninguna toma de tensión apuntada."
HISTORIAL_CABECERA = "Estas son tus últimas tomas de tensión:"
TENSION_BORRADA = "Toma de tensión borrada."
TENSION_MODIFICADA = "Toma de tensión modificada:"
TENSION_PIDE_VALORES = (
    "Escribe la tensión alta, la baja y el pulso.\n"
    "Por ejemplo: 130 85 72.\n"
    "Si no tienes pulso, escribe solo la alta y la baja: 130 85."
)
TENSION_PIDE_FECHA = (
    "¿Quieres cambiar también la fecha y hora?\n"
    "Escríbela así: 14/11/2026 8:30.\n"
    "Si no, escribe no."
)
TENSION_FECHA_MAL = (
    "No he entendido la fecha o la hora.\n"
    "Escríbela así: 14/11/2026 8:30."
)
TENSION_VALORES_MAL = (
    "No he entendido los valores.\n"
    "Escribe la alta, la baja y, si quieres, el pulso con números.\n"
    "Por ejemplo: 130 85 72."
)

SIN_MEDICACION = (
    "No tienes ningún medicamento apuntado.\n"
    "Para apuntar uno, escribe medicacion añadir."
)
MEDICACION_CABECERA = "Estos son tus medicamentos activos:"
MEDICACION_PIDE_NOMBRE = (
    "¿Cómo se llama el medicamento?\n"
    "Por ejemplo: Paracetamol."
)
MEDICACION_PIDE_DOSIS = "¿Qué dosis?\nPor ejemplo: 1 comprimido."
MEDICACION_PIDE_PAUTA = "¿Cada cuánto lo tomas?\nPor ejemplo: cada 8 horas."
MEDICACION_BORRADA = "Medicamento borrado."
MEDICACION_NO_BORRADA = "No lo he borrado. No se ha borrado nada."
MEDICACION_PREGUNTA_BORRAR = "¿Lo borro? Responde sí o no."
MEDICACION_MODIFICADA = "Medicamento modificado:"
MEDICACION_CAMBIA_NOMBRE = (
    "Nombre actual: {actual}.\n"
    "Escribe el nombre nuevo, o no para dejarlo igual."
)
MEDICACION_CAMBIA_DOSIS = (
    "Dosis actual: {actual}.\n"
    "Escribe la dosis nueva, o no para dejarla igual."
)
MEDICACION_CAMBIA_PAUTA = (
    "Pauta actual: {actual}.\n"
    "Escribe la pauta nueva, o no para dejarla igual."
)

SIN_HISTORIAL = (
    "No tienes ninguna entrada en tu historial de salud.\n"
    "Para apuntar una, escribe historial añadir."
)
HISTORIAL_SALUD_CABECERA = "Estas son las entradas de tu historial de salud:"
HISTORIAL_PIDE_DESCRIPCION = (
    "¿Qué quieres apuntar?\n"
    "Por ejemplo: Analítica de sangre. Todo salió bien."
)
HISTORIAL_PIDE_FECHA = (
    "¿De qué día es?\n"
    "Por ejemplo: 12/11/2026.\n"
    "Si es de hoy, escribe hoy o no."
)
HISTORIAL_FECHA_MAL = (
    "No he entendido la fecha.\n"
    "Escríbela así: 12/11/2026."
)
HISTORIAL_BORRADA = "Entrada del historial borrada."
HISTORIAL_MODIFICADA = "Entrada del historial modificada:"
HISTORIAL_CAMBIA_DESCRIPCION = (
    "Descripción actual:\n"
    "{actual}\n"
    "Escribe la descripción nueva, o no para dejarla igual."
)
HISTORIAL_CAMBIA_FECHA = (
    "Fecha actual: {actual}.\n"
    "Escribe la fecha nueva, o no para dejarla igual."
)
BORRAR_TENSION_SIN_NUMERO = (
    "No sé qué toma de tensión quieres borrar.\n"
    "Escribe el número después de /borrar-tension. Por ejemplo: /borrar-tension 1\n"
    "El número 1 es la toma más reciente. Para verlas, escribe /tensiones."
)
PREGUNTA_GUARDAR_VARIAS = "¿Las guardo? Responde sí o no."
PREGUNTA_BORRAR_VARIAS = "¿Las borro? Responde sí o no."
PREGUNTA_CAMBIAR_VARIAS = "¿Las cambio? Responde sí o no."
CITAS_BORRADAS = "Citas borradas."
BOTON_CADUCADO = "Ese botón ya no vale. Escribe /ayuda para ver lo que sé hacer."
ANADIR_PIDE_TITULO = (
    "¿Cómo se llama la cita?\n"
    "Por ejemplo: Analítica de sangre."
)
ANADIR_PIDE_FECHA = (
    "¿Qué día y a qué hora es?\n"
    "Por ejemplo: 12/11/2026 8:30."
)
ANADIR_PIDE_LUGAR = "¿Dónde es?\nSi no lo sabes, escribe no."
CAMBIO_PIDE_FECHA = (
    "Escribe la nueva fecha y hora.\n"
    "Por ejemplo: 12/11/2026 8:30."
)
CAMBIO_FECHA_MAL_BOTON = (
    "No he entendido la fecha o la hora.\n"
    "Escríbela así: 12/11/2026 8:30."
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
_pendientes: dict[str, list[Cita]] = {}

# Citas que esperan un "sí" o un "no" para borrarse.
_borrados_pendientes: dict[str, list[Cita]] = {}

# Cambios de fecha y hora que esperan un "sí" o un "no":
# cada elemento es la cita como está y la cita como quedará.
_cambios_pendientes: dict[str, list[tuple[Cita, Cita]]] = {}

# Tomas de tensión que esperan un "sí" o un "no" para borrarse.
_tensiones_pendientes: dict[str, Tension] = {}

# Cita que espera la fecha y la hora nuevas después de pulsar "Cambiar".
_cambios_por_boton: dict[str, Cita] = {}

# Toma de tensión que se está modificando después de pulsar "Modificar".
_modificaciones_tension: dict[str, dict] = {}

# Paso a paso de "añadir" cuando no se escribe la cita entera.
_pasos_anadir: dict[str, dict] = {}

# Paso a paso para apuntar un medicamento o una entrada del historial.
_pasos_medicacion: dict[str, dict] = {}
_pasos_historial: dict[str, dict] = {}

# Medicamentos y entradas del historial que esperan un "sí" o un "no" para borrarse.
_medicaciones_pendientes: dict[str, Medicacion] = {}
_historial_pendientes: dict[str, EntradaHistorial] = {}

# Medicamento o entrada del historial que se está modificando con sus pasos.
_modificaciones_medicacion: dict[str, dict] = {}
_modificaciones_historial: dict[str, dict] = {}


def ahora_local(cfg: Config) -> datetime:
    return datetime.now(ZoneInfo(cfg.zona_horaria)).replace(tzinfo=None, second=0, microsecond=0)


def debe_responder(chat_id: str | int, cfg: Config) -> bool:
    """Solo se contesta al chat que está apuntado en TELEGRAM_CHAT_ID."""
    return bool(cfg.telegram_chat_id) and str(chat_id) == str(cfg.telegram_chat_id)


def _respuesta_citas(citas) -> Respuesta:
    if not citas:
        return Respuesta("No tienes citas apuntadas.")
    partes = [Respuesta("Estas son todas tus citas futuras:")]
    for cita in citas:
        partes.append(
            Respuesta(
                acciones.linea_cita(cita),
                botones=[
                    [
                        _boton("Cambiar", f"cambiar:{cita.id}"),
                        _boton("Borrar", f"borrar_cita:{cita.id}"),
                    ]
                ],
            )
        )
    return Respuesta("\n".join(partes), mensajes=partes)


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


def _botones_borrar_citas() -> list[list[dict]]:
    return [
        [
            _boton("Sí", "confirmar_borrar_citas"),
            _boton("No", "cancelar_borrar_citas"),
        ]
    ]


def _respuesta_confirmar_borrado_citas(citas: list[Cita]) -> Respuesta:
    if len(citas) == 1:
        texto = _texto_borrado(citas[0])
    else:
        texto = _texto_borrados(citas)
    return Respuesta(texto, botones=_botones_borrar_citas())


def _texto_pedir_fecha(cita: Cita) -> str:
    return "\n".join(
        [
            "Vas a cambiar esta cita:",
            acciones.linea_cita(cita),
            CAMBIO_PIDE_FECHA,
        ]
    )


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


def _texto_borrados(citas: list[Cita]) -> str:
    lineas = ["Vas a borrar estas citas:"]
    for cita in citas:
        lineas.append(acciones.linea_cita(cita))
    lineas.append(PREGUNTA_BORRAR_VARIAS)
    return "\n".join(lineas)


def _texto_cambios(cambios: list[tuple[Cita, Cita]]) -> str:
    lineas = ["Vas a cambiar estas citas:"]
    for posicion, (cita, nueva) in enumerate(cambios, start=1):
        lineas.append(f"{posicion}. {acciones.linea_cita(cita)}")
        lineas.append("Quedará así:")
        lineas.append(acciones.linea_cita(nueva))
    lineas.append(PREGUNTA_CAMBIAR_VARIAS)
    return "\n".join(lineas)


def _texto_citas_cambiadas(cambios: list[tuple[Cita, Cita]]) -> str:
    lineas = ["Citas cambiadas:"]
    for _cita, nueva in cambios:
        lineas.append(acciones.linea_cita(nueva))
    return "\n".join(lineas)


def _texto_citas_guardadas(citas: list[Cita]) -> str:
    lineas = ["Citas guardadas:"]
    for posicion, cita in enumerate(citas, start=1):
        lineas.append(
            f"{posicion}. {fecha_larga(cita.fecha_hora)} a las "
            f"{hora_texto(cita.fecha_hora)}: {cita.titulo}"
        )
        if cita.lugar:
            lineas.append(f"Lugar: {cita.lugar}")
    return "\n".join(lineas)


def _linea_tension(toma: Tension) -> str:
    texto = (
        f"{fecha_larga(toma.fecha_hora)}, {hora_texto(toma.fecha_hora)}: "
        f"{toma.alta} de alta, {toma.baja} de baja"
    )
    if toma.pulso is not None:
        texto += f", pulso {toma.pulso}"
    if toma.nota:
        texto += f". Nota: {toma.nota}"
    return texto


def _texto_borrado_tension(toma: Tension) -> str:
    return "\n".join(
        [
            "Vas a borrar esta toma de tensión:",
            _linea_tension(toma),
            PREGUNTA_BORRAR,
        ]
    )


def _respuesta_confirmar_borrado_tension(toma: Tension) -> Respuesta:
    botones = [
        [
            _boton("Sí", "confirmar_borrar_tension"),
            _boton("No", "cancelar_borrar_tension"),
        ]
    ]
    return Respuesta(_texto_borrado_tension(toma), botones=botones)


def _texto_no_existe_tension(numero: int) -> str:
    return (
        f"No hay ninguna toma de tensión con el número {numero}.\n"
        "Escribe /tensiones para ver tus últimas tomas."
    )


def _apuntar_tension(con, cfg: Config, partes: list[str], ahora: datetime) -> str:
    resto = partes[1:]
    if len(resto) < 2:
        return TEXTO_TENSION
    try:
        alta = int(resto[0])
        baja = int(resto[1])
    except ValueError:
        return TEXTO_NUMEROS

    pulso = None
    fecha_hora = ahora
    opcionales = resto[2:]

    if len(opcionales) == 1:
        try:
            pulso = int(opcionales[0])
        except ValueError:
            return TEXTO_NUMEROS
    elif len(opcionales) == 2:
        try:
            fecha_hora = parsear_fecha_hora(" ".join(opcionales))
        except ValueError:
            return TENSION_FECHA_MAL
    elif len(opcionales) == 3:
        try:
            pulso = int(opcionales[0])
        except ValueError:
            return TEXTO_NUMEROS
        try:
            fecha_hora = parsear_fecha_hora(" ".join(opcionales[1:]))
        except ValueError:
            return TENSION_FECHA_MAL
    elif len(opcionales) > 3:
        return TEXTO_TENSION

    try:
        tension = Tension(fecha_hora=fecha_hora, alta=alta, baja=baja, pulso=pulso)
    except ValueError as error:
        return str(error)

    db.guardar_tension(con, tension)
    respuesta = f"Apuntado: {alta} de alta, {baja} de baja"
    if pulso is not None:
        respuesta += f", pulso {pulso}"
    if fecha_hora != ahora:
        respuesta += f", el {fecha_larga(fecha_hora)} a las {hora_texto(fecha_hora)}"
    return respuesta


def _valores_tension(texto: str) -> tuple[int, int, int | None]:
    partes = texto.strip().split()
    if len(partes) not in (2, 3):
        raise ValueError(TENSION_VALORES_MAL)
    try:
        alta = int(partes[0])
        baja = int(partes[1])
        pulso = int(partes[2]) if len(partes) == 3 else None
    except ValueError:
        raise ValueError(TENSION_VALORES_MAL) from None
    return alta, baja, pulso


def _texto_tension_modificada(toma: Tension) -> str:
    return f"{TENSION_MODIFICADA}\n{_linea_tension(toma)}"


def _avanzar_modificacion_tension(con, texto: str, clave: str) -> Respuesta:
    """Sigue el paso a paso para cambiar una toma de tensión."""
    estado = _modificaciones_tension[clave]
    toma = estado["toma"]

    if estado["paso"] == "valores":
        try:
            alta, baja, pulso = _valores_tension(texto)
            Tension(fecha_hora=toma.fecha_hora, alta=alta, baja=baja, pulso=pulso)
        except ValueError as error:
            return Respuesta(str(error))
        estado["alta"] = alta
        estado["baja"] = baja
        estado["pulso"] = pulso
        estado["paso"] = "fecha"
        return Respuesta(TENSION_PIDE_FECHA)

    if texto.strip().lower() in ("no", "n"):
        fecha_hora = toma.fecha_hora
    else:
        try:
            fecha_hora = parsear_fecha_hora(texto.strip())
        except ValueError:
            return Respuesta(TENSION_FECHA_MAL)

    nueva = Tension(
        fecha_hora=fecha_hora,
        alta=estado["alta"],
        baja=estado["baja"],
        pulso=estado["pulso"],
        nota=toma.nota,
        id=toma.id,
    )
    db.actualizar_tension(con, nueva)
    _modificaciones_tension.pop(clave, None)
    return Respuesta(_texto_tension_modificada(nueva))


def _respuesta_historial_tension(tomas: list) -> Respuesta:
    """Muestra cada toma en su mensaje, con un botón para modificarla o borrarla."""
    if not tomas:
        return Respuesta(SIN_TENSION)
    partes = [Respuesta(HISTORIAL_CABECERA)]
    for posicion, toma in enumerate(tomas, start=1):
        partes.append(
            Respuesta(
                f"{posicion}. {_linea_tension(toma)}",
                botones=[
                    [
                        _boton("Modificar", f"modificar_tension:{toma.id}"),
                        _boton("Borrar", f"borrar_tension:{toma.id}"),
                    ]
                ],
            )
        )
    return Respuesta("\n".join(partes), mensajes=partes)


def _linea_medicacion(medicacion: Medicacion) -> str:
    return f"{medicacion.nombre}: {medicacion.dosis}, {medicacion.pauta}"


def _respuesta_medicaciones(medicaciones: list[Medicacion]) -> Respuesta:
    """Muestra cada medicamento en su mensaje, con sus botones."""
    if not medicaciones:
        return Respuesta(SIN_MEDICACION)
    partes = [Respuesta(MEDICACION_CABECERA)]
    for posicion, medicacion in enumerate(medicaciones, start=1):
        partes.append(
            Respuesta(
                f"{posicion}. {_linea_medicacion(medicacion)}",
                botones=[
                    [
                        _boton(
                            "Modificar",
                            f"modificar_medicacion:{medicacion.id}",
                        ),
                        _boton("Borrar", f"borrar_medicacion:{medicacion.id}"),
                    ]
                ],
            )
        )
    return Respuesta("\n".join(partes), mensajes=partes)


def _texto_borrado_medicacion(medicacion: Medicacion) -> str:
    return "\n".join(
        [
            "Vas a borrar este medicamento:",
            _linea_medicacion(medicacion),
            MEDICACION_PREGUNTA_BORRAR,
        ]
    )


def _respuesta_confirmar_borrado_medicacion(medicacion: Medicacion) -> Respuesta:
    botones = [
        [
            _boton("Sí", "confirmar_borrar_medicacion"),
            _boton("No", "cancelar_borrar_medicacion"),
        ]
    ]
    return Respuesta(_texto_borrado_medicacion(medicacion), botones=botones)


def _linea_historial(entrada: EntradaHistorial) -> str:
    return f"{fecha_larga(entrada.fecha)}: {entrada.descripcion}"


def _respuesta_historial(entradas: list[EntradaHistorial]) -> Respuesta:
    """Muestra cada entrada en su mensaje, con sus botones."""
    if not entradas:
        return Respuesta(SIN_HISTORIAL)
    partes = [Respuesta(HISTORIAL_SALUD_CABECERA)]
    for posicion, entrada in enumerate(entradas, start=1):
        partes.append(
            Respuesta(
                f"{posicion}. {_linea_historial(entrada)}",
                botones=[
                    [
                        _boton("Modificar", f"modificar_historial:{entrada.id}"),
                        _boton("Borrar", f"borrar_historial:{entrada.id}"),
                    ]
                ],
            )
        )
    return Respuesta("\n".join(partes), mensajes=partes)


def _texto_borrado_historial(entrada: EntradaHistorial) -> str:
    return "\n".join(
        [
            "Vas a borrar esta entrada del historial:",
            _linea_historial(entrada),
            PREGUNTA_BORRAR,
        ]
    )


def _respuesta_confirmar_borrado_historial(entrada: EntradaHistorial) -> Respuesta:
    botones = [
        [
            _boton("Sí", "confirmar_borrar_historial"),
            _boton("No", "cancelar_borrar_historial"),
        ]
    ]
    return Respuesta(_texto_borrado_historial(entrada), botones=botones)


def _fecha_de_hoy(texto: str, ahora: datetime) -> date:
    """Para el historial: 'hoy', 'no' o nada significa el día de hoy."""
    limpio = texto.strip().lower()
    if limpio in ("hoy", "no", "n", ""):
        return ahora.date()
    return parsear_fecha(texto.strip())


def _avanzar_paso_medicacion(con, texto: str, clave: str) -> Respuesta:
    """Sigue el paso a paso para apuntar un medicamento."""
    estado = _pasos_medicacion[clave]
    limpio = texto.strip()

    if estado["paso"] == "nombre":
        if not limpio:
            return Respuesta(MEDICACION_PIDE_NOMBRE)
        estado["nombre"] = limpio
        estado["paso"] = "dosis"
        return Respuesta(MEDICACION_PIDE_DOSIS)

    if estado["paso"] == "dosis":
        if not limpio:
            return Respuesta(MEDICACION_PIDE_DOSIS)
        estado["dosis"] = limpio
        estado["paso"] = "pauta"
        return Respuesta(MEDICACION_PIDE_PAUTA)

    if estado["paso"] == "pauta":
        if not limpio:
            return Respuesta(MEDICACION_PIDE_PAUTA)
        try:
            medicacion = Medicacion(
                nombre=estado["nombre"],
                dosis=estado["dosis"],
                pauta=limpio,
            )
        except ValueError as error:
            return Respuesta(str(error))
        db.guardar_medicacion(con, medicacion)
        _pasos_medicacion.pop(clave, None)
        return Respuesta(f"Medicamento guardado:\n{_linea_medicacion(medicacion)}")

    _pasos_medicacion.pop(clave, None)
    return Respuesta(NO_ENTENDIDO)


def _avanzar_modificacion_medicacion(con, texto: str, clave: str) -> Respuesta:
    """Sigue el paso a paso para cambiar un medicamento."""
    estado = _modificaciones_medicacion[clave]
    medicacion = estado["medicacion"]
    limpio = texto.strip()

    if estado["paso"] == "nombre":
        if limpio and limpio.lower() not in ("no", "n"):
            estado["nombre"] = limpio
        estado["paso"] = "dosis"
        return Respuesta(MEDICACION_CAMBIA_DOSIS.format(actual=estado["dosis"]))

    if estado["paso"] == "dosis":
        if limpio and limpio.lower() not in ("no", "n"):
            estado["dosis"] = limpio
        estado["paso"] = "pauta"
        return Respuesta(MEDICACION_CAMBIA_PAUTA.format(actual=estado["pauta"]))

    if estado["paso"] == "pauta":
        if limpio and limpio.lower() not in ("no", "n"):
            estado["pauta"] = limpio
        try:
            nueva = Medicacion(
                nombre=estado["nombre"],
                dosis=estado["dosis"],
                pauta=estado["pauta"],
                activa=medicacion.activa,
                id=medicacion.id,
            )
        except ValueError as error:
            return Respuesta(str(error))
        db.actualizar_medicacion(con, nueva)
        _modificaciones_medicacion.pop(clave, None)
        return Respuesta(f"{MEDICACION_MODIFICADA}\n{_linea_medicacion(nueva)}")

    _modificaciones_medicacion.pop(clave, None)
    return Respuesta(NO_ENTENDIDO)


def _avanzar_paso_historial(con, texto: str, clave: str, ahora: datetime) -> Respuesta:
    """Sigue el paso a paso para apuntar una entrada del historial."""
    estado = _pasos_historial[clave]
    limpio = texto.strip()

    if estado["paso"] == "descripcion":
        if not limpio:
            return Respuesta(HISTORIAL_PIDE_DESCRIPCION)
        estado["descripcion"] = limpio
        estado["paso"] = "fecha"
        return Respuesta(HISTORIAL_PIDE_FECHA)

    if estado["paso"] == "fecha":
        try:
            fecha = _fecha_de_hoy(limpio, ahora)
        except ValueError:
            return Respuesta(HISTORIAL_FECHA_MAL)
        try:
            entrada = EntradaHistorial(
                descripcion=estado["descripcion"], fecha=fecha
            )
        except ValueError as error:
            return Respuesta(str(error))
        db.guardar_entrada_historial(con, entrada)
        _pasos_historial.pop(clave, None)
        return Respuesta(f"Entrada guardada:\n{_linea_historial(entrada)}")

    _pasos_historial.pop(clave, None)
    return Respuesta(NO_ENTENDIDO)


def _avanzar_modificacion_historial(
    con, texto: str, clave: str, ahora: datetime
) -> Respuesta:
    """Sigue el paso a paso para cambiar una entrada del historial."""
    estado = _modificaciones_historial[clave]
    entrada = estado["entrada"]
    limpio = texto.strip()

    if estado["paso"] == "descripcion":
        if limpio and limpio.lower() not in ("no", "n"):
            estado["descripcion"] = limpio
        estado["paso"] = "fecha"
        return Respuesta(
            HISTORIAL_CAMBIA_FECHA.format(actual=fecha_larga(estado["fecha"]))
        )

    if estado["paso"] == "fecha":
        limpio_minusculas = limpio.lower()
        if limpio_minusculas in ("no", "n", ""):
            fecha = estado["fecha"]
        elif limpio_minusculas == "hoy":
            fecha = ahora.date()
        else:
            try:
                fecha = parsear_fecha(limpio)
            except ValueError:
                return Respuesta(HISTORIAL_FECHA_MAL)
        try:
            nueva = EntradaHistorial(
                descripcion=estado["descripcion"],
                fecha=fecha,
                id=entrada.id,
            )
        except ValueError as error:
            return Respuesta(str(error))
        db.actualizar_entrada_historial(con, nueva)
        _modificaciones_historial.pop(clave, None)
        return Respuesta(f"{HISTORIAL_MODIFICADA}\n{_linea_historial(nueva)}")

    _modificaciones_historial.pop(clave, None)
    return Respuesta(NO_ENTENDIDO)


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


def _texto_propuestas(citas: list[Cita]) -> str:
    """Una propuesta de cita, o una lista si se han escrito varias."""
    if len(citas) == 1:
        return _texto_propuesta(citas[0])

    lineas = ["He entendido estas citas:"]
    for posicion, cita in enumerate(citas, start=1):
        lineas.append(f"{posicion}. {cita.titulo}")
        lineas.append(
            f"{fecha_larga(cita.fecha_hora)} a las {hora_texto(cita.fecha_hora)}"
        )
        if cita.lugar:
            lineas.append(f"Lugar: {cita.lugar}")
        if cita.preparacion:
            lineas.append("Preparación:")
            for paso_posicion, paso in enumerate(cita.preparacion, start=1):
                lineas.append(f"{paso_posicion}. {paso}")
    lineas.append(PREGUNTA_GUARDAR_VARIAS)
    return "\n".join(lineas)


# Conjunto de órdenes conocidas (sin la barra) para detectar si un mensaje es una orden.
# Valor True = la orden requiere argumentos; False = orden simple (sin argumentos).
_ORDENES_CONOCIDAS: dict[str, bool] = {
    "ayuda": False,
    "citas": False,
    "proximas": False,
    "añadir": True,
    "cambiar": True,
    "borrar": True,
    "borrar-tension": True,
    "tension": True,
    "tensiones": False,
    "medicacion": False,
    "historial": False,
}


def _parsear_orden(texto: str) -> tuple[str, str]:
    """Extrae la orden y el resto del mensaje.

    Acepta órdenes con o sin barra inicial (ej: "/ayuda" o "ayuda").
    Si hay @usuario (ej: "/ayuda@mibot"), se quita.
    Devuelve (orden_sin_barra, resto_del_mensaje).
    """
    limpio = texto.strip()
    if not limpio:
        return "", ""

    partes = limpio.split(maxsplit=1)
    primera = partes[0].lower()
    resto = partes[1] if len(partes) > 1 else ""

    # Quitar @usuario si está (formato de Telegram: /orden@botname)
    if "@" in primera:
        primera = primera.split("@", 1)[0]

    # Quitar barra inicial si la hay
    if primera.startswith("/"):
        primera = primera[1:]

    # Telegram no permite guiones en los nombres de comando, así que se
    # acepta /borrar_tension igual que /borrar-tension.
    if primera == "borrar_tension":
        primera = "borrar-tension"
    if primera == "anadir":
        primera = "añadir"

    return primera, resto


def _es_anadir(resto: str) -> bool:
    return resto.strip().lower() in ("anadir", "añadir", "nuevo", "nueva")


def _es_orden_valida(orden: str, resto: str, texto_original: str) -> bool:
    """Comprueba si el mensaje parece una invocación de orden válida.

    - Órdenes simples (ayuda, citas, proximas): el mensaje debe ser exactamente la orden.
    - Órdenes con argumentos (añadir, cambiar, borrar, tension): debe haber resto.
    - Si el mensaje original empieza por "/", se acepta cualquier orden conocida.
    """
    if orden not in _ORDENES_CONOCIDAS:
        return False

    # "añadir" es válido con o sin datos: sin datos empieza el paso a paso.
    if orden == "añadir":
        return True

    # "medicacion" e "historial" pueden llevar "anadir" para empezar el paso a paso.
    if orden in ("medicacion", "historial") and _es_anadir(resto):
        return True

    # Si el original empieza por "/", es explícitamente una orden
    if texto_original.strip().startswith("/"):
        return True

    # Sin barra: validar según si requiere argumentos
    requiere_args = _ORDENES_CONOCIDAS[orden]
    if requiere_args:
        # Debe haber algo después de la orden
        return bool(resto.strip())
    else:
        # Orden simple: no debe haber resto (solo espacios)
        return not resto.strip()


def _primera_palabra(texto: str) -> str:
    limpio = texto.strip().lower()
    if not limpio:
        return ""
    return limpio.split()[0].strip(".,;:!¡¿?\"'")


def _clave_chat(chat_id) -> str:
    return "local" if chat_id is None else str(chat_id)


def _responder_borrar_tension(con, resto: str, clave: str) -> str:
    partes = resto.split()
    if len(partes) != 1:
        return BORRAR_TENSION_SIN_NUMERO
    try:
        numero = int(partes[0])
    except ValueError:
        return BORRAR_TENSION_SIN_NUMERO

    tomas = db.listar_tensiones(con)
    if numero < 1 or numero > len(tomas):
        return _texto_no_existe_tension(numero)

    toma = tomas[numero - 1]
    _tensiones_pendientes[clave] = toma
    return _respuesta_confirmar_borrado_tension(toma)


def _responder_borrado(con, texto: str, chat_id) -> str:
    clave = _clave_chat(chat_id)
    _borrados_pendientes.pop(clave, None)
    _pendientes.pop(clave, None)
    _cambios_pendientes.pop(clave, None)
    _tensiones_pendientes.pop(clave, None)

    orden, resto = _parsear_orden(texto)

    if orden == "borrar-tension":
        return _responder_borrar_tension(con, resto, clave)

    partes = resto.split()
    if partes and partes[0].lower() == "tension":
        return _responder_borrar_tension(con, " ".join(partes[1:]), clave)

    if not partes:
        return BORRAR_SIN_NUMERO

    numeros = []
    for parte in partes:
        try:
            numero = int(parte)
        except ValueError:
            return BORRAR_SIN_NUMERO
        if numero not in numeros:
            numeros.append(numero)

    citas = []
    for numero in numeros:
        try:
            citas.append(acciones.cita_para_borrar(con, numero))
        except ValueError:
            return _texto_no_existe(numero)

    _borrados_pendientes[clave] = citas
    return _respuesta_confirmar_borrado_citas(citas)


def _responder_cambiar(con, texto: str, chat_id) -> str:
    clave = _clave_chat(chat_id)
    _cambios_pendientes.pop(clave, None)
    _borrados_pendientes.pop(clave, None)
    _pendientes.pop(clave, None)
    _tensiones_pendientes.pop(clave, None)

    _orden, resto = _parsear_orden(texto)
    bloques = [bloque.strip() for bloque in resto.split(";") if bloque.strip()]
    if not bloques:
        return CAMBIO_SIN_DATOS

    cambios: list[tuple[Cita, Cita]] = []
    for bloque in bloques:
        partes = bloque.split()
        if len(partes) < 3:
            return CAMBIO_SIN_DATOS
        try:
            numero = int(partes[0])
        except ValueError:
            return CAMBIO_SIN_DATOS

        try:
            fecha_hora = datetime.combine(
                parsear_fecha(partes[1]), parsear_hora(partes[2])
            )
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
        cambios.append((cita, nueva))

    _cambios_pendientes[clave] = cambios
    if len(cambios) == 1:
        return _texto_cambio(*cambios[0])
    return _texto_cambios(cambios)


def _responder_anadir(texto: str, chat_id) -> str:
    clave = _clave_chat(chat_id)
    _pendientes.pop(clave, None)
    _borrados_pendientes.pop(clave, None)
    _cambios_pendientes.pop(clave, None)
    _tensiones_pendientes.pop(clave, None)

    _orden, resto = _parsear_orden(texto)
    bloques = [bloque.strip() for bloque in resto.split(";") if bloque.strip()]
    if not bloques:
        _pasos_anadir[clave] = {"paso": "titulo"}
        return Respuesta(ANADIR_PIDE_TITULO)

    citas = []
    for bloque in bloques:
        partes = [parte.strip() for parte in bloque.split("|")]
        if not 2 <= len(partes) <= 3:
            return ANADIR_SIN_DATOS

        titulo = partes[0]
        if not titulo:
            return ANADIR_SIN_DATOS

        if not partes[1]:
            return ANADIR_SIN_DATOS
        try:
            fecha_hora = parsear_fecha_hora(partes[1])
        except ValueError:
            return ANADIR_FECHA_MAL

        lugar = partes[2] if len(partes) == 3 else ""
        if lugar.lower().startswith("lugar") and ":" in lugar:
            lugar = lugar.split(":", 1)[1].strip()

        try:
            cita = acciones.crear_cita(
                titulo=titulo, fecha_hora=fecha_hora, lugar=lugar
            )
        except ValueError:
            return ANADIR_SIN_DATOS
        citas.append(cita)

    _pendientes[clave] = citas
    return _texto_propuestas(citas)


def _avanzar_paso_anadir(con, texto: str, clave: str) -> Respuesta:
    """Sigue el paso a paso de 'añadir' con lo que ha escrito la persona."""
    borrador = _pasos_anadir[clave]
    paso = borrador.get("paso")
    limpio = texto.strip()

    if paso == "titulo":
        if not limpio:
            return Respuesta(ANADIR_PIDE_TITULO)
        borrador["titulo"] = limpio
        borrador["paso"] = "fecha"
        return Respuesta(ANADIR_PIDE_FECHA)

    if paso == "fecha":
        try:
            fecha_hora = parsear_fecha_hora(limpio)
        except ValueError:
            return Respuesta(ANADIR_PIDE_FECHA)
        borrador["fecha_hora"] = fecha_hora
        borrador["paso"] = "lugar"
        return Respuesta(ANADIR_PIDE_LUGAR)

    if paso == "lugar":
        lugar = ""
        if limpio.lower() not in ("no", "n"):
            lugar = limpio
            if lugar.lower().startswith("lugar") and ":" in lugar:
                lugar = lugar.split(":", 1)[1].strip()
        try:
            cita = acciones.crear_cita(
                titulo=borrador["titulo"],
                fecha_hora=borrador["fecha_hora"],
                lugar=lugar,
            )
        except ValueError:
            _pasos_anadir.pop(clave, None)
            return Respuesta(ANADIR_SIN_DATOS)
        _pasos_anadir.pop(clave, None)
        _pendientes[clave] = [cita]
        return Respuesta(_texto_propuesta(cita))

    _pasos_anadir.pop(clave, None)
    return Respuesta(ANADIR_SIN_DATOS)


def _responder_frase(
    con, cfg: Config, texto: str, ahora: datetime, chat_id, imagen: bytes | None = None
) -> str:
    """Trata un mensaje que no es una orden como una cita nueva."""
    clave = _clave_chat(chat_id)

    if clave in _pasos_anadir:
        return _avanzar_paso_anadir(con, texto, clave)

    if clave in _pasos_medicacion:
        return _avanzar_paso_medicacion(con, texto, clave)

    if clave in _pasos_historial:
        return _avanzar_paso_historial(con, texto, clave, ahora)

    if clave in _modificaciones_medicacion:
        return _avanzar_modificacion_medicacion(con, texto, clave)

    if clave in _modificaciones_historial:
        return _avanzar_modificacion_historial(con, texto, clave, ahora)

    if clave in _modificaciones_tension:
        return _avanzar_modificacion_tension(con, texto, clave)

    cita_a_cambiar = _cambios_por_boton.get(clave)
    if cita_a_cambiar is not None:
        try:
            fecha_hora = parsear_fecha_hora(texto.strip())
        except ValueError:
            return Respuesta(CAMBIO_FECHA_MAL_BOTON)
        nueva = Cita(
            titulo=cita_a_cambiar.titulo,
            fecha_hora=fecha_hora,
            tipo=cita_a_cambiar.tipo,
            lugar=cita_a_cambiar.lugar,
            preparacion=cita_a_cambiar.preparacion,
            notas=cita_a_cambiar.notas,
            id=cita_a_cambiar.id,
        )
        acciones.cambiar_cita(con, cita_a_cambiar, nueva)
        _cambios_por_boton.pop(clave, None)
        return Respuesta(_texto_cita_cambiada(nueva))

    pendiente_medicacion = _medicaciones_pendientes.pop(clave, None)
    if pendiente_medicacion is not None:
        if imagen is None and _primera_palabra(texto) in ("sí", "si", "s"):
            db.borrar_medicacion(con, pendiente_medicacion.id)
            return MEDICACION_BORRADA
        if imagen is None and _primera_palabra(texto) in ("no", "n"):
            return MEDICACION_NO_BORRADA
        # Si escribe otra cosa o manda una foto, se olvida el borrado.

    pendiente_historial = _historial_pendientes.pop(clave, None)
    if pendiente_historial is not None:
        if imagen is None and _primera_palabra(texto) in ("sí", "si", "s"):
            db.borrar_entrada_historial(con, pendiente_historial.id)
            return HISTORIAL_BORRADA
        if imagen is None and _primera_palabra(texto) in ("no", "n"):
            return NO_BORRADA
        # Si escribe otra cosa o manda una foto, se olvida el borrado.

    pendiente_tension = _tensiones_pendientes.pop(clave, None)
    if pendiente_tension is not None:
        if imagen is None and _primera_palabra(texto) in ("sí", "si", "s"):
            db.borrar_tension(con, pendiente_tension.id)
            return TENSION_BORRADA
        if imagen is None and _primera_palabra(texto) in ("no", "n"):
            return NO_BORRADA
        # Si escribe otra cosa o manda una foto, se olvida el borrado.

    pendiente_borrado = _borrados_pendientes.pop(clave, None)
    if pendiente_borrado:
        if imagen is None and _primera_palabra(texto) in ("sí", "si", "s"):
            for cita in pendiente_borrado:
                acciones.borrar_cita(con, cita)
            if len(pendiente_borrado) == 1:
                return CITA_BORRADA
            return CITAS_BORRADAS
        if imagen is None and _primera_palabra(texto) in ("no", "n"):
            return NO_BORRADA
        # Si escribe otra cosa o manda una foto, se olvida el borrado.

    pendiente_cambio = _cambios_pendientes.pop(clave, None)
    if pendiente_cambio:
        if imagen is None and _primera_palabra(texto) in ("sí", "si", "s"):
            for cita, nueva in pendiente_cambio:
                acciones.cambiar_cita(con, cita, nueva)
            if len(pendiente_cambio) == 1:
                return _texto_cita_cambiada(pendiente_cambio[0][1])
            return _texto_citas_cambiadas(pendiente_cambio)
        if imagen is None and _primera_palabra(texto) in ("no", "n"):
            return NO_CAMBIADA
        # Si escribe otra cosa o manda una foto, se olvida el cambio.

    pendiente = _pendientes.pop(clave, None)

    if pendiente:
        if imagen is None and _primera_palabra(texto) in ("sí", "si", "s"):
            for cita in pendiente:
                db.guardar_cita(con, cita)
            if len(pendiente) == 1:
                return _texto_cita_guardada(pendiente[0])
            return _texto_citas_guardadas(pendiente)
        if imagen is None and _primera_palabra(texto) in ("no", "n"):
            return NO_GUARDADA
        # Si escribe otra cosa o manda una foto, se entiende como una cita nueva.

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
    _pendientes[clave] = [cita]
    return _texto_propuesta(cita)


def _responder(
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

    # Extraer la orden (con o sin barra) y el resto del mensaje
    orden, resto = _parsear_orden(texto)

    # Comprobar si es una invocación de orden válida
    es_orden = _es_orden_valida(orden, resto, texto)

    # Si es una orden válida, limpiar estados pendientes de otras órdenes
    if es_orden:
        clave = _clave_chat(chat_id)
        if orden not in ("borrar", "borrar-tension"):
            _borrados_pendientes.pop(clave, None)
        if orden != "cambiar":
            _cambios_pendientes.pop(clave, None)
        if orden != "añadir":
            _pendientes.pop(clave, None)
        if orden not in ("borrar", "borrar-tension"):
            _tensiones_pendientes.pop(clave, None)
        _pasos_anadir.pop(clave, None)
        _cambios_por_boton.pop(clave, None)
        _modificaciones_tension.pop(clave, None)
        _pasos_medicacion.pop(clave, None)
        _pasos_historial.pop(clave, None)
        _medicaciones_pendientes.pop(clave, None)
        _historial_pendientes.pop(clave, None)
        _modificaciones_medicacion.pop(clave, None)
        _modificaciones_historial.pop(clave, None)

    # Procesar órdenes conocidas
    if es_orden and orden == "proximas":
        return PROXIMAS_AHORA_CITAS
    if es_orden and orden == "añadir":
        return _responder_anadir(texto, chat_id)
    if es_orden and orden == "citas":
        citas = sorted(db.listar_citas(con, desde=ahora), key=lambda cita: cita.fecha_hora)
        return _respuesta_citas(citas)
    if es_orden and orden == "cambiar":
        return _responder_cambiar(con, texto, chat_id)
    if es_orden and orden in ("borrar", "borrar-tension"):
        return _responder_borrado(con, texto, chat_id)
    if es_orden and orden == "tension":
        # Para tension, necesitamos las partes separadas como antes
        partes = texto.strip().split()
        return _apuntar_tension(con, cfg, partes, ahora)
    if es_orden and orden == "tensiones":
        tomas = db.listar_tensiones(con)
        return _respuesta_historial_tension(tomas)
    if es_orden and orden == "medicacion":
        if _es_anadir(resto):
            clave = _clave_chat(chat_id)
            _pasos_medicacion[clave] = {"paso": "nombre"}
            return Respuesta(MEDICACION_PIDE_NOMBRE)
        return _respuesta_medicaciones(db.listar_medicaciones(con))
    if es_orden and orden == "historial":
        if _es_anadir(resto):
            clave = _clave_chat(chat_id)
            _pasos_historial[clave] = {"paso": "descripcion"}
            return Respuesta(HISTORIAL_PIDE_DESCRIPCION)
        return _respuesta_historial(db.listar_historial(con))
    if es_orden and orden == "ayuda":
        return AYUDA

    # Si el mensaje original empieza por "/" pero no es una orden válida, no se entiende
    if texto.strip().startswith("/") or not texto.strip():
        return NO_ENTENDIDO

    # Si no es una orden válida ni empieza por "/", tratarlo como frase natural
    return _responder_frase(con, cfg, texto, ahora, chat_id)


def responder(
    con,
    cfg: Config,
    texto: str,
    ahora: datetime | None = None,
    chat_id=None,
    imagen: bytes | None = None,
) -> Respuesta:
    """Igual que _responder, pero siempre devuelve una Respuesta con botones."""
    resultado = _responder(
        con, cfg, texto, ahora=ahora, chat_id=chat_id, imagen=imagen
    )
    if isinstance(resultado, Respuesta):
        return resultado
    return Respuesta(resultado)


def _cita_por_id(con, valor: str) -> Cita | None:
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None
    try:
        return acciones.cita_para_borrar(con, numero)
    except ValueError:
        return None


def _tension_por_id(con, valor: str) -> Tension | None:
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None
    try:
        return db.obtener_tension(con, numero)
    except ValueError:
        return None


def _medicacion_por_id(con, valor: str) -> Medicacion | None:
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None
    try:
        return db.obtener_medicacion(con, numero)
    except ValueError:
        return None


def _historial_por_id(con, valor: str) -> EntradaHistorial | None:
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None
    try:
        return db.obtener_entrada_historial(con, numero)
    except ValueError:
        return None


def _limpiar_pendientes(clave: str) -> None:
    _pendientes.pop(clave, None)
    _borrados_pendientes.pop(clave, None)
    _cambios_pendientes.pop(clave, None)
    _tensiones_pendientes.pop(clave, None)
    _cambios_por_boton.pop(clave, None)
    _modificaciones_tension.pop(clave, None)
    _pasos_anadir.pop(clave, None)
    _pasos_medicacion.pop(clave, None)
    _pasos_historial.pop(clave, None)
    _medicaciones_pendientes.pop(clave, None)
    _historial_pendientes.pop(clave, None)
    _modificaciones_medicacion.pop(clave, None)
    _modificaciones_historial.pop(clave, None)


def responder_callback(con, cfg: Config, datos: str, chat_id=None) -> Respuesta:
    """Responde a un botón pulsado en Telegram."""
    clave = _clave_chat(chat_id)
    prefijo, _, valor = datos.partition(":")

    if prefijo == "cambiar":
        cita = _cita_por_id(con, valor)
        if cita is None:
            return Respuesta(BOTON_CADUCADO)
        _limpiar_pendientes(clave)
        _cambios_por_boton[clave] = cita
        return Respuesta(_texto_pedir_fecha(cita))

    if prefijo == "borrar_cita":
        cita = _cita_por_id(con, valor)
        if cita is None:
            return Respuesta(BOTON_CADUCADO)
        _limpiar_pendientes(clave)
        _borrados_pendientes[clave] = [cita]
        return _respuesta_confirmar_borrado_citas([cita])

    if prefijo == "borrar_tension":
        toma = _tension_por_id(con, valor)
        if toma is None:
            return Respuesta(BOTON_CADUCADO)
        _limpiar_pendientes(clave)
        _tensiones_pendientes[clave] = toma
        return _respuesta_confirmar_borrado_tension(toma)

    if prefijo == "modificar_tension":
        toma = _tension_por_id(con, valor)
        if toma is None:
            return Respuesta(BOTON_CADUCADO)
        _limpiar_pendientes(clave)
        _modificaciones_tension[clave] = {"toma": toma, "paso": "valores"}
        return Respuesta(TENSION_PIDE_VALORES)

    if prefijo == "borrar_medicacion":
        medicacion = _medicacion_por_id(con, valor)
        if medicacion is None:
            return Respuesta(BOTON_CADUCADO)
        _limpiar_pendientes(clave)
        _medicaciones_pendientes[clave] = medicacion
        return _respuesta_confirmar_borrado_medicacion(medicacion)

    if prefijo == "modificar_medicacion":
        medicacion = _medicacion_por_id(con, valor)
        if medicacion is None:
            return Respuesta(BOTON_CADUCADO)
        _limpiar_pendientes(clave)
        _modificaciones_medicacion[clave] = {
            "medicacion": medicacion,
            "paso": "nombre",
            "nombre": medicacion.nombre,
            "dosis": medicacion.dosis,
            "pauta": medicacion.pauta,
        }
        return Respuesta(
            MEDICACION_CAMBIA_NOMBRE.format(actual=medicacion.nombre)
        )

    if prefijo == "borrar_historial":
        entrada = _historial_por_id(con, valor)
        if entrada is None:
            return Respuesta(BOTON_CADUCADO)
        _limpiar_pendientes(clave)
        _historial_pendientes[clave] = entrada
        return _respuesta_confirmar_borrado_historial(entrada)

    if prefijo == "modificar_historial":
        entrada = _historial_por_id(con, valor)
        if entrada is None:
            return Respuesta(BOTON_CADUCADO)
        _limpiar_pendientes(clave)
        _modificaciones_historial[clave] = {
            "entrada": entrada,
            "paso": "descripcion",
            "descripcion": entrada.descripcion,
            "fecha": entrada.fecha,
        }
        return Respuesta(
            HISTORIAL_CAMBIA_DESCRIPCION.format(actual=entrada.descripcion)
        )

    if datos == "confirmar_borrar_citas":
        citas = _borrados_pendientes.pop(clave, [])
        if not citas:
            return Respuesta(BOTON_CADUCADO)
        for cita in citas:
            acciones.borrar_cita(con, cita)
        if len(citas) == 1:
            return Respuesta(CITA_BORRADA)
        return Respuesta(CITAS_BORRADAS)

    if datos == "cancelar_borrar_citas":
        _borrados_pendientes.pop(clave, None)
        return Respuesta(NO_BORRADA)

    if datos == "confirmar_borrar_tension":
        toma = _tensiones_pendientes.pop(clave, None)
        if toma is None:
            return Respuesta(BOTON_CADUCADO)
        db.borrar_tension(con, toma.id)
        return Respuesta(TENSION_BORRADA)

    if datos == "cancelar_borrar_tension":
        _tensiones_pendientes.pop(clave, None)
        return Respuesta(NO_BORRADA)

    if datos == "confirmar_borrar_medicacion":
        medicacion = _medicaciones_pendientes.pop(clave, None)
        if medicacion is None:
            return Respuesta(BOTON_CADUCADO)
        db.borrar_medicacion(con, medicacion.id)
        return Respuesta(MEDICACION_BORRADA)

    if datos == "cancelar_borrar_medicacion":
        _medicaciones_pendientes.pop(clave, None)
        return Respuesta(MEDICACION_NO_BORRADA)

    if datos == "confirmar_borrar_historial":
        entrada = _historial_pendientes.pop(clave, None)
        if entrada is None:
            return Respuesta(BOTON_CADUCADO)
        db.borrar_entrada_historial(con, entrada.id)
        return Respuesta(HISTORIAL_BORRADA)

    if datos == "cancelar_borrar_historial":
        _historial_pendientes.pop(clave, None)
        return Respuesta(NO_BORRADA)

    return Respuesta(BOTON_CADUCADO)
