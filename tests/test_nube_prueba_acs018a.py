import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
NUBE = RAIZ / "nube-prueba"


def leer_jsonc(ruta):
    texto = ruta.read_text(encoding="utf-8")
    sin_comentarios = re.sub(r"^\s*//.*$", "", texto, flags=re.MULTILINE)
    return json.loads(sin_comentarios)


def test_esquema_idempotente_sin_duplicar_citas():
    esquema = (NUBE / "schema.sql").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        ruta = Path(tmp) / "prueba.db"
        conexion = sqlite3.connect(ruta)
        try:
            conexion.executescript(esquema)
            conexion.executescript(esquema)
            filas = conexion.execute(
                "SELECT id, titulo, fecha_hora, lugar FROM citas_prueba ORDER BY id"
            ).fetchall()
        finally:
            conexion.close()

    assert filas == [
        (1, "Cita de prueba con la doctora Ejemplo", "2026-11-20 10:00", "Hospital Inventado"),
        (2, "Revisión de mentira", "2026-11-25 17:30", "Centro de Salud Ficticio"),
    ]


def test_configuracion_sin_activadores_cron():
    configuracion = leer_jsonc(NUBE / "wrangler.jsonc")
    assert "triggers" not in configuracion
    assert "crons" not in json.dumps(configuracion, ensure_ascii=False)


def test_worker_simulado_envio_limite_y_fallo():
    script = RAIZ / "tests" / "_prueba_worker_acs018a.mjs"
    resultado = subprocess.run(
        ["node", str(script)],
        cwd=RAIZ,
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, (
        "La prueba del Worker en Node ha fallado.\n"
        f"STDOUT:\n{resultado.stdout}\nSTDERR:\n{resultado.stderr}"
    )
    assert "OK envio_antes_del_limite" in resultado.stdout
    assert "OK ningun_envio_despues_del_limite" in resultado.stdout
    assert "OK telegram_falla_consumiendo_intento" in resultado.stdout
