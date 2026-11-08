from datetime import datetime

from acompanante import db
from acompanante.conversacion import (
    AYUDA,
    NO_ENTENDIDO,
    debe_responder,
    responder,
)
from acompanante.modelos import Cita


def guardar_citas(cfg):
    con = db.conectar(cfg.ruta_bd)
    db.guardar_cita(
        con,
        Cita(titulo="Cita pasada", fecha_hora=datetime(2026, 11, 8, 9, 0)),
    )
    for numero in range(1, 7):
        db.guardar_cita(
            con,
            Cita(
                titulo=f"Cita {numero}",
                fecha_hora=datetime(2026, 11, 9 + numero, 8, 30),
                lugar="Centro de salud",
            ),
        )
    return con


def test_proximas_ensena_solo_las_cinco_siguientes(cfg):
    con = guardar_citas(cfg)
    respuesta = responder(con, cfg, "/proximas", ahora=datetime(2026, 11, 9, 9, 0))
    con.close()

    assert respuesta.startswith("Tus próximas citas:")
    assert "1. martes 10 de noviembre a las 8:30: Cita 1 (Centro de salud)" in respuesta
    assert "5. sábado 14 de noviembre a las 8:30: Cita 5 (Centro de salud)" in respuesta
    assert "Cita 6" not in respuesta
    assert "Cita pasada" not in respuesta


def test_proximas_ordena_por_fecha_y_hora(cfg, monkeypatch):
    con = db.conectar(cfg.ruta_bd)
    tarde = Cita(titulo="Tarde", fecha_hora=datetime(2026, 11, 12, 17, 0))
    temprano = Cita(titulo="Temprano", fecha_hora=datetime(2026, 11, 12, 8, 30))
    otro_dia = Cita(titulo="Otro día", fecha_hora=datetime(2026, 11, 10, 9, 0))
    monkeypatch.setattr(
        "acompanante.conversacion.db.listar_citas",
        lambda con, desde=None: [tarde, otro_dia, temprano],
    )

    respuesta = responder(con, cfg, "/proximas", ahora=datetime(2026, 11, 9, 9, 0))
    con.close()

    lineas = respuesta.splitlines()
    assert lineas[1].endswith("Otro día")
    assert lineas[2].endswith("Temprano")
    assert lineas[3].endswith("Tarde")


def test_proximas_sin_citas(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/proximas", ahora=datetime(2026, 11, 9, 9, 0))
    con.close()
    assert respuesta == "No tienes citas apuntadas."


def test_tension_guarda_la_toma_y_responde(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(
        con, cfg, "/tension 130 85 72", ahora=datetime(2026, 11, 9, 9, 5)
    )
    tomas = db.listar_tensiones(con)
    con.close()

    assert respuesta == "Apuntado: 130 de alta, 85 de baja, pulso 72"
    assert len(tomas) == 1
    assert tomas[0].fecha_hora == datetime(2026, 11, 9, 9, 5)
    assert (tomas[0].alta, tomas[0].baja, tomas[0].pulso) == (130, 85, 72)


def test_tension_sin_pulso(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/tension 120 80", ahora=datetime(2026, 11, 9, 9, 5))
    con.close()
    assert respuesta == "Apuntado: 120 de alta, 80 de baja"


def test_tension_con_letras_avisa(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/tension 130 85 alto")
    con.close()
    assert "números enteros" in respuesta
    assert "/tension 130 85 72" in respuesta


def test_tension_con_alta_menor_que_baja_avisa(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/tension 85 130")
    con.close()
    assert "La tensión de alta no puede ser menor que la de baja" in respuesta


def test_tension_incompleta_avisa(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/tension 130")
    con.close()
    assert respuesta == "Para apuntar la tensión escribe: /tension 130 85 72"


def test_ayuda_tiene_cuatro_lineas_y_las_ordenes(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/ayuda")
    con.close()

    assert respuesta == AYUDA
    assert len(respuesta.splitlines()) == 4
    assert "/proximas" in respuesta
    assert "/tension" in respuesta
    assert "/ayuda" in respuesta


def test_cualquier_otra_cosa_no_se_entiende(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "hola, ¿qué tal?")
    con.close()
    assert respuesta == NO_ENTENDIDO


def test_debe_responder_solo_al_chat_autorizado(cfg):
    cfg.telegram_chat_id = "999"
    assert debe_responder("999", cfg) is True
    assert debe_responder(999, cfg) is True
    assert debe_responder("1000", cfg) is False


def test_debe_responder_sin_chat_configurado(cfg):
    assert debe_responder("999", cfg) is False
