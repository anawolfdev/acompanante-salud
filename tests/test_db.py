from datetime import date, datetime, time

from acompanante import db
from acompanante.modelos import Cita, EntradaHistorial, Medicacion, Tarea, Tension


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


def test_guardar_y_leer_tension(cfg):
    con = db.conectar(cfg.ruta_bd)
    tension = Tension(
        fecha_hora=datetime(2026, 11, 9, 9, 5),
        alta=130,
        baja=85,
        pulso=72,
        nota="después de cenar",
    )
    nuevo_id = db.guardar_tension(con, tension)

    leidas = db.listar_tensiones(con)
    assert len(leidas) == 1
    assert leidas[0].id == nuevo_id
    assert leidas[0].fecha_hora == datetime(2026, 11, 9, 9, 5)
    assert leidas[0].alta == 130
    assert leidas[0].baja == 85
    assert leidas[0].pulso == 72
    assert leidas[0].nota == "después de cenar"


def test_tension_sin_pulso_ni_nota(cfg):
    con = db.conectar(cfg.ruta_bd)
    db.guardar_tension(
        con, Tension(fecha_hora=datetime(2026, 11, 9, 9, 5), alta=130, baja=85)
    )

    leida = db.listar_tensiones(con)[0]
    assert leida.pulso is None
    assert leida.nota == ""


def test_actualizar_tension_cambia_los_datos(cfg):
    con = db.conectar(cfg.ruta_bd)
    tension_id = db.guardar_tension(
        con,
        Tension(
            fecha_hora=datetime(2026, 11, 9, 9, 5),
            alta=130,
            baja=85,
            pulso=72,
            nota="después de cenar",
        ),
    )
    tension = db.listar_tensiones(con)[0]
    tension.fecha_hora = datetime(2026, 11, 15, 10, 30)
    tension.alta = 140
    tension.baja = 90
    tension.pulso = None

    db.actualizar_tension(con, tension)

    leida = db.listar_tensiones(con)[0]
    assert leida.id == tension_id
    assert leida.fecha_hora == datetime(2026, 11, 15, 10, 30)
    assert (leida.alta, leida.baja, leida.pulso) == (140, 90, None)
    assert leida.nota == "después de cenar"


def test_obtener_tension_devuelve_la_toma_aunque_sea_antigua(cfg):
    con = db.conectar(cfg.ruta_bd)
    primera = db.guardar_tension(
        con, Tension(fecha_hora=datetime(2026, 11, 1, 9, 0), alta=120, baja=80)
    )
    for dia in range(2, 13):
        db.guardar_tension(
            con, Tension(fecha_hora=datetime(2026, 11, dia, 9, 0), alta=130, baja=85)
        )

    leida = db.obtener_tension(con, primera)

    assert leida.id == primera
    assert (leida.alta, leida.baja) == (120, 80)
    assert leida.fecha_hora == datetime(2026, 11, 1, 9, 0)


def test_obtener_tension_que_no_existe_falla(cfg):
    con = db.conectar(cfg.ruta_bd)
    try:
        db.obtener_tension(con, 99)
    except ValueError as error:
        assert "99" in str(error)
    else:
        raise AssertionError("Tenía que fallar con una toma que no existe")
    finally:
        con.close()


def test_listar_tensiones_devuelve_las_10_mas_recientes(cfg):
    con = db.conectar(cfg.ruta_bd)
    for dia in range(1, 13):
        db.guardar_tension(
            con, Tension(fecha_hora=datetime(2026, 11, dia, 9, 0), alta=120, baja=80)
        )

    leidas = db.listar_tensiones(con)
    assert len(leidas) == 10
    assert [toma.fecha_hora.day for toma in leidas] == [
        12, 11, 10, 9, 8, 7, 6, 5, 4, 3
    ]


def test_borrar_tension_la_quita_de_la_lista(cfg):
    con = db.conectar(cfg.ruta_bd)
    primera = db.guardar_tension(
        con, Tension(fecha_hora=datetime(2026, 11, 9, 9, 0), alta=120, baja=80)
    )
    db.guardar_tension(
        con, Tension(fecha_hora=datetime(2026, 11, 10, 9, 0), alta=130, baja=85)
    )

    db.borrar_tension(con, primera)

    leidas = db.listar_tensiones(con)
    assert len(leidas) == 1
    assert leidas[0].alta == 130


def test_guardar_y_leer_medicacion(cfg):
    con = db.conectar(cfg.ruta_bd)
    medicacion = Medicacion(
        nombre="Paracetamol",
        dosis="1 comprimido",
        pauta="cada 8 horas",
    )
    nuevo_id = db.guardar_medicacion(con, medicacion)

    leidas = db.listar_medicaciones(con)
    assert len(leidas) == 1
    assert leidas[0].id == nuevo_id
    assert leidas[0].nombre == "Paracetamol"
    assert leidas[0].dosis == "1 comprimido"
    assert leidas[0].pauta == "cada 8 horas"
    assert leidas[0].activa is True


def test_medicacion_pausada_no_sale_entre_las_activas(cfg):
    con = db.conectar(cfg.ruta_bd)
    db.guardar_medicacion(
        con, Medicacion(nombre="Ibuprofeno", dosis="1 comprimido", pauta="cada 8 horas")
    )
    medicacion = db.listar_medicaciones(con)[0]
    medicacion.activa = False
    db.actualizar_medicacion(con, medicacion)

    assert db.listar_medicaciones(con) == []
    assert len(db.listar_medicaciones(con, solo_activas=False)) == 1


def test_actualizar_medicacion_cambia_los_datos(cfg):
    con = db.conectar(cfg.ruta_bd)
    db.guardar_medicacion(
        con, Medicacion(nombre="Paracetamol", dosis="1 comprimido", pauta="cada 8 horas")
    )
    medicacion = db.listar_medicaciones(con)[0]
    medicacion.dosis = "2 comprimidos"
    medicacion.pauta = "cada 12 horas"
    db.actualizar_medicacion(con, medicacion)

    leida = db.obtener_medicacion(con, medicacion.id)
    assert leida.dosis == "2 comprimidos"
    assert leida.pauta == "cada 12 horas"


def test_obtener_medicacion_que_no_existe_falla(cfg):
    con = db.conectar(cfg.ruta_bd)
    try:
        db.obtener_medicacion(con, 99)
    except ValueError as error:
        assert "99" in str(error)
    else:
        raise AssertionError("Tenía que fallar con un medicamento que no existe")
    finally:
        con.close()


def test_borrar_medicacion_la_quita_de_la_lista(cfg):
    con = db.conectar(cfg.ruta_bd)
    medicacion_id = db.guardar_medicacion(
        con, Medicacion(nombre="Paracetamol", dosis="1 comprimido", pauta="cada 8 horas")
    )

    db.borrar_medicacion(con, medicacion_id)

    assert db.listar_medicaciones(con) == []


def test_historial_se_lista_de_lo_mas_reciente_a_lo_mas_antiguo(cfg):
    con = db.conectar(cfg.ruta_bd)
    db.guardar_entrada_historial(
        con, EntradaHistorial(descripcion="Analítica", fecha=date(2026, 11, 9))
    )
    db.guardar_entrada_historial(
        con, EntradaHistorial(descripcion="Nota del médico", fecha=date(2026, 11, 10))
    )
    db.guardar_entrada_historial(
        con, EntradaHistorial(descripcion="Vacuna", fecha=date(2026, 11, 8))
    )

    leidas = db.listar_historial(con)

    assert [entrada.descripcion for entrada in leidas] == [
        "Nota del médico",
        "Analítica",
        "Vacuna",
    ]


def test_actualizar_entrada_historial_cambia_descripcion_y_fecha(cfg):
    con = db.conectar(cfg.ruta_bd)
    entrada_id = db.guardar_entrada_historial(
        con, EntradaHistorial(descripcion="Analítica", fecha=date(2026, 11, 9))
    )
    entrada = db.obtener_entrada_historial(con, entrada_id)
    entrada.descripcion = "Analítica de sangre"
    entrada.fecha = date(2026, 11, 12)

    db.actualizar_entrada_historial(con, entrada)

    leida = db.obtener_entrada_historial(con, entrada_id)
    assert leida.descripcion == "Analítica de sangre"
    assert leida.fecha == date(2026, 11, 12)


def test_obtener_entrada_historial_que_no_existe_falla(cfg):
    con = db.conectar(cfg.ruta_bd)
    try:
        db.obtener_entrada_historial(con, 99)
    except ValueError as error:
        assert "99" in str(error)
    else:
        raise AssertionError("Tenía que fallar con una entrada que no existe")
    finally:
        con.close()


def test_borrar_entrada_historial_la_quita_de_la_lista(cfg):
    con = db.conectar(cfg.ruta_bd)
    entrada_id = db.guardar_entrada_historial(
        con, EntradaHistorial(descripcion="Analítica", fecha=date(2026, 11, 9))
    )

    db.borrar_entrada_historial(con, entrada_id)

    assert db.listar_historial(con) == []
