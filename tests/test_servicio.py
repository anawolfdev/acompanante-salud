"""Comprueba que la plantilla del servicio y los scripts de instalación están bien.

Estas pruebas no instalan nada ni llaman a launchctl: solo leen los archivos.
"""

import plistlib
import shutil
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLA = RAIZ / "deploy" / "com.anawolfdev.acompanante.plist"
INSTALAR = RAIZ / "scripts" / "instalar-servicio.sh"
QUITAR = RAIZ / "scripts" / "quitar-servicio.sh"


def leer_plantilla():
    with open(PLANTILLA, "rb") as archivo:
        return plistlib.load(archivo)


def test_la_plantilla_existe_y_se_puede_leer():
    assert PLANTILLA.is_file()
    assert leer_plantilla()["Label"] == "com.anawolfdev.acompanante"


def test_la_plantilla_arranca_sola_y_se_levanta_si_se_para():
    datos = leer_plantilla()
    assert datos["RunAtLoad"] is True
    assert datos["KeepAlive"] is True


def test_la_plantilla_arranca_la_orden_vigilar():
    datos = leer_plantilla()
    programa = datos["ProgramArguments"]
    assert programa[1:] == ["-m", "acompanante", "vigilar"]


def test_la_plantilla_usa_rutas_absolutas():
    datos = leer_plantilla()
    assert Path(datos["ProgramArguments"][0]).is_absolute()
    assert Path(datos["WorkingDirectory"]).is_absolute()
    assert Path(datos["StandardOutPath"]).is_absolute()
    assert Path(datos["StandardErrorPath"]).is_absolute()


def test_la_carpeta_de_trabajo_es_la_del_proyecto():
    # Se compara solo el nombre de la carpeta: en GitHub el proyecto está
    # en otra ruta y la plantilla lleva la de este Mac.
    datos = leer_plantilla()
    assert Path(datos["WorkingDirectory"]).name == RAIZ.name


def test_los_logs_van_a_la_carpeta_de_logs_del_mac():
    datos = leer_plantilla()
    salida = Path(datos["StandardOutPath"])
    error = Path(datos["StandardErrorPath"])
    assert salida.parent.parts[-2:] == ("Library", "Logs")
    assert error.parent.parts[-2:] == ("Library", "Logs")
    assert salida.name == "acompanante.log"
    assert error.name == "acompanante-error.log"
    assert salida != error


def test_los_scripts_existen_y_se_pueden_ejecutar():
    for script in (INSTALAR, QUITAR):
        assert script.is_file()
        assert script.stat().st_mode & 0o111, f"{script.name} no tiene permiso de ejecución"


def test_los_scripts_de_arranque_no_tienen_errores_de_sintaxis():
    bash = shutil.which("bash")
    if bash is None:
        return
    for script in (INSTALAR, QUITAR):
        resultado = subprocess.run([bash, "-n", str(script)], capture_output=True, text=True)
        assert resultado.returncode == 0, resultado.stderr


def test_el_script_de_quitar_usa_la_misma_etiqueta():
    assert "com.anawolfdev.acompanante" in QUITAR.read_text(encoding="utf-8")
