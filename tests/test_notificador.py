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
    contestar_callback,
    crear_notificador,
    descargar_foto,
    leer_mensajes,
    registrar_comandos_telegram,
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


def test_telegram_manda_los_botones_inline():
    peticiones = []
    botones = [
        [
            {"text": "Cambiar", "callback_data": "cambiar:3"},
            {"text": "Borrar", "callback_data": "borrar_cita:3"},
        ]
    ]
    n = NotificadorTelegram("123:ABC", "999", abrir=abridor({"ok": True}, peticiones))
    n.enviar("Estas son tus citas.", botones=botones)

    datos = urllib.parse.parse_qs(peticiones[0].data.decode())
    assert datos["chat_id"] == ["999"]
    assert datos["text"] == ["Estas son tus citas."]
    assert json.loads(datos["reply_markup"][0]) == {"inline_keyboard": botones}


def test_contestar_callback_avisa_a_telegram():
    peticiones = []
    contestar_callback("123:ABC", "cb-1", abrir=abridor({"ok": True}, peticiones))

    p = peticiones[0]
    assert p.full_url == "https://api.telegram.org/bot123:ABC/answerCallbackQuery"
    assert p.get_method() == "POST"
    assert urllib.parse.parse_qs(p.data.decode()) == {
        "callback_query_id": ["cb-1"]
    }


def test_contestar_callback_si_telegram_falla_avisa():
    with pytest.raises(ErrorDeEnvio, match="botón"):
        contestar_callback(
            "123:ABC",
            "cb-1",
            abrir=abridor({"ok": False, "description": "bad request"}, []),
        )


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
        {"update_id": 10, "chat_id": "999", "texto": "/proximas", "foto": ""},
        {"update_id": 11, "chat_id": "1000", "texto": "hola", "foto": ""},
    ]
    assert "offset=10" in peticiones[0].full_url
    assert "timeout=30" in peticiones[0].full_url
    assert peticiones[0].get_method() == "GET"


def test_leer_mensajes_devuelve_los_botones_pulsados():
    respuesta = {
        "ok": True,
        "result": [
            {
                "update_id": 30,
                "callback_query": {
                    "id": "cb-1",
                    "data": "borrar_cita:2",
                    "message": {"chat": {"id": 999}},
                },
            },
        ],
    }
    mensajes = leer_mensajes("123:ABC", abrir=abridor(respuesta, []))

    assert mensajes == [
        {
            "update_id": 30,
            "chat_id": "999",
            "texto": "",
            "foto": "",
            "callback_id": "cb-1",
            "callback_data": "borrar_cita:2",
        }
    ]


def test_leer_mensajes_sin_texto_no_rompe():
    respuesta = {
        "ok": True,
        "result": [
            {"update_id": 12, "message": {"chat": {"id": 999}}},
            {"update_id": 13, "message": {}},
        ],
    }
    mensajes = leer_mensajes("123:ABC", abrir=abridor(respuesta, []))
    assert mensajes == [{"update_id": 12, "chat_id": "999", "texto": "", "foto": ""}]


def test_leer_mensajes_error_se_explica():
    n = abridor({"ok": False, "description": "Unauthorized"}, [])
    with pytest.raises(ErrorDeEnvio, match="Unauthorized"):
        leer_mensajes("123:ABC", abrir=n)


def test_leer_mensajes_sin_token_avisa():
    with pytest.raises(ErrorDeEnvio, match="TELEGRAM_TOKEN"):
        leer_mensajes("")


def test_leer_mensajes_devuelve_la_foto_mas_grande():
    respuesta = {
        "ok": True,
        "result": [
            {
                "update_id": 14,
                "message": {
                    "chat": {"id": 999},
                    "photo": [{"file_id": "pequena"}, {"file_id": "grande"}],
                },
            },
        ],
    }
    mensajes = leer_mensajes("123:ABC", abrir=abridor(respuesta, []))

    assert mensajes[0]["foto"] == "grande"
    assert mensajes[0]["texto"] == ""


def test_leer_mensajes_usa_el_texto_que_acompana_a_la_foto():
    respuesta = {
        "ok": True,
        "result": [
            {
                "update_id": 15,
                "message": {
                    "chat": {"id": 999},
                    "caption": "la cita del especialista",
                    "photo": [{"file_id": "foto-1"}],
                },
            },
        ],
    }
    mensajes = leer_mensajes("123:ABC", abrir=abridor(respuesta, []))

    assert mensajes[0]["texto"] == "la cita del especialista"
    assert mensajes[0]["foto"] == "foto-1"


def test_descargar_foto_pide_la_direccion_y_baja_los_bytes():
    peticiones = []
    respuestas = [
        {"ok": True, "result": {"file_path": "photos/foto.jpg"}},
        b"\xff\xd8foto",
    ]

    def abrir(peticion, timeout=None):
        peticiones.append(peticion)
        respuesta = respuestas[len(peticiones) - 1]
        if isinstance(respuesta, dict):
            return RespuestaFalsa(json.dumps(respuesta).encode())
        return RespuestaFalsa(respuesta)

    foto = descargar_foto("123:ABC", "file-1", abrir=abrir)

    assert foto == b"\xff\xd8foto"
    assert peticiones[0].full_url == "https://api.telegram.org/bot123:ABC/getFile?file_id=file-1"
    assert peticiones[1].full_url == "https://api.telegram.org/file/bot123:ABC/photos/foto.jpg"


def test_descargar_foto_sin_token_avisa():
    with pytest.raises(ErrorDeEnvio, match="TELEGRAM_TOKEN"):
        descargar_foto("", "file-1")


def test_descargar_foto_si_telegram_falla_avisa():
    def abrir(peticion, timeout=None):
        return RespuestaFalsa(
            json.dumps({"ok": False, "description": "file is too big"}).encode()
        )

    with pytest.raises(ErrorDeEnvio, match="file is too big"):
        descargar_foto("123:ABC", "file-1", abrir=abrir)


def test_crear_notificador_por_defecto_es_consola():
    assert isinstance(crear_notificador(Config()), NotificadorConsola)


def test_registrar_comandos_telegram_exito():
    peticiones = []
    respuesta = {"ok": True}
    ok = registrar_comandos_telegram("123:ABC", abrir=abridor(respuesta, peticiones))
    assert ok is True
    p = peticiones[0]
    assert p.full_url == "https://api.telegram.org/bot123:ABC/setMyCommands"
    assert p.get_method() == "POST"
    datos = json.loads(p.data.decode())
    assert "commands" in datos
    assert len(datos["commands"]) == 7
    nombres = [c["command"] for c in datos["commands"]]
    assert nombres == [
        "ayuda",
        "anadir",
        "citas",
        "tension",
        "tensiones",
        "medicacion",
        "historial",
    ]
    assert "añadir" not in nombres


def test_registrar_comandos_telegram_fallo_silencioso():
    # Telegram devuelve error
    ok = registrar_comandos_telegram("123:ABC", abrir=abridor({"ok": False, "description": "bad request"}, []))
    assert ok is False

    # Excepción de red
    def abrir_falla(peticion, timeout=None):
        raise ConnectionError("sin red")

    ok = registrar_comandos_telegram("123:ABC", abrir=abrir_falla)
    assert ok is False


def test_registrar_comandos_telegram_sin_token():
    ok = registrar_comandos_telegram("")
    assert ok is False
