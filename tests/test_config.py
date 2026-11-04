from acompanante.config import leer_config


def test_minutos_entre_revisiones_por_defecto():
    assert leer_config({}).minutos_entre_revisiones == 5


def test_minutos_entre_revisiones_desde_el_entorno():
    assert leer_config({"MINUTOS_ENTRE_REVISIONES": "2"}).minutos_entre_revisiones == 2
