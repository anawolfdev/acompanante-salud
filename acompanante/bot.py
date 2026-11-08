"""Une los mensajes que llegan de Telegram con las respuestas de la aplicación."""

from __future__ import annotations

from acompanante.config import Config
from acompanante.conversacion import debe_responder, responder
from acompanante.notificador import NotificadorTelegram, leer_mensajes


def atender_mensajes(con, cfg: Config, offset: int | None = None, abrir=None) -> int | None:
    """Lee los mensajes nuevos y contesta solo al chat autorizado.

    Devuelve el número desde el que hay que preguntar la próxima vez, para no
    repetir los mensajes que ya se han leído.
    """
    mensajes = leer_mensajes(cfg.telegram_token, offset=offset, abrir=abrir)
    for mensaje in mensajes:
        offset = mensaje["update_id"] + 1
        if not debe_responder(mensaje["chat_id"], cfg):
            continue
        respuesta = responder(con, cfg, mensaje["texto"])
        NotificadorTelegram(cfg.telegram_token, str(mensaje["chat_id"])).enviar(respuesta)
    return offset
