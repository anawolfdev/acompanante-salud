from acompanante import db
from acompanante.bot import atender_mensajes
from acompanante.conversacion import AYUDA, NO_LEIDO_PAPEL
from acompanante.notificador import ErrorDeEnvio


def test_atender_responde_solo_al_chat_autorizado(cfg, monkeypatch):
    cfg.telegram_token = "123:ABC"
    cfg.telegram_chat_id = "999"
    enviados = []
    offsets = []

    class TelegramFalso:
        def __init__(self, token, chat_id):
            self.chat_id = chat_id

        def enviar(self, texto):
            enviados.append((self.chat_id, texto))

    def leer_falsos(token, offset=None, abrir=None):
        offsets.append(offset)
        return [
            {"update_id": 5, "chat_id": "999", "texto": "/ayuda"},
            {"update_id": 6, "chat_id": "1000", "texto": "/ayuda"},
        ]

    monkeypatch.setattr("acompanante.bot.NotificadorTelegram", TelegramFalso)
    monkeypatch.setattr("acompanante.bot.leer_mensajes", leer_falsos)

    con = db.conectar(cfg.ruta_bd)
    siguiente = atender_mensajes(con, cfg)
    con.close()

    assert offsets == [None]
    assert enviados == [("999", AYUDA)]
    assert siguiente == 7


def test_atender_no_contesta_a_otra_cuenta(cfg, monkeypatch):
    cfg.telegram_token = "123:ABC"
    cfg.telegram_chat_id = "999"
    enviados = []

    class TelegramFalso:
        def __init__(self, token, chat_id):
            self.chat_id = chat_id

        def enviar(self, texto):
            enviados.append((self.chat_id, texto))

    monkeypatch.setattr("acompanante.bot.NotificadorTelegram", TelegramFalso)
    monkeypatch.setattr(
        "acompanante.bot.leer_mensajes",
        lambda token, offset=None, abrir=None: [
            {"update_id": 8, "chat_id": "1000", "texto": "/proximas"},
        ],
    )

    con = db.conectar(cfg.ruta_bd)
    siguiente = atender_mensajes(con, cfg)
    con.close()

    assert enviados == []
    assert siguiente == 9


def test_atender_descarga_la_foto_y_la_pasa_a_la_aplicacion(cfg, monkeypatch):
    cfg.telegram_token = "123:ABC"
    cfg.telegram_chat_id = "999"
    enviados = []
    descargas = []
    recibidas = []

    class TelegramFalso:
        def __init__(self, token, chat_id):
            self.chat_id = chat_id

        def enviar(self, texto):
            enviados.append((self.chat_id, texto))

    def descargar(token, file_id, abrir=None):
        descargas.append((token, file_id))
        return b"\xff\xd8foto"

    def responder_falso(con, cfg, texto, chat_id=None, imagen=None):
        recibidas.append(imagen)
        return "He entendido esta cita:"

    monkeypatch.setattr("acompanante.bot.NotificadorTelegram", TelegramFalso)
    monkeypatch.setattr(
        "acompanante.bot.leer_mensajes",
        lambda token, offset=None, abrir=None: [
            {"update_id": 20, "chat_id": "999", "texto": "", "foto": "foto-1"},
        ],
    )
    monkeypatch.setattr("acompanante.bot.descargar_foto", descargar)
    monkeypatch.setattr("acompanante.bot.responder", responder_falso)

    con = db.conectar(cfg.ruta_bd)
    siguiente = atender_mensajes(con, cfg)
    con.close()

    assert descargas == [("123:ABC", "foto-1")]
    assert recibidas == [b"\xff\xd8foto"]
    assert enviados == [("999", "He entendido esta cita:")]
    assert siguiente == 21


def test_atender_si_no_puede_descargar_la_foto_avisa(cfg, monkeypatch):
    cfg.telegram_token = "123:ABC"
    cfg.telegram_chat_id = "999"
    enviados = []

    class TelegramFalso:
        def __init__(self, token, chat_id):
            self.chat_id = chat_id

        def enviar(self, texto):
            enviados.append((self.chat_id, texto))

    def falla(token, file_id, abrir=None):
        raise ErrorDeEnvio("sin red")

    monkeypatch.setattr("acompanante.bot.NotificadorTelegram", TelegramFalso)
    monkeypatch.setattr(
        "acompanante.bot.leer_mensajes",
        lambda token, offset=None, abrir=None: [
            {"update_id": 21, "chat_id": "999", "texto": "", "foto": "foto-1"},
        ],
    )
    monkeypatch.setattr("acompanante.bot.descargar_foto", falla)

    con = db.conectar(cfg.ruta_bd)
    siguiente = atender_mensajes(con, cfg)
    con.close()

    assert enviados == [("999", NO_LEIDO_PAPEL)]
    assert siguiente == 22
