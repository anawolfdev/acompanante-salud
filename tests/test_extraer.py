import json
from datetime import datetime

import pytest

from acompanante.config import Config
from acompanante.extraer import ErrorExtraccion, extraer_cita


class IAFalsa:
    def __init__(self, respuesta):
        self.respuesta = respuesta
        self.preguntas = []

    def preguntar(self, texto, imagen=None, tipo_imagen="image/jpeg", sistema=None):
        self.preguntas.append((texto, sistema))
        return self.respuesta


def test_extrae_la_frase_de_ejemplo():
    ia = IAFalsa(
        json.dumps(
            {
                "titulo": "Analítica de sangre",
                "tipo": "analitica",
                "fecha": "2026-11-12",
                "hora": "08:30",
                "lugar": "Centro de salud",
                "preparacion": ["Ve en ayunas"],
            }
        )
    )

    propuesta = extraer_cita(
        "analítica el 12 de noviembre a las 8:30 en el centro de salud, en ayunas",
        Config(),
        ahora=datetime(2026, 11, 11, 10, 0),
        cliente=ia,
    )

    assert propuesta.titulo == "Analítica de sangre"
    assert propuesta.tipo == "analitica"
    assert propuesta.fecha_hora == datetime(2026, 11, 12, 8, 30)
    assert propuesta.lugar == "Centro de salud"
    assert propuesta.preparacion == ["Ve en ayunas"]
    assert propuesta.faltan_datos is False

    pregunta, sistema = ia.preguntas[0]
    assert "analítica el 12 de noviembre a las 8:30" in pregunta
    assert "miércoles 11 de noviembre de 2026" in pregunta
    assert "JSON" in sistema


def test_entiende_json_dentro_de_un_bloque_de_codigo():
    ia = IAFalsa(
        '```json\n{"titulo": "Vacuna de la gripe", "tipo": "vacuna", '
        '"fecha": "2026-11-20", "hora": "11:00", "lugar": "", "preparacion": []}\n```'
    )

    propuesta = extraer_cita("vacuna el 20 de noviembre a las 11:00", Config(), cliente=ia)

    assert propuesta.titulo == "Vacuna de la gripe"
    assert propuesta.tipo == "vacuna"
    assert propuesta.fecha_hora == datetime(2026, 11, 20, 11, 0)


def test_sin_fecha_no_se_inventa():
    ia = IAFalsa(
        json.dumps(
            {
                "titulo": "Analítica de sangre",
                "tipo": "analitica",
                "fecha": "",
                "hora": "08:30",
                "lugar": "Centro de salud",
                "preparacion": [],
            }
        )
    )

    propuesta = extraer_cita("analítica a las 8:30", Config(), cliente=ia)

    assert propuesta.fecha_hora is None
    assert propuesta.faltan_datos is True


def test_tipo_raro_se_guarda_como_otro():
    ia = IAFalsa(
        json.dumps(
            {
                "titulo": "Revisión",
                "tipo": "dentista",
                "fecha": "2026-11-20",
                "hora": "11:00",
                "lugar": "",
                "preparacion": [],
            }
        )
    )

    propuesta = extraer_cita("revisión el 20 de noviembre a las 11:00", Config(), cliente=ia)

    assert propuesta.tipo == "otro"


def test_preparacion_vacia_usa_la_sugerida_del_tipo():
    ia = IAFalsa(
        json.dumps(
            {
                "titulo": "Vacuna de la gripe",
                "tipo": "vacuna",
                "fecha": "2026-11-20",
                "hora": "11:00",
                "lugar": "",
                "preparacion": [],
            }
        )
    )

    propuesta = extraer_cita("vacuna el 20 de noviembre a las 11:00", Config(), cliente=ia)

    assert "Lleva la tarjeta sanitaria" in propuesta.preparacion


def test_si_la_ia_no_devuelve_json_avisa():
    ia = IAFalsa("No sé qué cita es.")

    with pytest.raises(ErrorExtraccion):
        extraer_cita("analítica el 12 de noviembre", Config(), cliente=ia)
