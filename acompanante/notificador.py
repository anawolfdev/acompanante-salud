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

    def enviar(self, texto: str) -> None:
        datos = urllib.parse.urlencode({"chat_id": self.chat_id, "text": texto}).encode()
        peticion = urllib.request.Request(self.URL.format(token=self.token), data=datos, method="POST")
        try:
            with self._abrir(peticion, timeout=20) as respuesta:
                cuerpo = json.loads(respuesta.read().decode("utf-8"))
        except Exception as error:  # red caída, token mal puesto...
            raise ErrorDeEnvio(f"Telegram no ha aceptado el mensaje: {error}") from error
        if not cuerpo.get("ok"):
            raise ErrorDeEnvio(f"Telegram no ha aceptado el mensaje: {cuerpo.get('description', cuerpo)}")


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


def crear_notificador(cfg: Config):
    if cfg.canal == "telegram":
        return NotificadorTelegram(cfg.telegram_token, cfg.telegram_chat_id)
    if cfg.canal == "consola":
        return NotificadorConsola()
    raise ErrorDeEnvio(f"Canal '{cfg.canal}' desconocido. Usa 'consola' o 'telegram'.")
