from acompanante.config import leer_config


def test_minutos_entre_revisiones_por_defecto():
    assert leer_config({}).minutos_entre_revisiones == 5


def test_minutos_entre_revisiones_desde_el_entorno():
    assert leer_config({"MINUTOS_ENTRE_REVISIONES": "2"}).minutos_entre_revisiones == 2


def test_hora_aviso_vispera_por_defecto():
    assert leer_config({}).hora_aviso_vispera == "21:00"


def test_hora_aviso_vispera_desde_el_entorno():
    assert leer_config({"HORA_AVISO_VISPERA": "20:30"}).hora_aviso_vispera == "20:30"
