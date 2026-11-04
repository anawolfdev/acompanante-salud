from acompanante.cli import main


def test_flujo_completo_en_consola(cfg, capsys):
    assert main(["iniciar"], cfg) == 0
    assert main([
        "nueva-cita", "--titulo", "Analítica", "--tipo", "analitica",
        "--fecha", "12/11/2099", "--hora", "8:30", "--lugar", "Centro de salud",
        "--preparar", "Ve en ayunas", "--preparar", "Lleva la muestra de orina",
    ], cfg) == 0
    assert main(["citas"], cfg) == 0
    salida = capsys.readouterr().out
    assert "Cita guardada" in salida
    assert "jueves 12 de noviembre a las 8:30: Analítica" in salida

    assert main(["avisos", "--ahora", "10/11/2099 10:00"], cfg) == 0
    salida = capsys.readouterr().out
    assert "1. Ve en ayunas." in salida
    assert "Avisos enviados: 1" in salida

    assert main(["avisos", "--ahora", "10/11/2099 10:05"], cfg) == 0
    assert "no toca ningún aviso" in capsys.readouterr().out


def test_fecha_mal_escrita_no_rompe(cfg, capsys):
    codigo = main(["nueva-cita", "--titulo", "X", "--fecha", "mañana", "--hora", "9:00"], cfg)
    assert codigo == 1
    assert "Escríbela así" in capsys.readouterr().out


def test_demo(cfg, capsys):
    assert main(["demo"], cfg) == 0
    salida = capsys.readouterr().out
    assert "Así te llegará el aviso 2 días antes" in salida
    assert "Pasado mañana" in salida


def test_mi_chat_ensena_el_numero(cfg, capsys, monkeypatch):
    cfg.telegram_token = "123:ABC"
    monkeypatch.setattr("acompanante.cli.consultar_chats", lambda token: [("999", "Ana")])
    assert main(["mi-chat"], cfg) == 0
    salida = capsys.readouterr().out
    assert "Te ha escrito Ana." in salida
    assert "Tu número de chat es: 999" in salida
    assert "TELEGRAM_CHAT_ID" in salida


def test_mi_chat_sin_mensajes_explica_que_hacer(cfg, capsys, monkeypatch):
    cfg.telegram_token = "123:ABC"
    monkeypatch.setattr("acompanante.cli.consultar_chats", lambda token: [])
    assert main(["mi-chat"], cfg) == 0
    salida = capsys.readouterr().out
    assert "Todavía no le has escrito a tu bot." in salida
    assert 'escríbele "hola"' in salida


def test_mi_chat_sin_token_avisa(cfg, capsys):
    assert main(["mi-chat"], cfg) == 1
    salida = capsys.readouterr().out
    assert "Error: Falta TELEGRAM_TOKEN" in salida
    assert ".env" in salida


def test_probar_telegram_manda_el_saludo(cfg, capsys, monkeypatch):
    cfg.telegram_token = "123:ABC"
    cfg.telegram_chat_id = "999"
    enviados = []

    class TelegramFalso:
        def __init__(self, token, chat_id):
            self.token = token
            self.chat_id = chat_id

        def enviar(self, texto):
            enviados.append(texto)

    monkeypatch.setattr("acompanante.cli.NotificadorTelegram", TelegramFalso)
    assert main(["probar-telegram"], cfg) == 0
    assert enviados == [
        "Hola, soy tu Acompañante de salud. Los avisos te llegarán por aquí."
    ]
    assert "Mensaje enviado" in capsys.readouterr().out


def test_probar_telegram_sin_chat_avisa(cfg, capsys):
    cfg.telegram_token = "123:ABC"
    assert main(["probar-telegram"], cfg) == 1
    salida = capsys.readouterr().out
    assert "Error: Falta TELEGRAM_TOKEN o TELEGRAM_CHAT_ID" in salida
    assert ".env" in salida
