from datetime import datetime

import pytest

from acompanante import conversacion, db
from acompanante.conversacion import (
    AYUDA,
    FALTAN_DATOS,
    IA_NO_ACTIVADA,
    NO_ENTENDIDO,
    NO_LEIDO_PAPEL,
    debe_responder,
    responder,
)
from acompanante.extraer import PropuestaCita
from acompanante.ia import IANoDisponible
from acompanante.modelos import Cita


@pytest.fixture(autouse=True)
def limpiar_citas_pendientes():
    conversacion._pendientes.clear()
    yield
    conversacion._pendientes.clear()


def propuesta_de_ejemplo():
    return PropuestaCita(
        titulo="Analítica de sangre",
        tipo="analitica",
        fecha_hora=datetime(2026, 11, 12, 8, 30),
        lugar="Centro de salud",
        preparacion=["Ve en ayunas"],
    )


def activar_ia(cfg):
    cfg.ia_proveedor = "gemini"
    cfg.ia_api_key = "clave-de-prueba"
    cfg.ia_modelo = "modelo-de-prueba"


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


def test_una_orden_desconocida_no_se_entiende(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/inventada")
    con.close()
    assert respuesta == NO_ENTENDIDO


def test_una_frase_sin_ia_avisa_de_que_no_esta_activada(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "analítica el 12 de noviembre a las 8:30")
    con.close()
    assert respuesta == IA_NO_ACTIVADA


def test_una_frase_propone_la_cita_y_pide_confirmacion(cfg, monkeypatch):
    activar_ia(cfg)
    monkeypatch.setattr(
        "acompanante.conversacion.extraer_cita",
        lambda texto, cfg, ahora=None, imagen=None: propuesta_de_ejemplo(),
    )
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(
        con,
        cfg,
        "analítica el 12 de noviembre a las 8:30 en el centro de salud, en ayunas",
        ahora=datetime(2026, 11, 11, 10, 0),
    )
    citas = db.listar_citas(con)
    con.close()

    assert "He entendido esta cita:" in respuesta
    assert "Analítica de sangre" in respuesta
    assert "jueves 12 de noviembre a las 8:30" in respuesta
    assert "Lugar: Centro de salud" in respuesta
    assert "1. Ve en ayunas" in respuesta
    assert "¿La guardo? Responde sí o no." in respuesta
    assert citas == []


def test_responde_si_y_guarda_la_cita(cfg, monkeypatch):
    activar_ia(cfg)
    monkeypatch.setattr(
        "acompanante.conversacion.extraer_cita",
        lambda texto, cfg, ahora=None, imagen=None: propuesta_de_ejemplo(),
    )
    con = db.conectar(cfg.ruta_bd)
    responder(
        con,
        cfg,
        "analítica el 12 de noviembre a las 8:30 en el centro de salud, en ayunas",
        ahora=datetime(2026, 11, 11, 10, 0),
    )
    respuesta = responder(con, cfg, "sí", ahora=datetime(2026, 11, 11, 10, 1))
    citas = db.listar_citas(con)
    con.close()

    assert "Cita guardada:" in respuesta
    assert len(citas) == 1
    assert citas[0].titulo == "Analítica de sangre"
    assert citas[0].fecha_hora == datetime(2026, 11, 12, 8, 30)
    assert citas[0].lugar == "Centro de salud"
    assert citas[0].preparacion == ["Ve en ayunas"]


def test_responde_no_y_no_guarda_nada(cfg, monkeypatch):
    activar_ia(cfg)
    monkeypatch.setattr(
        "acompanante.conversacion.extraer_cita",
        lambda texto, cfg, ahora=None, imagen=None: propuesta_de_ejemplo(),
    )
    con = db.conectar(cfg.ruta_bd)
    responder(
        con,
        cfg,
        "analítica el 12 de noviembre a las 8:30 en el centro de salud, en ayunas",
        ahora=datetime(2026, 11, 11, 10, 0),
    )
    respuesta = responder(con, cfg, "no", ahora=datetime(2026, 11, 11, 10, 1))
    citas = db.listar_citas(con)
    con.close()

    assert respuesta == "No la he guardado. No se ha apuntado nada."
    assert citas == []


def test_si_falta_la_fecha_o_la_hora_se_pregunta(cfg, monkeypatch):
    activar_ia(cfg)
    monkeypatch.setattr(
        "acompanante.conversacion.extraer_cita",
        lambda texto, cfg, ahora=None, imagen=None: PropuestaCita(
            titulo="Analítica de sangre", tipo="analitica"
        ),
    )
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "analítica de sangre", ahora=datetime(2026, 11, 11, 10, 0))
    citas = db.listar_citas(con)
    con.close()

    assert respuesta == FALTAN_DATOS
    assert citas == []


def test_una_foto_propone_la_cita_y_pide_confirmacion(cfg, monkeypatch):
    activar_ia(cfg)
    recibidas = []

    def extraer(texto, cfg, ahora=None, imagen=None):
        recibidas.append(imagen)
        return propuesta_de_ejemplo()

    monkeypatch.setattr("acompanante.conversacion.extraer_cita", extraer)
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(
        con, cfg, "", ahora=datetime(2026, 11, 11, 10, 0), imagen=b"\xff\xd8foto"
    )
    citas = db.listar_citas(con)
    con.close()

    assert recibidas == [b"\xff\xd8foto"]
    assert "He entendido esta cita:" in respuesta
    assert "Analítica de sangre" in respuesta
    assert "jueves 12 de noviembre a las 8:30" in respuesta
    assert "Lugar: Centro de salud" in respuesta
    assert "1. Ve en ayunas" in respuesta
    assert "¿La guardo? Responde sí o no." in respuesta
    assert citas == []


def test_una_foto_se_guarda_solo_al_decir_si(cfg, monkeypatch):
    activar_ia(cfg)
    monkeypatch.setattr(
        "acompanante.conversacion.extraer_cita",
        lambda texto, cfg, ahora=None, imagen=None: propuesta_de_ejemplo(),
    )
    con = db.conectar(cfg.ruta_bd)
    responder(con, cfg, "", ahora=datetime(2026, 11, 11, 10, 0), imagen=b"\xff\xd8foto")
    respuesta = responder(con, cfg, "sí", ahora=datetime(2026, 11, 11, 10, 1))
    citas = db.listar_citas(con)
    con.close()

    assert "Cita guardada:" in respuesta
    assert len(citas) == 1
    assert citas[0].fecha_hora == datetime(2026, 11, 12, 8, 30)


def test_una_foto_que_no_se_lee_avisa(cfg, monkeypatch):
    activar_ia(cfg)
    monkeypatch.setattr(
        "acompanante.conversacion.extraer_cita",
        lambda texto, cfg, ahora=None, imagen=None: PropuestaCita(
            titulo="Papel de la cita", tipo="cita"
        ),
    )
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "", imagen=b"\xff\xd8foto")
    citas = db.listar_citas(con)
    con.close()

    assert respuesta == NO_LEIDO_PAPEL
    assert "No consigo leer bien el papel." in respuesta
    assert citas == []


def test_una_foto_sin_ia_avisa_de_que_no_esta_activada(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "", imagen=b"\xff\xd8foto")
    con.close()
    assert respuesta == IA_NO_ACTIVADA


def test_si_la_ia_falla_avisa_sin_jerga(cfg, monkeypatch):
    activar_ia(cfg)

    def falla(texto, cfg, ahora=None, imagen=None):
        raise IANoDisponible("El proveedor ha fallado")

    monkeypatch.setattr("acompanante.conversacion.extraer_cita", falla)
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "analítica el 12 de noviembre a las 8:30")
    con.close()

    assert "no puedo entender la frase" in respuesta
    assert "proveedor" not in respuesta


def test_debe_responder_solo_al_chat_autorizado(cfg):
    cfg.telegram_chat_id = "999"
    assert debe_responder("999", cfg) is True
    assert debe_responder(999, cfg) is True
    assert debe_responder("1000", cfg) is False


def test_debe_responder_sin_chat_configurado(cfg):
    assert debe_responder("999", cfg) is False
