from acompanante import db
from acompanante.bot import atender_mensajes
from acompanante.conversacion import AYUDA


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
