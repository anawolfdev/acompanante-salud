import io
import json
import urllib.parse

import pytest

from acompanante.config import Config
from acompanante.notificador import ErrorDeEnvio, NotificadorConsola, NotificadorTelegram, crear_notificador


class RespuestaFalsa(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def abridor(respuesta: dict, guardar: list):
    def abrir(peticion, timeout=None):
        guardar.append(peticion)
        return RespuestaFalsa(json.dumps(respuesta).encode())
    return abrir


def test_telegram_manda_el_texto():
    peticiones = []
    n = NotificadorTelegram("123:ABC", "999", abrir=abridor({"ok": True}, peticiones))
    n.enviar("Recordatorio de salud.")
    p = peticiones[0]
    assert p.full_url == "https://api.telegram.org/bot123:ABC/sendMessage"
    datos = urllib.parse.parse_qs(p.data.decode())
    assert datos == {"chat_id": ["999"], "text": ["Recordatorio de salud."]}


def test_telegram_error_se_explica():
    n = NotificadorTelegram("123:ABC", "999", abrir=abridor({"ok": False, "description": "chat not found"}, []))
    with pytest.raises(ErrorDeEnvio, match="chat not found"):
        n.enviar("hola")


def test_telegram_sin_token_avisa():
    with pytest.raises(ErrorDeEnvio, match="ACS-002"):
        NotificadorTelegram("", "")


def test_crear_notificador_por_defecto_es_consola():
    assert isinstance(crear_notificador(Config()), NotificadorConsola)
