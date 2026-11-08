from datetime import date, datetime, time

from acompanante import db
from acompanante.modelos import Cita, Tarea


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


def test_borrar_cita_la_quita_de_la_lista(cfg):
    con = db.conectar(cfg.ruta_bd)
    cid = db.guardar_cita(con, Cita(titulo="X", fecha_hora=datetime(2026, 12, 1, 9, 0)))
    db.borrar_cita(con, cid)
    assert db.listar_citas(con) == []


def test_obtener_cita_avisa_si_no_existe(cfg):
    con = db.conectar(cfg.ruta_bd)
    try:
        db.obtener_cita(con, 7)
    except ValueError as error:
        assert str(error) == "No hay ninguna cita con el número 7"
    else:
        assert False, "Tenía que avisar de que la cita no existe"


def test_actualizar_cita_y_olvidar_los_avisos(cfg):
    con = db.conectar(cfg.ruta_bd)
    cid = db.guardar_cita(con, Cita(titulo="X", fecha_hora=datetime(2026, 12, 1, 9, 0)))
    db.marcar_aviso_enviado(con, cid, "previo", datetime(2026, 11, 29, 10, 0))

    cita = db.obtener_cita(con, cid)
    cita.fecha_hora = datetime(2026, 12, 2, 9, 30)
    db.actualizar_cita(con, cita)
    db.borrar_avisos_de_cita(con, cid)

    assert db.obtener_cita(con, cid).fecha_hora == datetime(2026, 12, 2, 9, 30)
    assert not db.aviso_enviado(con, cid, "previo")


def test_aviso_enviado_se_recuerda(cfg):
    con = db.conectar(cfg.ruta_bd)
    cid = db.guardar_cita(con, Cita(titulo="X", fecha_hora=datetime(2026, 12, 1, 9, 0)))
    assert not db.aviso_enviado(con, cid, "previo")
    db.marcar_aviso_enviado(con, cid, "previo", datetime(2026, 11, 29, 10, 0))
    db.marcar_aviso_enviado(con, cid, "previo", datetime(2026, 11, 29, 10, 5))  # no falla si se repite
    assert db.aviso_enviado(con, cid, "previo")


def test_guardar_y_leer_tarea(cfg):
    con = db.conectar(cfg.ruta_bd)
    tarea = Tarea(titulo="Tomarte la tensión", dias=[0, 3], hora=time(9, 0))
    nuevo_id = db.guardar_tarea(con, tarea)

    leidas = db.listar_tareas(con)
    assert len(leidas) == 1
    assert leidas[0].id == nuevo_id
    assert leidas[0].titulo == "Tomarte la tensión"
    assert leidas[0].dias == [0, 3]
    assert leidas[0].hora == time(9, 0)
    assert leidas[0].activa


def test_pausar_tarea_la_quita_de_las_activas(cfg):
    con = db.conectar(cfg.ruta_bd)
    tid = db.guardar_tarea(
        con, Tarea(titulo="Tomarte la tensión", dias=[0], hora=time(9, 0))
    )

    db.pausar_tarea(con, tid)

    assert not db.obtener_tarea(con, tid).activa
    assert db.listar_tareas(con, solo_activas=True) == []


def test_obtener_tarea_avisa_si_no_existe(cfg):
    con = db.conectar(cfg.ruta_bd)
    try:
        db.obtener_tarea(con, 7)
    except ValueError as error:
        assert str(error) == "No hay ninguna tarea con el número 7"
    else:
        assert False, "Tenía que avisar de que la tarea no existe"


def test_aviso_de_tarea_enviado_se_recuerda(cfg):
    con = db.conectar(cfg.ruta_bd)
    tid = db.guardar_tarea(
        con, Tarea(titulo="Tomarte la tensión", dias=[0], hora=time(9, 0))
    )
    lunes = date(2026, 11, 9)

    assert not db.aviso_tarea_enviado(con, tid, lunes)
    db.marcar_aviso_tarea_enviado(con, tid, lunes, datetime(2026, 11, 9, 9, 0))
    db.marcar_aviso_tarea_enviado(con, tid, lunes, datetime(2026, 11, 9, 9, 5))
    assert db.aviso_tarea_enviado(con, tid, lunes)
    assert not db.aviso_tarea_enviado(con, tid, date(2026, 11, 16))
