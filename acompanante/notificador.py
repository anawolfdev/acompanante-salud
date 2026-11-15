"""Canales por los que salen los avisos: consola (para probar) y Telegram."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from acompanante.config import Config


class ErrorDeEnvio(Exception):
    """No se pudo mandar el aviso."""


class NotificadorConsola:
    """Escribe el aviso en la pantalla. Útil para probar sin Telegram."""

    def enviar(self, texto: str) -> None:
        print("-" * 40)
        print(texto)
        print("-" * 40)


class NotificadorTelegram:
    """Manda el aviso como mensaje de Telegram con la API oficial de bots (gratis)."""

    URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, token: str, chat_id: str, abrir=urllib.request.urlopen) -> None:
        if not token or not chat_id:
            raise ErrorDeEnvio(
                "Falta TELEGRAM_TOKEN o TELEGRAM_CHAT_ID en el archivo .env. "
                "Mira la GUIA.md (paso 0.8) y el ticket ACS-002."
            )
        self.token = token
        self.chat_id = chat_id
        self._abrir = abrir

    def enviar(self, texto: str, botones=None) -> None:
        datos = {"chat_id": self.chat_id, "text": texto}
        if botones:
            datos["reply_markup"] = json.dumps({"inline_keyboard": botones})
        cuerpo_datos = urllib.parse.urlencode(datos).encode()
        peticion = urllib.request.Request(
            self.URL.format(token=self.token), data=cuerpo_datos, method="POST"
        )
        try:
            with self._abrir(peticion, timeout=20) as respuesta:
                cuerpo = json.loads(respuesta.read().decode("utf-8"))
        except Exception as error:  # red caída, token mal puesto...
            raise ErrorDeEnvio(f"Telegram no ha aceptado el mensaje: {error}") from error
        if not cuerpo.get("ok"):
            raise ErrorDeEnvio(f"Telegram no ha aceptado el mensaje: {cuerpo.get('description', cuerpo)}")


def contestar_callback(token: str, callback_id: str, texto: str = "", abrir=None) -> None:
    """Avisa a Telegram de que el botón ya se ha atendido.

    Si no se contesta, el botón se queda cargando en el móvil de la persona.
    """
    if not token:
        raise ErrorDeEnvio(
            "Falta TELEGRAM_TOKEN en el archivo .env. "
            "Copia el token de @BotFather y pégalo ahí. "
            "Mira la GUIA.md (paso 0.8) y el ticket ACS-002."
        )
    if abrir is None:
        abrir = urllib.request.urlopen
    url = "https://api.telegram.org/bot{token}/answerCallbackQuery".format(token=token)
    datos = {"callback_query_id": callback_id}
    if texto:
        datos["text"] = texto
    cuerpo_datos = urllib.parse.urlencode(datos).encode()
    peticion = urllib.request.Request(url, data=cuerpo_datos, method="POST")
    try:
        with abrir(peticion, timeout=20) as respuesta:
            cuerpo = json.loads(respuesta.read().decode("utf-8"))
    except Exception as error:  # red caída, token mal puesto...
        raise ErrorDeEnvio(f"Telegram no ha contestado al botón: {error}") from error
    if not cuerpo.get("ok"):
        raise ErrorDeEnvio(
            f"Telegram no ha aceptado el botón: {cuerpo.get('description', cuerpo)}"
        )


def consultar_chats(token: str, abrir=None) -> list[tuple[str, str]]:
    """Pregunta a Telegram quién le ha escrito al bot.

    Devuelve una lista de (número de chat, nombre), sin repetir personas.
    """
    if not token:
        raise ErrorDeEnvio(
            "Falta TELEGRAM_TOKEN en el archivo .env. "
            "Copia el token de @BotFather y pégalo ahí. "
            "Mira la GUIA.md (paso 0.8) y el ticket ACS-002."
        )
    if abrir is None:
        abrir = urllib.request.urlopen
    url = "https://api.telegram.org/bot{token}/getUpdates".format(token=token)
    peticion = urllib.request.Request(url, method="GET")
    try:
        with abrir(peticion, timeout=20) as respuesta:
            cuerpo = json.loads(respuesta.read().decode("utf-8"))
    except Exception as error:  # red caída, token mal puesto...
        raise ErrorDeEnvio(f"Telegram no ha contestado: {error}") from error
    if not cuerpo.get("ok"):
        raise ErrorDeEnvio(
            f"Telegram no ha aceptado la consulta: {cuerpo.get('description', cuerpo)}"
        )

    chats: list[tuple[str, str]] = []
    for actualizacion in cuerpo.get("result") or []:
        chat = (actualizacion.get("message") or {}).get("chat") or {}
        if chat.get("id") is None:
            continue
        numero = str(chat["id"])
        if any(numero == visto for visto, _ in chats):
            continue
        nombre = " ".join(
            parte for parte in (chat.get("first_name"), chat.get("last_name")) if parte
        )
        chats.append((numero, nombre))
    return chats


def leer_mensajes(token: str, offset: int | None = None, timeout: int = 30, abrir=None) -> list[dict]:
    """Pregunta a Telegram por los mensajes nuevos que le han escrito al bot.

    Devuelve una lista de diccionarios con 'update_id', 'chat_id', 'texto' y 'foto'.
    'foto' es el identificador de la foto que ha mandado la persona, o "" si no
    hay foto. Con 'offset' se pide a Telegram que no vuelva a mandar los mensajes
    anteriores. Con 'timeout' se usa long polling: Telegram mantiene la conexión
    abierta hasta que llega un mensaje o pasan esos segundos.
    """
    if not token:
        raise ErrorDeEnvio(
            "Falta TELEGRAM_TOKEN en el archivo .env. "
            "Copia el token de @BotFather y pégalo ahí. "
            "Mira la GUIA.md (paso 0.8) y el ticket ACS-002."
        )
    if abrir is None:
        abrir = urllib.request.urlopen
    parametros = {"timeout": str(timeout)}
    if offset is not None:
        parametros["offset"] = str(offset)
    url = "https://api.telegram.org/bot{token}/getUpdates?{consulta}".format(
        token=token, consulta=urllib.parse.urlencode(parametros)
    )
    peticion = urllib.request.Request(url, method="GET")
    try:
        with abrir(peticion, timeout=timeout + 10) as respuesta:
            cuerpo = json.loads(respuesta.read().decode("utf-8"))
    except Exception as error:  # red caída, token mal puesto...
        raise ErrorDeEnvio(f"Telegram no ha contestado: {error}") from error
    if not cuerpo.get("ok"):
        raise ErrorDeEnvio(
            f"Telegram no ha aceptado la consulta: {cuerpo.get('description', cuerpo)}"
        )

    mensajes: list[dict] = []
    for actualizacion in cuerpo.get("result") or []:
        numero = actualizacion.get("update_id")
        if numero is None:
            continue

        callback = actualizacion.get("callback_query")
        if callback:
            mensaje_callback = callback.get("message") or {}
            chat = mensaje_callback.get("chat") or {}
            chat_id = chat.get("id")
            if chat_id is None:
                chat_id = (callback.get("from") or {}).get("id")
            if chat_id is None:
                continue
            mensajes.append(
                {
                    "update_id": numero,
                    "chat_id": str(chat_id),
                    "texto": "",
                    "foto": "",
                    "callback_id": str(callback.get("id") or ""),
                    "callback_data": callback.get("data") or "",
                }
            )
            continue

        mensaje = actualizacion.get("message") or {}
        chat = mensaje.get("chat") or {}
        if chat.get("id") is None:
            continue
        fotos = mensaje.get("photo") or []
        foto = fotos[-1].get("file_id") if fotos else ""
        mensajes.append(
            {
                "update_id": numero,
                "chat_id": str(chat["id"]),
                "texto": mensaje.get("text") or mensaje.get("caption") or "",
                "foto": foto or "",
            }
        )
    return mensajes


def descargar_foto(token: str, file_id: str, abrir=None) -> bytes:
    """Descarga la foto que ha mandado la persona al bot de Telegram.

    Primero pregunta a Telegram dónde está el archivo (getFile) y después
    descarga los bytes de la foto.
    """
    if not token:
        raise ErrorDeEnvio(
            "Falta TELEGRAM_TOKEN en el archivo .env. "
            "Copia el token de @BotFather y pégalo ahí. "
            "Mira la GUIA.md (paso 0.8) y el ticket ACS-002."
        )
    if abrir is None:
        abrir = urllib.request.urlopen
    url = "https://api.telegram.org/bot{token}/getFile?{consulta}".format(
        token=token, consulta=urllib.parse.urlencode({"file_id": file_id})
    )
    peticion = urllib.request.Request(url, method="GET")
    try:
        with abrir(peticion, timeout=20) as respuesta:
            cuerpo = json.loads(respuesta.read().decode("utf-8"))
    except Exception as error:  # red caída, token mal puesto...
        raise ErrorDeEnvio(f"Telegram no ha contestado: {error}") from error
    if not cuerpo.get("ok"):
        raise ErrorDeEnvio(
            f"Telegram no ha aceptado la consulta: {cuerpo.get('description', cuerpo)}"
        )
    ruta = (cuerpo.get("result") or {}).get("file_path")
    if not ruta:
        raise ErrorDeEnvio("Telegram no ha mandado la dirección de la foto.")

    url_foto = "https://api.telegram.org/file/bot{token}/{ruta}".format(token=token, ruta=ruta)
    peticion_foto = urllib.request.Request(url_foto, method="GET")
    try:
        with abrir(peticion_foto, timeout=30) as respuesta:
            return respuesta.read()
    except Exception as error:  # red caída mientras baja la foto...
        raise ErrorDeEnvio(f"No se ha podido descargar la foto: {error}") from error


def crear_notificador(cfg: Config):
    if cfg.canal == "telegram":
        return NotificadorTelegram(cfg.telegram_token, cfg.telegram_chat_id)
    if cfg.canal == "consola":
        return NotificadorConsola()
    raise ErrorDeEnvio(f"Canal '{cfg.canal}' desconocido. Usa 'consola' o 'telegram'.")


def registrar_comandos_telegram(token: str, abrir=None) -> bool:
    """Registra la lista de comandos en Telegram (setMyCommands).

    Si falla, devuelve False pero no lanza excepción para que el bot
    pueda seguir funcionando. Devuelve True si se registró correctamente.
    """
    if not token:
        return False

    comandos = [
        {"command": "ayuda", "description": "Ver lo que sé hacer"},
        {"command": "anadir", "description": "Apuntar una cita nueva"},
        {"command": "citas", "description": "Ver tus citas"},
        {"command": "tension", "description": "Apuntar una toma de tensión"},
        {"command": "historial", "description": "Ver tus últimas tomas de tensión"},
    ]
    if abrir is None:
        abrir = urllib.request.urlopen

    url = "https://api.telegram.org/bot{token}/setMyCommands".format(token=token)
    datos = json.dumps({"commands": comandos}).encode("utf-8")
    peticion = urllib.request.Request(
        url, data=datos, method="POST", headers={"Content-Type": "application/json"}
    )
    try:
        with abrir(peticion, timeout=20) as respuesta:
            cuerpo = json.loads(respuesta.read().decode("utf-8"))
    except Exception:
        # Silencioso: el bot sigue funcionando aunque no se registre el menú
        return False
    return bool(cuerpo.get("ok"))
