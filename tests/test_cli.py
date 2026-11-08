from datetime import datetime

from acompanante import db
from acompanante.cli import main
from acompanante.modelos import Cita
from acompanante.notificador import ErrorDeEnvio


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


def guardar_analitica(cfg):
    con = db.conectar(cfg.ruta_bd)
    db.guardar_cita(
        con,
        Cita(titulo="Analítica", tipo="analitica", fecha_hora=datetime(2026, 11, 12, 8, 30)),
    )
    con.close()


def test_vigilar_manda_los_avisos_y_no_repite(cfg, capsys, monkeypatch):
    guardar_analitica(cfg)
    momentos = iter([datetime(2026, 11, 10, 10, 0), datetime(2026, 11, 10, 10, 5)])
    monkeypatch.setattr("acompanante.cli.ahora_local", lambda _cfg: next(momentos))

    enviados = []

    class Buzon:
        def enviar(self, texto):
            enviados.append(texto)

    monkeypatch.setattr("acompanante.cli.crear_notificador", lambda _cfg: Buzon())

    esperas = []

    def esperar_falsa(segundos):
        esperas.append(segundos)
        if len(esperas) == 2:
            raise KeyboardInterrupt

    monkeypatch.setattr("acompanante.cli.esperar", esperar_falsa)

    assert main(["vigilar"], cfg) == 0

    salida = capsys.readouterr().out
    assert "Vigilando tus citas. Para parar, pulsa Control + C" in salida
    assert len(enviados) == 1
    assert "Avisos enviados: 1" in salida
    assert "Vigilancia parada. Hasta luego." in salida
    assert esperas == [300, 300]


def test_vigilar_sigue_si_telegram_falla(cfg, capsys, monkeypatch):
    guardar_analitica(cfg)
    momentos = iter([datetime(2026, 11, 10, 10, 0), datetime(2026, 11, 10, 10, 5)])
    monkeypatch.setattr("acompanante.cli.ahora_local", lambda _cfg: next(momentos))

    intentos = []

    class TelegramQueFalla:
        def enviar(self, texto):
            intentos.append(texto)
            raise ErrorDeEnvio("no hay conexión con Telegram")

    monkeypatch.setattr("acompanante.cli.crear_notificador", lambda _cfg: TelegramQueFalla())

    esperas = []

    def esperar_falsa(segundos):
        esperas.append(segundos)
        if len(esperas) == 2:
            raise KeyboardInterrupt

    monkeypatch.setattr("acompanante.cli.esperar", esperar_falsa)

    assert main(["vigilar"], cfg) == 0

    salida = capsys.readouterr().out
    assert len(intentos) == 2
    assert "No se han podido mandar los avisos: no hay conexión con Telegram" in salida
    assert salida.count("Se volverá a intentar en la próxima revisión.") == 2
    assert "Vigilancia parada. Hasta luego." in salida


def test_vigilar_espera_los_minutos_configurados(cfg, monkeypatch):
    cfg.minutos_entre_revisiones = 2
    monkeypatch.setattr("acompanante.cli.ahora_local", lambda _cfg: datetime(2026, 11, 10, 10, 0))

    class Buzon:
        def enviar(self, texto):
            pass

    monkeypatch.setattr("acompanante.cli.crear_notificador", lambda _cfg: Buzon())

    esperas = []

    def esperar_falsa(segundos):
        esperas.append(segundos)
        raise KeyboardInterrupt

    monkeypatch.setattr("acompanante.cli.esperar", esperar_falsa)

    assert main(["vigilar"], cfg) == 0
    assert esperas == [120]


def guardar_cita_de_prueba(cfg, **cambios):
    datos = dict(
        titulo="Analítica",
        tipo="analitica",
        fecha_hora=datetime(2099, 11, 12, 8, 30),
        lugar="Centro de salud",
        preparacion=["Ve en ayunas"],
    )
    datos.update(cambios)
    con = db.conectar(cfg.ruta_bd)
    cita = Cita(**datos)
    db.guardar_cita(con, cita)
    con.close()
    return cita.id


def test_borrar_cita_pide_confirmacion_y_la_quita(cfg, capsys, monkeypatch):
    cid = guardar_cita_de_prueba(cfg)
    monkeypatch.setattr("builtins.input", lambda _texto="": "s")

    assert main(["borrar-cita", str(cid)], cfg) == 0
    salida = capsys.readouterr().out
    assert "¿Seguro que quieres borrar esta cita? (s/n)" in salida
    assert "Cita borrada." in salida

    assert main(["citas"], cfg) == 0
    assert "No tienes citas apuntadas." in capsys.readouterr().out


def test_borrar_cita_si_se_dice_que_no_no_borra(cfg, capsys, monkeypatch):
    cid = guardar_cita_de_prueba(cfg)
    monkeypatch.setattr("builtins.input", lambda _texto="": "n")

    assert main(["borrar-cita", str(cid)], cfg) == 0
    assert "No se ha borrado nada." in capsys.readouterr().out

    con = db.conectar(cfg.ruta_bd)
    assert len(db.listar_citas(con)) == 1
    con.close()


def test_borrar_cita_con_numero_que_no_existe(cfg, capsys):
    assert main(["borrar-cita", "7"], cfg) == 1
    assert "No hay ninguna cita con el número 7" in capsys.readouterr().out


def test_cambiar_cita_solo_cambia_lo_indicado(cfg, capsys):
    cid = guardar_cita_de_prueba(cfg)

    assert main(["cambiar-cita", str(cid), "--hora", "9:45"], cfg) == 0
    assert "jueves 12 de noviembre a las 9:45: Analítica (Centro de salud)" in capsys.readouterr().out

    con = db.conectar(cfg.ruta_bd)
    cita = db.obtener_cita(con, cid)
    con.close()
    assert cita.fecha_hora == datetime(2099, 11, 12, 9, 45)
    assert cita.tipo == "analitica"
    assert cita.preparacion == ["Ve en ayunas"]


def test_cambiar_la_hora_hace_que_el_aviso_vuelva_a_salir(cfg, capsys):
    cid = guardar_cita_de_prueba(cfg)

    assert main(["avisos", "--ahora", "10/11/2099 10:00"], cfg) == 0
    assert "Avisos enviados: 1" in capsys.readouterr().out

    assert main(["avisos", "--ahora", "10/11/2099 10:05"], cfg) == 0
    assert "no toca ningún aviso" in capsys.readouterr().out

    assert main(["cambiar-cita", str(cid), "--hora", "9:30"], cfg) == 0
    capsys.readouterr()

    assert main(["avisos", "--simular", "--ahora", "10/11/2099 10:06"], cfg) == 0
    salida = capsys.readouterr().out
    assert "a las 9:30" in salida
    assert "Avisos que tocarían" in salida


def test_cambiar_la_fecha_hace_que_el_aviso_salga_con_el_dia_nuevo(cfg, capsys):
    cid = guardar_cita_de_prueba(cfg)

    assert main(["avisos", "--ahora", "10/11/2099 10:00"], cfg) == 0
    assert "Avisos enviados: 1" in capsys.readouterr().out

    assert main(["cambiar-cita", str(cid), "--fecha", "13/11/2099"], cfg) == 0
    capsys.readouterr()

    assert main(["avisos", "--simular", "--ahora", "11/11/2099 10:00"], cfg) == 0
    salida = capsys.readouterr().out
    assert "viernes 13 de noviembre" in salida
    assert "Avisos que tocarían" in salida


def test_cambiar_cita_sin_opciones_avisa(cfg, capsys):
    cid = guardar_cita_de_prueba(cfg)
    assert main(["cambiar-cita", str(cid)], cfg) == 0
    assert "No has indicado ningún cambio." in capsys.readouterr().out


def test_cambiar_cita_con_numero_que_no_existe(cfg, capsys):
    assert main(["cambiar-cita", "7", "--hora", "9:00"], cfg) == 1
    assert "No hay ninguna cita con el número 7" in capsys.readouterr().out


def test_analitica_sin_preparar_usa_la_lista_sugerida(cfg, capsys):
    assert main([
        "nueva-cita", "--titulo", "Analítica", "--tipo", "analitica",
        "--fecha", "12/11/2099", "--hora", "8:30",
    ], cfg) == 0
    capsys.readouterr()

    assert main(["avisos", "--simular", "--ahora", "10/11/2099 10:00"], cfg) == 0
    salida = capsys.readouterr().out
    assert "1. Ve en ayunas si te lo han indicado." in salida
    assert "2. Lleva la muestra de orina si te la han pedido." in salida
    assert "3. Lleva el volante del médico." in salida
    assert "4. Lleva la tarjeta sanitaria." in salida


def test_preparar_propio_manda_sobre_la_sugerencia(cfg, capsys):
    assert main([
        "nueva-cita", "--titulo", "Analítica", "--tipo", "analitica",
        "--fecha", "12/11/2099", "--hora", "8:30",
        "--preparar", "Lleva mi carpeta azul",
    ], cfg) == 0
    capsys.readouterr()

    assert main(["avisos", "--simular", "--ahora", "10/11/2099 10:00"], cfg) == 0
    salida = capsys.readouterr().out
    assert "1. Lleva mi carpeta azul." in salida
    assert "Ve en ayunas" not in salida


def test_sin_sugerencias_no_anade_preparacion(cfg, capsys):
    assert main([
        "nueva-cita", "--titulo", "Analítica", "--tipo", "analitica",
        "--fecha", "12/11/2099", "--hora", "8:30", "--sin-sugerencias",
    ], cfg) == 0
    capsys.readouterr()

    assert main(["avisos", "--simular", "--ahora", "10/11/2099 10:00"], cfg) == 0
    salida = capsys.readouterr().out
    assert "No hay nada apuntado que preparar. Lleva tu tarjeta sanitaria." in salida
    assert "Ve en ayunas" not in salida


def test_vacuna_sin_preparar_usa_su_lista_sugerida(cfg, capsys):
    assert main([
        "nueva-cita", "--titulo", "Vacuna de la gripe", "--tipo", "vacuna",
        "--fecha", "12/11/2099", "--hora", "8:30",
    ], cfg) == 0
    capsys.readouterr()

    assert main(["avisos", "--simular", "--ahora", "10/11/2099 10:00"], cfg) == 0
    salida = capsys.readouterr().out
    assert "1. Lleva la tarjeta sanitaria." in salida
    assert "2. Lleva la cartilla de vacunación si la tienes." in salida


def crear_tarea_de_la_tension(cfg):
    return main([
        "nueva-tarea", "--titulo", "Tomarte la tensión",
        "--dias", "lunes,jueves", "--hora", "9:00",
    ], cfg)


def test_nueva_tarea_y_lista(cfg, capsys):
    assert crear_tarea_de_la_tension(cfg) == 0
    salida = capsys.readouterr().out
    assert "Tarea guardada:" in salida
    assert "[1] lunes y jueves a las 9:00: Tomarte la tensión" in salida

    assert main(["tareas"], cfg) == 0
    salida = capsys.readouterr().out
    assert "Tienes 1 tarea(s):" in salida
    assert "[1] lunes y jueves a las 9:00: Tomarte la tensión" in salida


def test_tareas_sin_ninguna(cfg, capsys):
    assert main(["tareas"], cfg) == 0
    assert "No tienes tareas apuntadas." in capsys.readouterr().out


def test_tarea_avisa_el_dia_y_no_se_repite(cfg, capsys):
    assert crear_tarea_de_la_tension(cfg) == 0
    capsys.readouterr()

    assert main(["avisos", "--ahora", "09/11/2026 9:00"], cfg) == 0
    salida = capsys.readouterr().out
    assert "Recordatorio: hoy lunes toca tomarte la tensión." in salida
    assert "Avisos enviados: 1" in salida

    assert main(["avisos", "--ahora", "09/11/2026 9:05"], cfg) == 0
    assert "no toca ningún aviso" in capsys.readouterr().out


def test_pausar_tarea_deja_de_avisar(cfg, capsys):
    assert crear_tarea_de_la_tension(cfg) == 0
    capsys.readouterr()

    assert main(["avisos", "--simular", "--ahora", "09/11/2026 9:00"], cfg) == 0
    assert "Recordatorio: hoy lunes toca tomarte la tensión." in capsys.readouterr().out

    assert main(["pausar-tarea", "1"], cfg) == 0
    salida = capsys.readouterr().out
    assert "Tarea pausada:" in salida
    assert "(pausada)" in salida

    assert main(["avisos", "--simular", "--ahora", "09/11/2026 9:00"], cfg) == 0
    assert "no toca ningún aviso" in capsys.readouterr().out


def test_pausar_tarea_con_numero_que_no_existe(cfg, capsys):
    assert main(["pausar-tarea", "7"], cfg) == 1
    assert "No hay ninguna tarea con el número 7" in capsys.readouterr().out


def test_dia_mal_escrito_no_rompe(cfg, capsys):
    codigo = main([
        "nueva-tarea", "--titulo", "Tomarte la tensión",
        "--dias", "finde", "--hora", "9:00",
    ], cfg)
    assert codigo == 1
    assert "lunes,jueves" in capsys.readouterr().out


def test_apuntar_tension_y_ver_el_historial(cfg, capsys, monkeypatch):
    monkeypatch.setattr(
        "acompanante.cli.ahora_local", lambda _cfg: datetime(2026, 11, 9, 9, 5)
    )

    assert main([
        "tension", "130", "85", "--pulso", "72", "--nota", "después de cenar",
    ], cfg) == 0
    salida = capsys.readouterr().out
    assert "Tensión guardada:" in salida
    assert (
        "lunes 9 de noviembre, 9:05: 130 de alta, 85 de baja, pulso 72. "
        "Nota: después de cenar"
    ) in salida

    assert main(["historial-tension"], cfg) == 0
    salida = capsys.readouterr().out
    assert "Estas son tus últimas tomas de tensión:" in salida
    assert (
        "lunes 9 de noviembre, 9:05: 130 de alta, 85 de baja, pulso 72. "
        "Nota: después de cenar"
    ) in salida


def test_tension_sin_pulso_no_ensena_pulso(cfg, capsys, monkeypatch):
    monkeypatch.setattr(
        "acompanante.cli.ahora_local", lambda _cfg: datetime(2026, 11, 9, 9, 5)
    )
    assert main(["tension", "130", "85"], cfg) == 0
    capsys.readouterr()

    assert main(["historial-tension"], cfg) == 0
    salida = capsys.readouterr().out
    assert "lunes 9 de noviembre, 9:05: 130 de alta, 85 de baja" in salida
    assert "pulso" not in salida


def test_historial_de_tension_sin_tomas(cfg, capsys):
    assert main(["historial-tension"], cfg) == 0
    assert "No tienes ninguna toma de tensión apuntada." in capsys.readouterr().out


def test_tension_con_alta_menor_que_baja_avisa(cfg, capsys):
    codigo = main(["tension", "85", "130"], cfg)
    assert codigo == 1
    salida = capsys.readouterr().out
    assert "La tensión de alta no puede ser menor que la de baja" in salida
    assert "Revisa los números" in salida


def test_tension_con_letras_avisa(cfg, capsys):
    codigo = main(["tension", "alta", "85"], cfg)
    assert codigo == 1
    salida = capsys.readouterr().out
    assert "La tensión de alta tiene que ser un número entero" in salida
    assert "Por ejemplo: 130" in salida


def test_tension_con_pulso_mal_escrito_avisa(cfg, capsys):
    codigo = main(["tension", "130", "85", "--pulso", "mucho"], cfg)
    assert codigo == 1
    salida = capsys.readouterr().out
    assert "El pulso tiene que ser un número entero" in salida
    assert "Por ejemplo: 72" in salida


def test_tension_con_numero_que_no_es_positivo_avisa(cfg, capsys):
    codigo = main(["tension", "0", "85"], cfg)
    assert codigo == 1
    assert "La tensión de alta tiene que ser un número mayor que cero" in capsys.readouterr().out


def test_vigilar_atiende_los_mensajes_del_bot(cfg, monkeypatch):
    cfg.telegram_token = "123:ABC"
    cfg.telegram_chat_id = "999"

    class Buzon:
        def enviar(self, texto):
            pass

    monkeypatch.setattr("acompanante.cli.crear_notificador", lambda _cfg: Buzon())

    offsets = []

    def atender_falsa(con, _cfg, offset=None):
        offsets.append(offset)
        return 7 if offset is None else 8

    monkeypatch.setattr("acompanante.cli.atender_mensajes", atender_falsa)

    esperas = []

    def esperar_falsa(segundos):
        esperas.append(segundos)
        if len(esperas) == 2:
            raise KeyboardInterrupt

    monkeypatch.setattr("acompanante.cli.esperar", esperar_falsa)

    assert main(["vigilar"], cfg) == 0
    assert offsets == [None, 7]
    assert esperas == [1, 1]


def test_vigilar_con_bot_revisa_avisos_cada_minuto(cfg, monkeypatch):
    cfg.telegram_token = "123:ABC"
    cfg.telegram_chat_id = "999"

    class Buzon:
        def enviar(self, texto):
            pass

    monkeypatch.setattr("acompanante.cli.crear_notificador", lambda _cfg: Buzon())

    revisiones = []
    monkeypatch.setattr(
        "acompanante.cli._revisar_avisos_una_vez",
        lambda con, _cfg: revisiones.append(1),
    )
    monkeypatch.setattr(
        "acompanante.cli.atender_mensajes",
        lambda con, _cfg, offset=None: offset,
    )

    momentos = iter([0.0, 30.0, 61.0])
    monkeypatch.setattr("acompanante.cli.time.monotonic", lambda: next(momentos))

    esperas = []

    def esperar_falsa(segundos):
        esperas.append(segundos)
        if len(esperas) == 3:
            raise KeyboardInterrupt

    monkeypatch.setattr("acompanante.cli.esperar", esperar_falsa)

    assert main(["vigilar"], cfg) == 0
    assert len(revisiones) == 2
    assert esperas == [1, 1, 1]


def test_citas_ordena_por_fecha_y_hora(cfg, capsys, monkeypatch):
    tarde = Cita(titulo="Tarde", fecha_hora=datetime(2026, 11, 12, 17, 0))
    temprano = Cita(titulo="Temprano", fecha_hora=datetime(2026, 11, 12, 8, 30))
    otro_dia = Cita(titulo="Otro día", fecha_hora=datetime(2026, 11, 10, 9, 0))
    monkeypatch.setattr(
        "acompanante.cli.db.listar_citas",
        lambda con, desde=None: [tarde, otro_dia, temprano],
    )

    assert main(["citas", "--todas"], cfg) == 0
    salida = capsys.readouterr().out
    lineas = [linea for linea in salida.splitlines() if linea.startswith("[")]
    assert "Otro día" in lineas[0]
    assert "Temprano" in lineas[1]
    assert "Tarde" in lineas[2]
