"""Lee la configuración del archivo .env y de las variables de entorno."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def cargar_env(ruta: str | Path = ".env") -> dict[str, str]:
    """Lee un archivo .env sencillo (CLAVE=valor). Las líneas con # se ignoran.

    No sobrescribe variables que ya existan en el entorno.
    """
    valores: dict[str, str] = {}
    ruta = Path(ruta)
    if not ruta.exists():
        return valores
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        valor = valor.strip().strip('"').strip("'")
        valores[clave.strip()] = valor
    for clave, valor in valores.items():
        os.environ.setdefault(clave, valor)
    return valores


@dataclass
class Config:
    ruta_bd: str = "datos/salud.db"
    zona_horaria: str = "Europe/Madrid"
    dias_antes: int = 2
    hora_aviso_previo: str = "10:00"
    hora_aviso_dia: str = "07:30"
    minutos_entre_revisiones: int = 5
    canal: str = "consola"
    telegram_token: str = ""
    telegram_chat_id: str = ""
    ia_proveedor: str = "ninguno"
    ia_api_key: str = ""
    ia_modelo: str = ""
    ia_url_base: str = ""


def leer_config(entorno: dict[str, str] | None = None) -> Config:
    """Crea la configuración a partir del entorno (o de un diccionario, en las pruebas)."""
    e = os.environ if entorno is None else entorno
    return Config(
        ruta_bd=e.get("RUTA_BD", "datos/salud.db"),
        zona_horaria=e.get("ZONA_HORARIA", "Europe/Madrid"),
        dias_antes=int(e.get("DIAS_ANTES", "2")),
        hora_aviso_previo=e.get("HORA_AVISO_PREVIO", "10:00"),
        hora_aviso_dia=e.get("HORA_AVISO_DIA", "07:30"),
        minutos_entre_revisiones=int(e.get("MINUTOS_ENTRE_REVISIONES", "5")),
        canal=e.get("CANAL", "consola").lower(),
        telegram_token=e.get("TELEGRAM_TOKEN", ""),
        telegram_chat_id=e.get("TELEGRAM_CHAT_ID", ""),
        ia_proveedor=e.get("IA_PROVEEDOR", "ninguno").lower(),
        ia_api_key=e.get("IA_API_KEY", ""),
        ia_modelo=e.get("IA_MODELO", ""),
        ia_url_base=e.get("IA_URL_BASE", ""),
    )
