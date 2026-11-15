"""Une los mensajes que llegan de Telegram con las respuestas de la aplicación."""

from __future__ import annotations

from acompanante.config import Config
from acompanante.conversacion import (
    NO_LEIDO_PAPEL,
    debe_responder,
    responder,
    responder_callback,
)
from acompanante.notificador import (
    ErrorDeEnvio,
    NotificadorTelegram,
    contestar_callback,
    descargar_foto,
    leer_mensajes,
)


def atender_mensajes(con, cfg: Config, offset: int | None = None, abrir=None) -> int | None:
    """Lee los mensajes nuevos y contesta solo al chat autorizado.

    Si llega una foto, la descarga y se la pasa a la aplicación para que intente
    leer el papel de la cita. Si llega un botón pulsado, lo atiende la aplicación.
    Devuelve el número desde el que hay que preguntar la próxima vez, para no
    repetir los mensajes que ya se han leído.
    """
    mensajes = leer_mensajes(cfg.telegram_token, offset=offset, abrir=abrir)
    for mensaje in mensajes:
        offset = mensaje["update_id"] + 1
        if not debe_responder(mensaje["chat_id"], cfg):
            continue

        if mensaje.get("callback_data"):
            if mensaje.get("callback_id"):
                try:
                    contestar_callback(
                        cfg.telegram_token, mensaje["callback_id"], abrir=abrir
                    )
                except ErrorDeEnvio:
                    # El botón tarda unos segundos en dejar de cargar, pero la
                    # respuesta se manda igualmente.
                    pass
            respuesta = responder_callback(
                con, cfg, mensaje["callback_data"], chat_id=mensaje["chat_id"]
            )
        else:
            imagen = None
            respuesta = None
            if mensaje.get("foto"):
                try:
                    imagen = descargar_foto(
                        cfg.telegram_token, mensaje["foto"], abrir=abrir
                    )
                except ErrorDeEnvio:
                    respuesta = NO_LEIDO_PAPEL
            if respuesta is None:
                respuesta = responder(
                    con, cfg, mensaje["texto"], chat_id=mensaje["chat_id"], imagen=imagen
                )

        notificador = NotificadorTelegram(
            cfg.telegram_token, str(mensaje["chat_id"])
        )
        partes = getattr(respuesta, "mensajes", None) or [respuesta]
        for parte in partes:
            botones = getattr(parte, "botones", None)
            if botones:
                notificador.enviar(parte, botones=botones)
            else:
                notificador.enviar(parte)
    return offset
