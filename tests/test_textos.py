from datetime import date, datetime, time

import pytest

from acompanante.textos import (
    cuando,
    dias_texto,
    fecha_larga,
    hora_texto,
    parsear_dias,
    parsear_fecha,
    parsear_fecha_hora,
    parsear_hora,
)


def test_fecha_larga_en_espanol():
    assert fecha_larga(date(2026, 11, 12)) == "jueves 12 de noviembre"


def test_hora_sin_cero_delante():
    assert hora_texto(time(8, 30)) == "8:30"
    assert hora_texto(datetime(2026, 1, 1, 17, 5)) == "17:05"


def test_cuando_relativo():
    hoy = date(2026, 11, 10)
    assert cuando(date(2026, 11, 10), hoy) == "hoy"
    assert cuando(date(2026, 11, 11), hoy) == "mañana"
    assert cuando(date(2026, 11, 12), hoy) == "pasado mañana"
    assert cuando(date(2026, 11, 15), hoy) == "dentro de 5 días"


@pytest.mark.parametrize("texto", ["12/11/2026", "12-11-2026", "2026-11-12"])
def test_parsear_fecha_formatos(texto):
    assert parsear_fecha(texto) == date(2026, 11, 12)


def test_parsear_fecha_mal_escrita_explica_como():
    with pytest.raises(ValueError, match="12/11/2026"):
        parsear_fecha("el jueves")


def test_parsear_hora_y_fecha_hora():
    assert parsear_hora("8.30") == time(8, 30)
    assert parsear_fecha_hora("12/11/2026 8:30") == datetime(2026, 11, 12, 8, 30)


def test_parsear_varios_dias_y_escribirlos():
    assert parsear_dias("lunes,jueves") == [0, 3]
    assert parsear_dias("jueves, lunes") == [0, 3]
    assert parsear_dias("miercoles") == [2]
    assert dias_texto([0]) == "lunes"
    assert dias_texto([0, 3]) == "lunes y jueves"
    assert dias_texto([0, 2, 4]) == "lunes, miércoles y viernes"


def test_parsear_dia_mal_escrito_explica_como():
    with pytest.raises(ValueError, match="lunes,jueves"):
        parsear_dias("lunes, finde")
