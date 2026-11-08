import io
import json
import urllib.parse

import pytest

from acompanante.config import Config
from acompanante.notificador import (
    ErrorDeEnvio,
    NotificadorConsola,
    NotificadorTelegram,
    consultar_chats,
    crear_notificador,
    leer_mensajes,
)


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


def test_consultar_chats_devuelve_el_numero_sin_repetir():
    peticiones = []
    respuesta = {
        "ok": True,
        "result": [
            {"update_id": 1, "message": {"chat": {"id": 999, "first_name": "Ana", "last_name": "Pérez"}}},
            {"update_id": 2, "message": {"chat": {"id": 999, "first_name": "Ana", "last_name": "Pérez"}}},
            {"update_id": 3, "message": {"chat": {"id": 1000, "first_name": "Luis"}}},
        ],
    }
    chats = consultar_chats("123:ABC", abrir=abridor(respuesta, peticiones))
    assert chats == [("999", "Ana Pérez"), ("1000", "Luis")]
    assert peticiones[0].full_url == "https://api.telegram.org/bot123:ABC/getUpdates"
    assert peticiones[0].get_method() == "GET"


def test_consultar_chats_sin_mensajes():
    chats = consultar_chats("123:ABC", abrir=abridor({"ok": True, "result": []}, []))
    assert chats == []


def test_consultar_chats_error_se_explica():
    n = abridor({"ok": False, "description": "Unauthorized"}, [])
    with pytest.raises(ErrorDeEnvio, match="Unauthorized"):
        consultar_chats("123:ABC", abrir=n)


def test_consultar_chats_sin_token_avisa():
    with pytest.raises(ErrorDeEnvio, match="TELEGRAM_TOKEN"):
        consultar_chats("")


def test_leer_mensajes_devuelve_el_texto_y_el_chat():
    peticiones = []
    respuesta = {
        "ok": True,
        "result": [
            {"update_id": 10, "message": {"chat": {"id": 999}, "text": "/proximas"}},
            {"update_id": 11, "message": {"chat": {"id": 1000}, "text": "hola"}},
        ],
    }
    mensajes = leer_mensajes("123:ABC", offset=10, abrir=abridor(respuesta, peticiones))

    assert mensajes == [
        {"update_id": 10, "chat_id": "999", "texto": "/proximas"},
        {"update_id": 11, "chat_id": "1000", "texto": "hola"},
    ]
    assert "offset=10" in peticiones[0].full_url
    assert "timeout=30" in peticiones[0].full_url
    assert peticiones[0].get_method() == "GET"


def test_leer_mensajes_sin_texto_no_rompe():
    respuesta = {
        "ok": True,
        "result": [
            {"update_id": 12, "message": {"chat": {"id": 999}}},
            {"update_id": 13, "message": {}},
        ],
    }
    mensajes = leer_mensajes("123:ABC", abrir=abridor(respuesta, []))
    assert mensajes == [{"update_id": 12, "chat_id": "999", "texto": ""}]


def test_leer_mensajes_error_se_explica():
    n = abridor({"ok": False, "description": "Unauthorized"}, [])
    with pytest.raises(ErrorDeEnvio, match="Unauthorized"):
        leer_mensajes("123:ABC", abrir=n)


def test_leer_mensajes_sin_token_avisa():
    with pytest.raises(ErrorDeEnvio, match="TELEGRAM_TOKEN"):
        leer_mensajes("")


def test_crear_notificador_por_defecto_es_consola():
    assert isinstance(crear_notificador(Config()), NotificadorConsola)
