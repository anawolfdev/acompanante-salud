import io
import json

import pytest

from acompanante.config import Config
from acompanante.ia import PROVEEDORES, ClienteIA, IANoDisponible, SinIA, crear_cliente_ia


class RespuestaFalsa(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_sin_ia_por_defecto():
    cliente = crear_cliente_ia(Config())
    assert isinstance(cliente, SinIA)
    with pytest.raises(IANoDisponible):
        cliente.preguntar("hola")


def test_proveedor_gemini_usa_su_direccion():
    cliente = crear_cliente_ia(Config(ia_proveedor="gemini", ia_api_key="k", ia_modelo="m"))
    assert cliente.url == PROVEEDORES["gemini"] + "/chat/completions"


def test_proveedor_desconocido():
    with pytest.raises(IANoDisponible, match="desconocido"):
        crear_cliente_ia(Config(ia_proveedor="inventado", ia_modelo="m"))


def test_pregunta_con_foto_manda_imagen_y_clave():
    enviadas = []

    def abrir(peticion, timeout=None):
        enviadas.append(peticion)
        return RespuestaFalsa(json.dumps({"choices": [{"message": {"content": "vale"}}]}).encode())

    cliente = ClienteIA("https://ejemplo.test/v1", "CLAVE", "modelo-x", abrir=abrir)
    assert cliente.preguntar("¿Qué fecha pone?", imagen=b"\xff\xd8foto") == "vale"
    p = enviadas[0]
    assert p.full_url == "https://ejemplo.test/v1/chat/completions"
    assert p.get_header("Authorization") == "Bearer CLAVE"
    cuerpo = json.loads(p.data)
    partes = cuerpo["messages"][0]["content"]
    assert partes[0]["text"] == "¿Qué fecha pone?"
    assert partes[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
