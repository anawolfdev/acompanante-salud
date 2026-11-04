from datetime import datetime

from acompanante import db
from acompanante.modelos import Cita


def test_guardar_y_leer_cita_con_preparacion(cfg):
    con = db.conectar(cfg.ruta_bd)
    cita = Cita(
        titulo="Analítica",
        tipo="analitica",
        fecha_hora=datetime(2026, 11, 12, 8, 30),
        lugar="Centro de salud de Coia",
        preparacion=["Ir en ayunas", "Llevar la muestra de orina"],
    )
    nuevo_id = db.guardar_cita(con, cita)
    leidas = db.listar_citas(con)
    assert len(leidas) == 1
    assert leidas[0].id == nuevo_id
    assert leidas[0].preparacion == ["Ir en ayunas", "Llevar la muestra de orina"]
    assert leidas[0].fecha_hora == datetime(2026, 11, 12, 8, 30)


def test_listar_desde_oculta_las_pasadas(cfg):
    con = db.conectar(cfg.ruta_bd)
    db.guardar_cita(con, Cita(titulo="Vieja", fecha_hora=datetime(2026, 1, 1, 9, 0)))
    db.guardar_cita(con, Cita(titulo="Nueva", fecha_hora=datetime(2026, 12, 1, 9, 0)))
    titulos = [c.titulo for c in db.listar_citas(con, desde=datetime(2026, 6, 1, 0, 0))]
    assert titulos == ["Nueva"]


def test_aviso_enviado_se_recuerda(cfg):
    con = db.conectar(cfg.ruta_bd)
    cid = db.guardar_cita(con, Cita(titulo="X", fecha_hora=datetime(2026, 12, 1, 9, 0)))
    assert not db.aviso_enviado(con, cid, "previo")
    db.marcar_aviso_enviado(con, cid, "previo", datetime(2026, 11, 29, 10, 0))
    db.marcar_aviso_enviado(con, cid, "previo", datetime(2026, 11, 29, 10, 5))  # no falla si se repite
    assert db.aviso_enviado(con, cid, "previo")
