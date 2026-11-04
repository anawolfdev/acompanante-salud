import pytest

from acompanante.config import Config


@pytest.fixture
def cfg(tmp_path):
    return Config(ruta_bd=str(tmp_path / "prueba.db"))
