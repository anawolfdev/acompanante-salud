from datetime import date, datetime, time

import pytest

from acompanante import db
from acompanante.config import Config
from acompanante.modelos import Cita, Tarea
from acompanante.recordatorios import (
    avisos_pendientes,
    enviar_avisos,
    momentos_de_aviso,
    tareas_pendientes,
    texto_aviso,
)

CFG = Config()


def nunca(_cid, _tipo):
    return False


def analitica(hora=8, minuto=30):
    return Cita(
        id=1,
        titulo="Analítica de sangre",
        tipo="analitica",
        fecha_hora=datetime(2026, 11, 12, hora, minuto),
        lugar="Centro de salud de Coia",
        preparacion=["Ve en ayunas", "Lleva la muestra de orina", "Lleva el volante."],
    )


def vacuna():
    return Cita(
        id=2,
        titulo="Vacuna de la gripe",
        tipo="vacuna",
        fecha_hora=datetime(2026, 11, 12, 11, 0),
        lugar="Centro de salud",
        preparacion=["Lleva la tarjeta sanitaria"],
    )


def test_momentos_dos_dias_antes_vispera_y_mismo_dia():
    m = momentos_de_aviso(analitica(), CFG)
    assert m["previo"] == datetime(2026, 11, 10, 10, 0)
    assert m["vispera"] == datetime(2026, 11, 11, 21, 0)
    assert m["dia"] == datetime(2026, 11, 12, 7, 30)


def test_sin_ayunas_no_hay_momento_la_noche_antes():
    assert "vispera" not in momentos_de_aviso(vacuna(), CFG)


def test_cita_muy_temprano_avisa_una_hora_antes():
    m = momentos_de_aviso(analitica(hora=7, minuto=45), CFG)
    assert m["dia"] == datetime(2026, 11, 12, 6, 45)


def test_antes_de_tiempo_no_hay_avisos():
    assert avisos_pendientes([analitica()], datetime(2026, 11, 10, 9, 59), CFG, nunca) == []


def test_aviso_previo_cuando_toca():
    avisos = avisos_pendientes([analitica()], datetime(2026, 11, 10, 10, 0), CFG, nunca)
    assert len(avisos) == 1
    assert avisos[0].tipo == "previo"
    assert avisos[0].texto.splitlines()[1].startswith("Pasado mañana, jueves 12 de noviembre, a las 8:30")


def test_aviso_vispera_con_ayunas_cuando_toca():
    avisos = avisos_pendientes([analitica()], datetime(2026, 11, 11, 21, 0), CFG, nunca)
    assert len(avisos) == 1
    assert avisos[0].tipo == "vispera"
    texto = avisos[0].texto
    assert "Mañana, jueves 12 de noviembre, a las 8:30: Analítica de sangre." in texto
    assert "Desde ahora, no comas nada." in texto
    assert "Deja preparado:" in texto
    assert "1. Ve en ayunas." in texto


def test_sin_ayunas_no_avisa_la_noche_antes():
    def solo_falta_previo(_cid, tipo):
        return tipo == "previo"

    assert avisos_pendientes([vacuna()], datetime(2026, 11, 11, 21, 0), CFG, solo_falta_previo) == []
    cita_sin_ayunas = analitica()
    cita_sin_ayunas.preparacion = ["Lleva la muestra de orina", "Lleva el volante"]
    assert (
        avisos_pendientes([cita_sin_ayunas], datetime(2026, 11, 11, 21, 0), CFG, solo_falta_previo)
        == []
    )


def test_analitica_con_ayunas_da_tres_avisos():
    cita = analitica()
    enviados = set()

    def ya_enviado(cid, tipo):
        return (cid, tipo) in enviados

    previo = avisos_pendientes([cita], datetime(2026, 11, 10, 10, 0), CFG, ya_enviado)
    for aviso in previo:
        for tipo in aviso.cubre:
            enviados.add((cita.id, tipo))

    vispera = avisos_pendientes([cita], datetime(2026, 11, 11, 21, 0), CFG, ya_enviado)
    for aviso in vispera:
        for tipo in aviso.cubre:
            enviados.add((cita.id, tipo))

    dia = avisos_pendientes([cita], datetime(2026, 11, 12, 7, 30), CFG, ya_enviado)

    assert [a.tipo for a in previo] == ["previo"]
    assert [a.tipo for a in vispera] == ["vispera"]
    assert [a.tipo for a in dia] == ["dia"]


def test_si_tocan_varios_solo_se_manda_el_del_dia():
    avisos = avisos_pendientes([analitica()], datetime(2026, 11, 12, 7, 40), CFG, nunca)
    assert [a.tipo for a in avisos] == ["dia"]
    assert sorted(avisos[0].cubre) == ["dia", "previo", "vispera"]


def test_cita_pasada_no_avisa():
    assert avisos_pendientes([analitica()], datetime(2026, 11, 12, 9, 0), CFG, nunca) == []


def test_texto_con_lista_numerada_y_sin_emojis():
    texto = texto_aviso(analitica(), datetime(2026, 11, 12, 7, 30))
    assert "Hoy, jueves 12 de noviembre, a las 8:30: Analítica de sangre." in texto
    assert "Dónde: Centro de salud de Coia." in texto
    assert "1. Ve en ayunas." in texto
    assert "3. Lleva el volante." in texto  # sin punto doble
    assert all(ord(c) < 0x2000 for c in texto), "Los avisos no llevan emojis"


def test_enviar_avisos_no_repite(cfg):
    con = db.conectar(cfg.ruta_bd)
    cita = analitica()
    cita.id = None
    db.guardar_cita(con, cita)

    class Buzon:
        def __init__(self):
            self.mensajes = []

        def enviar(self, texto):
            self.mensajes.append(texto)

    buzon = Buzon()
    momento = datetime(2026, 11, 10, 10, 0)
    assert len(enviar_avisos(con, buzon, momento, cfg)) == 1
    assert len(enviar_avisos(con, buzon, momento, cfg)) == 0
    assert len(buzon.mensajes) == 1


def test_enviar_aviso_vispera_no_repite(cfg):
    con = db.conectar(cfg.ruta_bd)
    cita = analitica()
    cita.id = None
    db.guardar_cita(con, cita)

    class Buzon:
        def __init__(self):
            self.mensajes = []

        def enviar(self, texto):
            self.mensajes.append(texto)

    buzon = Buzon()
    momento = datetime(2026, 11, 11, 21, 0)
    assert len(enviar_avisos(con, buzon, momento, cfg)) == 1
    assert len(enviar_avisos(con, buzon, momento, cfg)) == 0
    assert len(buzon.mensajes) == 1
    assert "Desde ahora, no comas nada." in buzon.mensajes[0]


def test_simular_no_apunta_nada(cfg):
    con = db.conectar(cfg.ruta_bd)
    cita = analitica()
    cita.id = None
    db.guardar_cita(con, cita)
    momento = datetime(2026, 11, 10, 10, 0)
    assert len(enviar_avisos(con, None, momento, cfg, simular=True)) == 1
    assert len(enviar_avisos(con, None, momento, cfg, simular=True)) == 1


def test_tipo_no_valido():
    with pytest.raises(ValueError, match="no válido"):
        Cita(titulo="X", tipo="dentista", fecha_hora=datetime(2026, 1, 1, 9, 0))


def tarea_tension(dias=(0,), activa=True):
    return Tarea(
        id=10,
        titulo="Tomarte la tensión",
        dias=list(dias),
        hora=time(9, 0),
        activa=activa,
    )


def test_tarea_avisa_el_lunes_a_la_hora():
    avisos = tareas_pendientes(
        [tarea_tension()], datetime(2026, 11, 9, 9, 0), lambda _tid, _fecha: False
    )
    assert len(avisos) == 1
    assert avisos[0].texto == "Recordatorio: hoy lunes toca tomarte la tensión."


def test_tarea_no_avisa_antes_de_la_hora():
    assert (
        tareas_pendientes(
            [tarea_tension()], datetime(2026, 11, 9, 8, 59), lambda _tid, _fecha: False
        )
        == []
    )


def test_tarea_no_avisa_otro_dia():
    assert (
        tareas_pendientes(
            [tarea_tension()], datetime(2026, 11, 10, 9, 0), lambda _tid, _fecha: False
        )
        == []
    )


def test_tarea_pausada_no_avisa():
    assert (
        tareas_pendientes(
            [tarea_tension(activa=False)],
            datetime(2026, 11, 9, 9, 0),
            lambda _tid, _fecha: False,
        )
        == []
    )


def test_tarea_no_se_repite_el_mismo_dia():
    enviados = set()

    def ya_enviado(tid, fecha):
        return (tid, fecha) in enviados

    tarea = tarea_tension()
    primera = tareas_pendientes([tarea], datetime(2026, 11, 9, 9, 0), ya_enviado)
    for aviso in primera:
        enviados.add((aviso.tarea.id, date(2026, 11, 9)))

    assert len(primera) == 1
    assert tareas_pendientes([tarea], datetime(2026, 11, 9, 9, 5), ya_enviado) == []


def test_enviar_aviso_de_tarea_no_repite(cfg):
    con = db.conectar(cfg.ruta_bd)
    db.guardar_tarea(
        con, Tarea(titulo="Tomarte la tensión", dias=[0], hora=time(9, 0))
    )

    class Buzon:
        def __init__(self):
            self.mensajes = []

        def enviar(self, texto):
            self.mensajes.append(texto)

    buzon = Buzon()
    momento = datetime(2026, 11, 9, 9, 0)
    assert len(enviar_avisos(con, buzon, momento, cfg)) == 1
    assert len(enviar_avisos(con, buzon, momento, cfg)) == 0
    assert buzon.mensajes == ["Recordatorio: hoy lunes toca tomarte la tensión."]


def test_simular_tarea_no_apunta_nada(cfg):
    con = db.conectar(cfg.ruta_bd)
    db.guardar_tarea(
        con, Tarea(titulo="Tomarte la tensión", dias=[0], hora=time(9, 0))
    )
    momento = datetime(2026, 11, 9, 9, 0)
    assert len(enviar_avisos(con, None, momento, cfg, simular=True)) == 1
    assert len(enviar_avisos(con, None, momento, cfg, simular=True)) == 1
