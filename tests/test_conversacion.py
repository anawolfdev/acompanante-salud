from datetime import datetime

import pytest

from acompanante import acciones, conversacion, db
from acompanante.conversacion import (
    AYUDA,
    ANADIR_PIDE_FECHA,
    ANADIR_PIDE_LUGAR,
    ANADIR_PIDE_TITULO,
    FALTAN_DATOS,
    HISTORIAL_CABECERA,
    IA_NO_ACTIVADA,
    NO_ENTENDIDO,
    NO_LEIDO_PAPEL,
    SIN_TENSION,
    TENSION_PIDE_FECHA,
    TENSION_PIDE_VALORES,
    debe_responder,
    responder,
    responder_callback,
)
from acompanante.extraer import PropuestaCita
from acompanante.ia import IANoDisponible
from acompanante.modelos import Cita, Tension


@pytest.fixture(autouse=True)
def limpiar_citas_pendientes():
    conversacion._pendientes.clear()
    conversacion._borrados_pendientes.clear()
    conversacion._cambios_pendientes.clear()
    conversacion._tensiones_pendientes.clear()
    conversacion._cambios_por_boton.clear()
    conversacion._modificaciones_tension.clear()
    conversacion._pasos_anadir.clear()
    yield
    conversacion._pendientes.clear()
    conversacion._borrados_pendientes.clear()
    conversacion._cambios_pendientes.clear()
    conversacion._tensiones_pendientes.clear()
    conversacion._cambios_por_boton.clear()
    conversacion._modificaciones_tension.clear()
    conversacion._pasos_anadir.clear()


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


def test_proximas_avisa_que_ahora_se_llama_citas(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/proximas", ahora=datetime(2026, 11, 9, 9, 0))
    con.close()
    assert respuesta == "Ahora se llama citas"


def test_citas_ensena_todas_las_futuras_con_su_numero(cfg):
    con = guardar_citas(cfg)
    respuesta = responder(con, cfg, "/citas", ahora=datetime(2026, 11, 9, 9, 0))
    con.close()

    lineas = respuesta.splitlines()
    assert lineas[0] == "Estas son todas tus citas futuras:"
    assert len(lineas) == 7
    assert lineas[1].startswith("[2] martes 10 de noviembre a las 8:30: Cita 1")
    assert lineas[6].startswith("[7] domingo 15 de noviembre a las 8:30: Cita 6")
    assert "Cita pasada" not in respuesta


def test_citas_ordena_por_fecha_y_hora(cfg, monkeypatch):
    con = db.conectar(cfg.ruta_bd)
    tarde = Cita(id=3, titulo="Tarde", fecha_hora=datetime(2026, 11, 12, 17, 0))
    temprano = Cita(id=2, titulo="Temprano", fecha_hora=datetime(2026, 11, 12, 8, 30))
    otro_dia = Cita(id=1, titulo="Otro día", fecha_hora=datetime(2026, 11, 10, 9, 0))
    monkeypatch.setattr(
        "acompanante.conversacion.db.listar_citas",
        lambda con, desde=None: [tarde, otro_dia, temprano],
    )

    respuesta = responder(con, cfg, "/citas", ahora=datetime(2026, 11, 9, 9, 0))
    con.close()

    lineas = respuesta.splitlines()
    assert lineas[1].endswith("Otro día")
    assert lineas[2].endswith("Temprano")
    assert lineas[3].endswith("Tarde")


def test_citas_sin_citas(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/citas", ahora=datetime(2026, 11, 9, 9, 0))
    con.close()
    assert respuesta == "No tienes citas apuntadas."
    assert respuesta.botones == []


def test_citas_muestra_cada_cita_en_su_mensaje_con_botones(cfg):
    con = guardar_citas(cfg)
    ahora = datetime(2026, 11, 9, 9, 0)
    respuesta = responder(con, cfg, "/citas", ahora=ahora)
    citas = sorted(
        db.listar_citas(con, desde=ahora), key=lambda cita: cita.fecha_hora
    )
    con.close()

    assert len(respuesta.mensajes) == len(citas) + 1
    assert respuesta.mensajes[0] == "Estas son todas tus citas futuras:"
    assert respuesta.mensajes[0].botones == []
    for parte, cita in zip(respuesta.mensajes[1:], citas):
        assert parte == acciones.linea_cita(cita)
        assert parte.botones == [
            [
                {"text": "Cambiar", "callback_data": f"cambiar:{cita.id}"},
                {"text": "Borrar", "callback_data": f"borrar_cita:{cita.id}"},
            ]
        ]


def test_anadir_ensena_la_cita_y_pide_confirmacion(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(
        con, cfg, "/añadir Analítica | 12/11/2026 8:30 | Centro de salud"
    )
    citas = db.listar_citas(con)
    con.close()

    assert "He entendido esta cita:" in respuesta
    assert "Analítica" in respuesta
    assert "jueves 12 de noviembre a las 8:30" in respuesta
    assert "Lugar: Centro de salud" in respuesta
    assert "1. Lleva la tarjeta sanitaria" in respuesta
    assert "¿La guardo? Responde sí o no." in respuesta
    assert citas == []


def test_anadir_despues_de_decir_si_guarda_la_cita(cfg):
    con = db.conectar(cfg.ruta_bd)
    responder(con, cfg, "/añadir Analítica | 12/11/2026 8:30 | Centro de salud")
    respuesta = responder(con, cfg, "sí")
    citas = db.listar_citas(con)
    con.close()

    assert "Cita guardada:" in respuesta
    assert "jueves 12 de noviembre a las 8:30: Analítica" in respuesta
    assert "Lugar: Centro de salud" in respuesta
    assert len(citas) == 1
    assert citas[0].titulo == "Analítica"
    assert citas[0].fecha_hora == datetime(2026, 11, 12, 8, 30)
    assert citas[0].lugar == "Centro de salud"
    assert citas[0].tipo == "cita"
    assert citas[0].preparacion == [
        "Lleva la tarjeta sanitaria",
        "Lleva los informes o papeles que te hayan dado",
    ]


def test_anadir_despues_de_decir_no_no_guarda(cfg):
    con = db.conectar(cfg.ruta_bd)
    responder(con, cfg, "/añadir Analítica | 12/11/2026 8:30 | Centro de salud")
    respuesta = responder(con, cfg, "no")
    citas = db.listar_citas(con)
    con.close()

    assert respuesta == "No la he guardado. No se ha apuntado nada."
    assert citas == []


def test_anadir_sin_lugar_funciona(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/añadir Vacuna de la gripe | 13/11/2026 9:00")
    assert "Lugar:" not in respuesta

    responder(con, cfg, "sí")
    citas = db.listar_citas(con)
    con.close()

    assert len(citas) == 1
    assert citas[0].lugar == ""


def test_anadir_fecha_mal_escrita_avisa_con_ejemplo(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/añadir Analítica | mañana 8:30 | Centro de salud")
    citas = db.listar_citas(con)
    con.close()

    assert "No he entendido la fecha o la hora." in respuesta
    assert "/añadir Analítica | 12/11/2026 8:30 | Centro de salud" in respuesta
    assert citas == []


def test_anadir_sin_datos_empieza_paso_a_paso(cfg):
    con = db.conectar(cfg.ruta_bd)

    respuesta = responder(con, cfg, "/añadir")
    assert respuesta == ANADIR_PIDE_TITULO

    respuesta = responder(con, cfg, "Analítica de sangre")
    assert respuesta == ANADIR_PIDE_FECHA

    respuesta = responder(con, cfg, "12/11/2026 8:30")
    assert respuesta == ANADIR_PIDE_LUGAR

    respuesta = responder(con, cfg, "Centro de salud")
    assert "He entendido esta cita:" in respuesta
    assert "Analítica de sangre" in respuesta
    assert "jueves 12 de noviembre a las 8:30" in respuesta
    assert "Lugar: Centro de salud" in respuesta
    assert "¿La guardo? Responde sí o no." in respuesta

    respuesta = responder(con, cfg, "sí")
    citas = db.listar_citas(con)
    con.close()

    assert "Cita guardada:" in respuesta
    assert len(citas) == 1
    assert citas[0].titulo == "Analítica de sangre"
    assert citas[0].lugar == "Centro de salud"


def test_anadir_sin_barra_tambien_empieza_paso_a_paso(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "añadir")
    con.close()
    assert respuesta == ANADIR_PIDE_TITULO


def test_anadir_paso_a_paso_sin_lugar(cfg):
    con = db.conectar(cfg.ruta_bd)
    responder(con, cfg, "/añadir")
    responder(con, cfg, "Vacuna de la gripe")
    responder(con, cfg, "13/11/2026 9:00")

    respuesta = responder(con, cfg, "no")
    responder(con, cfg, "sí")
    citas = db.listar_citas(con)
    con.close()

    assert "Lugar:" not in respuesta
    assert len(citas) == 1
    assert citas[0].lugar == ""


def test_anadir_paso_a_paso_si_la_fecha_esta_mal_la_vuelve_a_preguntar(cfg):
    con = db.conectar(cfg.ruta_bd)
    responder(con, cfg, "/añadir")
    responder(con, cfg, "Analítica")

    respuesta = responder(con, cfg, "mañana 8:30")
    assert respuesta == ANADIR_PIDE_FECHA

    respuesta = responder(con, cfg, "12/11/2026 8:30")
    assert respuesta == ANADIR_PIDE_LUGAR
    con.close()


def test_anadir_con_formato_incompleto_avisa_con_ejemplo(cfg):
    con = db.conectar(cfg.ruta_bd)
    for texto in (
        "/añadir Analítica 12/11/2026 8:30",
        "/añadir | 12/11/2026 8:30",
        "/añadir Analítica | | Centro de salud",
    ):
        respuesta = responder(con, cfg, texto)
        assert "No sé qué cita quieres añadir o cuándo." in respuesta
        assert "/añadir Analítica | 12/11/2026 8:30 | Centro de salud" in respuesta

    citas = db.listar_citas(con)
    con.close()
    assert citas == []


def test_anadir_se_olvida_si_se_escribe_otra_orden(cfg):
    con = db.conectar(cfg.ruta_bd)
    responder(con, cfg, "/añadir Analítica | 12/11/2026 8:30 | Centro de salud")
    responder(con, cfg, "/citas")
    responder(con, cfg, "sí")
    citas = db.listar_citas(con)
    con.close()

    assert citas == []


def test_anadir_varias_citas_separadas_por_punto_y_coma(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(
        con,
        cfg,
        "añadir Médico | 12/11/2026 8:30 | Lugar: Vigo ; "
        "Dentista | 15/11/2026 10:00 | Lugar: Vigo",
    )
    assert "He entendido estas citas:" in respuesta
    assert "Médico" in respuesta
    assert "Dentista" in respuesta
    assert "jueves 12 de noviembre a las 8:30" in respuesta
    assert "domingo 15 de noviembre a las 10:00" in respuesta
    assert "Lugar: Lugar:" not in respuesta
    assert "¿Las guardo? Responde sí o no." in respuesta

    respuesta = responder(con, cfg, "sí")
    citas = db.listar_citas(con)
    con.close()

    assert respuesta.startswith("Citas guardadas:")
    assert [cita.titulo for cita in citas] == ["Médico", "Dentista"]
    assert [cita.lugar for cita in citas] == ["Vigo", "Vigo"]


def guardar_cita_de_ejemplo(cfg):
    con = db.conectar(cfg.ruta_bd)
    cita = Cita(
        titulo="Analítica",
        fecha_hora=datetime(2026, 11, 12, 8, 30),
        lugar="Centro de salud",
    )
    db.guardar_cita(con, cita)
    return con, cita


def test_borrar_ensena_la_cita_y_pide_confirmacion(cfg):
    con, cita = guardar_cita_de_ejemplo(cfg)
    respuesta = responder(
        con, cfg, f"/borrar {cita.id}", ahora=datetime(2026, 11, 9, 9, 0)
    )
    citas = db.listar_citas(con)
    con.close()

    assert "Vas a borrar esta cita:" in respuesta
    assert f"[{cita.id}] jueves 12 de noviembre a las 8:30: Analítica (Centro de salud)" in respuesta
    assert "¿La borro? Responde sí o no." in respuesta
    assert len(citas) == 1


def test_borrar_despues_de_decir_si_la_quita(cfg):
    con, cita = guardar_cita_de_ejemplo(cfg)
    responder(con, cfg, f"/borrar {cita.id}", ahora=datetime(2026, 11, 9, 9, 0))
    respuesta = responder(con, cfg, "sí", ahora=datetime(2026, 11, 9, 9, 1))
    citas = db.listar_citas(con)
    con.close()

    assert respuesta == "Cita borrada."
    assert citas == []


def test_borrar_despues_de_decir_no_no_borra(cfg):
    con, cita = guardar_cita_de_ejemplo(cfg)
    responder(con, cfg, f"/borrar {cita.id}", ahora=datetime(2026, 11, 9, 9, 0))
    respuesta = responder(con, cfg, "no", ahora=datetime(2026, 11, 9, 9, 1))
    citas = db.listar_citas(con)
    con.close()

    assert respuesta == "No la he borrado. No se ha borrado nada."
    assert len(citas) == 1


def test_borrar_numero_que_no_existe_avisa(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/borrar 7")
    con.close()

    assert respuesta == (
        "No hay ninguna cita con el número 7.\n"
        "Escribe /citas para ver los números de tus citas."
    )


def test_borrar_sin_numero_avisa(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/borrar")
    con.close()

    assert "No sé qué cita quieres borrar." in respuesta
    assert "/borrar 3" in respuesta


def test_borrar_varias_citas_a_la_vez(cfg):
    con = guardar_citas(cfg)
    respuesta = responder(
        con, cfg, "borrar 2 5 7", ahora=datetime(2026, 11, 9, 9, 0)
    )
    assert "Vas a borrar estas citas:" in respuesta
    assert "[2] martes 10 de noviembre a las 8:30: Cita 1" in respuesta
    assert "[5] viernes 13 de noviembre a las 8:30: Cita 4" in respuesta
    assert "[7] domingo 15 de noviembre a las 8:30: Cita 6" in respuesta
    assert "¿Las borro? Responde sí o no." in respuesta

    respuesta = responder(con, cfg, "sí", ahora=datetime(2026, 11, 9, 9, 1))
    titulos = [cita.titulo for cita in db.listar_citas(con)]
    con.close()

    assert respuesta == "Citas borradas."
    assert titulos == ["Cita pasada", "Cita 2", "Cita 3", "Cita 5"]


def test_cambiar_ensena_la_cita_actual_y_la_nueva_y_pide_confirmacion(cfg):
    con, cita = guardar_cita_de_ejemplo(cfg)
    respuesta = responder(
        con, cfg, f"/cambiar {cita.id} 13/11/2026 9:45", ahora=datetime(2026, 11, 9, 9, 0)
    )
    citas = db.listar_citas(con)
    con.close()

    assert "Vas a cambiar esta cita:" in respuesta
    assert f"[{cita.id}] jueves 12 de noviembre a las 8:30: Analítica (Centro de salud)" in respuesta
    assert "Quedará así:" in respuesta
    assert f"[{cita.id}] viernes 13 de noviembre a las 9:45: Analítica (Centro de salud)" in respuesta
    assert "¿La cambio? Responde sí o no." in respuesta
    assert citas[0].fecha_hora == datetime(2026, 11, 12, 8, 30)


def test_cambiar_despues_de_decir_si_la_cambia(cfg):
    con, cita = guardar_cita_de_ejemplo(cfg)
    responder(con, cfg, f"/cambiar {cita.id} 13/11/2026 9:45", ahora=datetime(2026, 11, 9, 9, 0))
    respuesta = responder(con, cfg, "sí", ahora=datetime(2026, 11, 9, 9, 1))
    citas = db.listar_citas(con)
    con.close()

    assert respuesta.startswith("Cita cambiada:")
    assert f"[{cita.id}] viernes 13 de noviembre a las 9:45: Analítica (Centro de salud)" in respuesta
    assert citas[0].fecha_hora == datetime(2026, 11, 13, 9, 45)
    assert citas[0].titulo == "Analítica"
    assert citas[0].lugar == "Centro de salud"


def test_cambiar_despues_de_decir_no_no_cambia(cfg):
    con, cita = guardar_cita_de_ejemplo(cfg)
    responder(con, cfg, f"/cambiar {cita.id} 13/11/2026 9:45", ahora=datetime(2026, 11, 9, 9, 0))
    respuesta = responder(con, cfg, "no", ahora=datetime(2026, 11, 9, 9, 1))
    citas = db.listar_citas(con)
    con.close()

    assert respuesta == "No la he cambiado. No se ha cambiado nada."
    assert citas[0].fecha_hora == datetime(2026, 11, 12, 8, 30)


def test_cambiar_numero_que_no_existe_avisa(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/cambiar 7 13/11/2026 9:45")
    con.close()

    assert "No hay ninguna cita con el número 7." in respuesta
    assert "Escribe /citas para ver los números de tus citas." in respuesta


def test_cambiar_fecha_mal_escrita_avisa_con_ejemplo(cfg):
    con, cita = guardar_cita_de_ejemplo(cfg)
    respuesta = responder(con, cfg, f"/cambiar {cita.id} mañana 9:45")
    con.close()

    assert "No he entendido la fecha o la hora." in respuesta
    assert "/cambiar 3 12/11/2026 8:30" in respuesta


def test_cambiar_sin_datos_avisa_con_ejemplo(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/cambiar")
    con.close()

    assert "No sé qué cita quieres cambiar o cuándo." in respuesta
    assert "/cambiar 3 12/11/2026 8:30" in respuesta


def test_cambiar_varias_citas_a_la_vez(cfg):
    con = db.conectar(cfg.ruta_bd)
    primera = Cita(titulo="Médico", fecha_hora=datetime(2026, 11, 12, 8, 30))
    segunda = Cita(titulo="Dentista", fecha_hora=datetime(2026, 11, 13, 9, 0))
    db.guardar_cita(con, primera)
    db.guardar_cita(con, segunda)

    respuesta = responder(
        con,
        cfg,
        f"cambiar {primera.id} 20/11/2026 10:00 ; {segunda.id} 21/11/2026 11:00",
        ahora=datetime(2026, 11, 9, 9, 0),
    )
    assert "Vas a cambiar estas citas:" in respuesta
    assert "Médico" in respuesta
    assert "Dentista" in respuesta
    assert "¿Las cambio? Responde sí o no." in respuesta

    respuesta = responder(con, cfg, "sí", ahora=datetime(2026, 11, 9, 9, 1))
    citas = db.listar_citas(con)
    con.close()

    assert respuesta.startswith("Citas cambiadas:")
    assert citas[0].fecha_hora == datetime(2026, 11, 20, 10, 0)
    assert citas[1].fecha_hora == datetime(2026, 11, 21, 11, 0)


def test_cambiar_la_fecha_hace_que_los_avisos_vuelvan_a_salir(cfg):
    con, cita = guardar_cita_de_ejemplo(cfg)
    db.marcar_aviso_enviado(con, cita.id, "previo", datetime(2026, 11, 10, 10, 0))
    assert db.aviso_enviado(con, cita.id, "previo") is True

    responder(con, cfg, f"/cambiar {cita.id} 13/11/2026 9:45", ahora=datetime(2026, 11, 9, 9, 0))
    responder(con, cfg, "sí", ahora=datetime(2026, 11, 9, 9, 1))

    assert db.aviso_enviado(con, cita.id, "previo") is False
    con.close()


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
    assert "con números" in respuesta
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
    assert respuesta == (
        "Para apuntar la tensión escribe: /tension 130 85 72. "
        "El primer número es la tensión alta, el segundo la baja y el tercero, "
        "si quieres, el pulso."
    )


def test_tension_con_fecha_y_hora_al_final(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(
        con,
        cfg,
        "/tension 130 85 72 14/11/2026 8:30",
        ahora=datetime(2026, 11, 9, 9, 5),
    )
    tomas = db.listar_tensiones(con)
    con.close()

    assert "Apuntado: 130 de alta, 85 de baja, pulso 72" in respuesta
    assert "sábado 14 de noviembre a las 8:30" in respuesta
    assert tomas[0].fecha_hora == datetime(2026, 11, 14, 8, 30)


def test_tension_con_fecha_al_final_y_sin_pulso(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(
        con,
        cfg,
        "/tension 120 80 14/11/2026 8:30",
        ahora=datetime(2026, 11, 9, 9, 5),
    )
    tomas = db.listar_tensiones(con)
    con.close()

    assert "Apuntado: 120 de alta, 80 de baja" in respuesta
    assert tomas[0].fecha_hora == datetime(2026, 11, 14, 8, 30)
    assert tomas[0].pulso is None


def test_tension_con_fecha_mal_escrita_avisa(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/tension 130 85 14/11/2026 25:00")
    tomas = db.listar_tensiones(con)
    con.close()

    assert "No he entendido la fecha o la hora." in respuesta
    assert "14/11/2026 8:30" in respuesta
    assert tomas == []


def guardar_tensiones_de_ejemplo(cfg):
    con = db.conectar(cfg.ruta_bd)
    db.guardar_tension(
        con,
        Tension(fecha_hora=datetime(2026, 11, 9, 9, 0), alta=120, baja=80),
    )
    db.guardar_tension(
        con,
        Tension(
            fecha_hora=datetime(2026, 11, 10, 9, 0),
            alta=130,
            baja=85,
            pulso=72,
            nota="después de cenar",
        ),
    )
    return con


def test_borrar_tension_ensena_la_mas_reciente_y_pide_confirmacion(cfg):
    con = guardar_tensiones_de_ejemplo(cfg)
    respuesta = responder(con, cfg, "borrar tension 1")
    tomas = db.listar_tensiones(con)
    con.close()

    assert "Vas a borrar esta toma de tensión:" in respuesta
    assert "130 de alta, 85 de baja, pulso 72. Nota: después de cenar" in respuesta
    assert "¿La borro? Responde sí o no." in respuesta
    assert len(tomas) == 2


def test_borrar_tension_despues_de_decir_si_la_quita(cfg):
    con = guardar_tensiones_de_ejemplo(cfg)
    responder(con, cfg, "borrar tension 1")
    respuesta = responder(con, cfg, "sí")
    tomas = db.listar_tensiones(con)
    con.close()

    assert respuesta == "Toma de tensión borrada."
    assert len(tomas) == 1
    assert tomas[0].alta == 120


def test_borrar_tension_despues_de_decir_no_no_borra(cfg):
    con = guardar_tensiones_de_ejemplo(cfg)
    responder(con, cfg, "borrar tension 1")
    respuesta = responder(con, cfg, "no")
    tomas = db.listar_tensiones(con)
    con.close()

    assert respuesta == "No la he borrado. No se ha borrado nada."
    assert len(tomas) == 2


def test_borrar_tension_con_barra_y_guion_funciona(cfg):
    con = guardar_tensiones_de_ejemplo(cfg)
    respuesta = responder(con, cfg, "/borrar-tension 2")
    assert "120 de alta, 80 de baja" in respuesta

    responder(con, cfg, "sí")
    tomas = db.listar_tensiones(con)
    con.close()

    assert len(tomas) == 1
    assert tomas[0].alta == 130


def test_borrar_tension_con_barra_baja_tambien_funciona(cfg):
    con = guardar_tensiones_de_ejemplo(cfg)
    respuesta = responder(con, cfg, "/borrar_tension 2")
    responder(con, cfg, "sí")
    tomas = db.listar_tensiones(con)
    con.close()

    assert "120 de alta, 80 de baja" in respuesta
    assert len(tomas) == 1
    assert tomas[0].alta == 130


def test_borrar_tension_numero_que_no_existe_avisa(cfg):
    con = guardar_tensiones_de_ejemplo(cfg)
    respuesta = responder(con, cfg, "/borrar-tension 7")
    con.close()

    assert respuesta == (
        "No hay ninguna toma de tensión con el número 7.\n"
        "Escribe /historial para ver tus últimas tomas."
    )


def test_borrar_tension_sin_numero_avisa(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/borrar-tension")
    con.close()

    assert "No sé qué toma de tensión quieres borrar." in respuesta
    assert "/borrar-tension 1" in respuesta


def test_boton_cambiar_pide_la_fecha_y_cambia_la_cita(cfg):
    con, cita = guardar_cita_de_ejemplo(cfg)

    respuesta = responder_callback(con, cfg, f"cambiar:{cita.id}")
    assert "Escribe la nueva fecha y hora." in respuesta
    assert "jueves 12 de noviembre a las 8:30" in respuesta

    respuesta = responder(
        con, cfg, "13/11/2026 9:45", ahora=datetime(2026, 11, 9, 9, 0)
    )
    citas = db.listar_citas(con)
    con.close()

    assert "Cita cambiada:" in respuesta
    assert citas[0].fecha_hora == datetime(2026, 11, 13, 9, 45)
    assert citas[0].titulo == "Analítica"


def test_boton_cambiar_con_fecha_mal_la_vuelve_a_pedir(cfg):
    con, cita = guardar_cita_de_ejemplo(cfg)
    responder_callback(con, cfg, f"cambiar:{cita.id}")

    respuesta = responder(con, cfg, "mañana")
    citas = db.listar_citas(con)
    con.close()

    assert "No he entendido la fecha o la hora." in respuesta
    assert citas[0].fecha_hora == datetime(2026, 11, 12, 8, 30)


def test_boton_borrar_cita_pide_confirmacion_y_borra(cfg):
    con, cita = guardar_cita_de_ejemplo(cfg)

    respuesta = responder_callback(con, cfg, f"borrar_cita:{cita.id}")
    assert "Vas a borrar esta cita:" in respuesta
    assert respuesta.botones == [
        [
            {"text": "Sí", "callback_data": "confirmar_borrar_citas"},
            {"text": "No", "callback_data": "cancelar_borrar_citas"},
        ]
    ]

    respuesta = responder_callback(con, cfg, "confirmar_borrar_citas")
    citas = db.listar_citas(con)
    con.close()

    assert respuesta == "Cita borrada."
    assert citas == []


def test_boton_borrar_cita_cancelar_no_borra(cfg):
    con, cita = guardar_cita_de_ejemplo(cfg)
    responder_callback(con, cfg, f"borrar_cita:{cita.id}")

    respuesta = responder_callback(con, cfg, "cancelar_borrar_citas")
    citas = db.listar_citas(con)
    con.close()

    assert respuesta == "No la he borrado. No se ha borrado nada."
    assert len(citas) == 1


def test_boton_borrar_tension_pide_confirmacion_y_borra(cfg):
    con = guardar_tensiones_de_ejemplo(cfg)
    toma = db.listar_tensiones(con)[0]

    respuesta = responder_callback(con, cfg, f"borrar_tension:{toma.id}")
    assert "Vas a borrar esta toma de tensión:" in respuesta
    assert respuesta.botones == [
        [
            {"text": "Sí", "callback_data": "confirmar_borrar_tension"},
            {"text": "No", "callback_data": "cancelar_borrar_tension"},
        ]
    ]

    respuesta = responder_callback(con, cfg, "confirmar_borrar_tension")
    tomas = db.listar_tensiones(con)
    con.close()

    assert respuesta == "Toma de tensión borrada."
    assert len(tomas) == 1
    assert tomas[0].alta == 120


def test_boton_modificar_pide_los_valores_y_la_fecha_opcional(cfg):
    con = guardar_tensiones_de_ejemplo(cfg)
    toma = db.listar_tensiones(con)[0]

    respuesta = responder_callback(con, cfg, f"modificar_tension:{toma.id}")
    assert respuesta == TENSION_PIDE_VALORES

    respuesta = responder(con, cfg, "140 90 75")
    assert respuesta == TENSION_PIDE_FECHA

    respuesta = responder(con, cfg, "no")
    tomas = db.listar_tensiones(con)
    con.close()

    assert "Toma de tensión modificada:" in respuesta
    assert "140 de alta, 90 de baja, pulso 75" in respuesta
    assert tomas[0].fecha_hora == toma.fecha_hora
    assert (tomas[0].alta, tomas[0].baja, tomas[0].pulso) == (140, 90, 75)
    assert tomas[0].nota == "después de cenar"


def test_boton_modificar_permite_cambiar_la_fecha(cfg):
    con = guardar_tensiones_de_ejemplo(cfg)
    toma = db.listar_tensiones(con)[0]
    responder_callback(con, cfg, f"modificar_tension:{toma.id}")
    responder(con, cfg, "140 90")

    respuesta = responder(con, cfg, "15/11/2026 10:30")
    tomas = db.listar_tensiones(con)
    con.close()

    assert "domingo 15 de noviembre, 10:30" in respuesta
    assert tomas[0].fecha_hora == datetime(2026, 11, 15, 10, 30)
    assert tomas[0].pulso is None


def test_boton_modificar_con_valores_mal_los_vuelve_a_pedir(cfg):
    con = guardar_tensiones_de_ejemplo(cfg)
    toma = db.listar_tensiones(con)[0]
    responder_callback(con, cfg, f"modificar_tension:{toma.id}")

    respuesta = responder(con, cfg, "alto bajo")
    assert "No he entendido los valores." in respuesta

    respuesta = responder(con, cfg, "85 130")
    assert "La tensión de alta no puede ser menor que la de baja" in respuesta

    respuesta = responder(con, cfg, "140 90 75")
    assert respuesta == TENSION_PIDE_FECHA
    con.close()


def test_boton_modificar_con_fecha_mal_la_vuelve_a_pedir(cfg):
    con = guardar_tensiones_de_ejemplo(cfg)
    toma = db.listar_tensiones(con)[0]
    responder_callback(con, cfg, f"modificar_tension:{toma.id}")
    responder(con, cfg, "140 90 75")

    respuesta = responder(con, cfg, "mañana")
    assert "No he entendido la fecha o la hora." in respuesta

    respuesta = responder(con, cfg, "no")
    tomas = db.listar_tensiones(con)
    con.close()

    assert "Toma de tensión modificada:" in respuesta
    assert (tomas[0].alta, tomas[0].baja, tomas[0].pulso) == (140, 90, 75)


def test_boton_modificar_una_toma_que_ya_no_existe_avisa(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder_callback(con, cfg, "modificar_tension:99")
    con.close()

    assert respuesta == "Ese botón ya no vale. Escribe /ayuda para ver lo que sé hacer."


def test_boton_modificar_una_toma_antigua_sigue_funcionando(cfg):
    con = db.conectar(cfg.ruta_bd)
    antigua = db.guardar_tension(
        con, Tension(fecha_hora=datetime(2026, 11, 1, 9, 0), alta=120, baja=80)
    )
    for dia in range(2, 13):
        db.guardar_tension(
            con, Tension(fecha_hora=datetime(2026, 11, dia, 9, 0), alta=130, baja=85)
        )

    respuesta = responder_callback(con, cfg, f"modificar_tension:{antigua}")
    assert respuesta == TENSION_PIDE_VALORES

    responder(con, cfg, "140 90 75")
    respuesta = responder(con, cfg, "no")
    tomas = {toma.id: toma for toma in db.listar_tensiones(con, limite=20)}
    con.close()

    assert "Toma de tensión modificada:" in respuesta
    assert (tomas[antigua].alta, tomas[antigua].baja) == (140, 90)
    assert tomas[antigua].fecha_hora == datetime(2026, 11, 1, 9, 0)


def test_boton_de_una_cita_que_ya_no_existe_avisa(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder_callback(con, cfg, "borrar_cita:99")
    con.close()

    assert respuesta == "Ese botón ya no vale. Escribe /ayuda para ver lo que sé hacer."


def test_historial_numera_las_tomas_y_muestra_nota_solo_si_la_tiene(cfg):
    con = guardar_tensiones_de_ejemplo(cfg)
    respuesta = responder(con, cfg, "historial")
    con.close()

    lineas = respuesta.splitlines()
    assert lineas[0] == "Estas son tus últimas tomas de tensión:"
    assert lineas[1].startswith("1. ")
    assert "130 de alta, 85 de baja, pulso 72" in lineas[1]
    assert "Nota: después de cenar" in lineas[1]
    assert lineas[2].startswith("2. ")
    assert "120 de alta, 80 de baja" in lineas[2]
    assert "Nota:" not in lineas[2]
    assert len(respuesta.mensajes) == 3
    assert respuesta.mensajes[0] == HISTORIAL_CABECERA
    assert respuesta.mensajes[1].botones == [
        [
            {"text": "Modificar", "callback_data": "modificar_tension:2"},
            {"text": "Borrar", "callback_data": "borrar_tension:2"},
        ]
    ]
    assert respuesta.mensajes[2].botones == [
        [
            {"text": "Modificar", "callback_data": "modificar_tension:1"},
            {"text": "Borrar", "callback_data": "borrar_tension:1"},
        ]
    ]


def test_ayuda_tiene_una_linea_por_comando(cfg):
    con = db.conectar(cfg.ruta_bd)
    respuesta = responder(con, cfg, "/ayuda")
    con.close()

    assert respuesta == AYUDA
    lineas = respuesta.splitlines()
    assert len(lineas) == 6
    assert lineas[0] == "Puedo hacer estas cosas:"
    assert lineas[1] == "1. añadir: apuntar una cita nueva."
    assert lineas[2] == "2. citas: ver tus citas y sus botones."
    assert lineas[3] == (
        "3. tension 130 85 72: apuntar una toma de tensión. "
        "Puedes añadir la fecha y la hora al final."
    )
    assert lineas[4] == "4. historial: ver tus tomas de tensión y sus botones."
    assert lineas[5] == "5. ayuda: volver a ver esta ayuda."
    assert "cambiar" not in respuesta
    assert "borrar" not in respuesta


def test_ordenes_sin_barra_funcionan_igual(cfg):
    """Las órdenes sin barra inicial funcionan igual que con barra."""
    con = db.conectar(cfg.ruta_bd)

    # ayuda
    r1 = responder(con, cfg, "ayuda")
    r2 = responder(con, cfg, "/ayuda")
    assert r1 == r2 == AYUDA

    # citas
    r1 = responder(con, cfg, "citas")
    r2 = responder(con, cfg, "/citas")
    assert r1 == r2 == "No tienes citas apuntadas."

    # proximas (deprecated)
    r1 = responder(con, cfg, "proximas")
    r2 = responder(con, cfg, "/proximas")
    assert r1 == r2 == "Ahora se llama citas"

    # tension CON argumentos funciona igual
    r1 = responder(con, cfg, "tension 130 85 72")
    r2 = responder(con, cfg, "/tension 130 85 72")
    assert r1 == r2
    assert "Apuntado: 130 de alta, 85 de baja, pulso 72" in r1

    # tension SIN argumentos: con barra da error de uso, sin barra va a lenguaje natural
    r_con_barra = responder(con, cfg, "/tension")
    assert "Para apuntar la tensión escribe:" in r_con_barra
    r_sin_barra = responder(con, cfg, "tension")
    assert r_sin_barra == IA_NO_ACTIVADA

    con.close()


def test_historial_sin_barra_funciona_igual(cfg):
    """La orden historial sin barra funciona igual que con barra."""
    # BD limpia para este test
    con = db.conectar(cfg.ruta_bd)

    # historial sin datos
    r1 = responder(con, cfg, "historial")
    r2 = responder(con, cfg, "/historial")
    assert r1 == r2 == SIN_TENSION

    # añadir una tensión
    responder(con, cfg, "tension 130 85 72")
    responder(con, cfg, "tension 120 80")

    # historial con datos
    r1 = responder(con, cfg, "historial")
    r2 = responder(con, cfg, "/historial")
    assert r1 == r2
    assert "130 de alta, 85 de baja, pulso 72" in r1
    assert "120 de alta, 80 de baja" in r1

    con.close()


def test_ordenes_sin_barra_con_argumentos(cfg):
    """Órdenes con argumentos funcionan sin barra."""
    con = db.conectar(cfg.ruta_bd)

    # añadir
    r1 = responder(con, cfg, "añadir Analítica | 12/11/2026 8:30 | Centro de salud")
    r2 = responder(con, cfg, "/añadir Analítica | 12/11/2026 8:30 | Centro de salud")
    assert r1 == r2
    assert "He entendido esta cita:" in r1

    con.close()


def test_frase_que_empezando_por_orden_no_es_orden(cfg):
    """Una frase natural que empieza con una palabra de orden no se trata como orden."""
    con = db.conectar(cfg.ruta_bd)

    # "citas medicas" no es la orden "citas" (citas es orden simple sin argumentos)
    respuesta = responder(con, cfg, "citas medicas")
    assert respuesta == IA_NO_ACTIVADA

    # "ayuda por favor" no es la orden "ayuda" (ayuda es orden simple sin argumentos)
    respuesta = responder(con, cfg, "ayuda por favor")
    assert respuesta == IA_NO_ACTIVADA

    # "tension arterial" SÍ se trata como orden "tension" porque tension requiere argumentos
    # y "arterial" se interpreta como argumento (aunque sea inválido, da error de uso)
    respuesta = responder(con, cfg, "tension arterial")
    assert "Para apuntar la tensión escribe:" in respuesta

    # En cambio, con barra SIEMPRE se trata como orden (compatibilidad)
    respuesta_con_barra = responder(con, cfg, "/tension arterial")
    assert "Para apuntar la tensión escribe:" in respuesta_con_barra

    con.close()


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
