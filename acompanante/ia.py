"""Conexión con un modelo de IA gratuito, cambiable desde el .env.

Todos los proveedores de la lista hablan el mismo "idioma" (el formato
compatible con OpenAI), así que cambiar de uno a otro es cambiar
IA_PROVEEDOR, IA_API_KEY e IA_MODELO. No hace falta tocar código.
"""

from __future__ import annotations

import base64
import json
import urllib.request

from acompanante.config import Config

PROVEEDORES = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "ollama": "http://localhost:11434/v1",  # modelo en tu propio ordenador
}


class IANoDisponible(Exception):
    """No hay IA configurada o el proveedor ha fallado."""


class SinIA:
    """Se usa cuando IA_PROVEEDOR=ninguno. La aplicación funciona igual, sin las partes de IA."""

    def preguntar(self, texto: str, imagen: bytes | None = None, tipo_imagen: str = "image/jpeg", sistema: str | None = None) -> str:
        raise IANoDisponible("No hay IA configurada. Pon IA_PROVEEDOR e IA_API_KEY en el archivo .env.")


class ClienteIA:
    def __init__(self, url_base: str, api_key: str, modelo: str, abrir=urllib.request.urlopen) -> None:
        if not modelo:
            raise IANoDisponible("Falta IA_MODELO en el archivo .env.")
        self.url = url_base.rstrip("/") + "/chat/completions"
        self.api_key = api_key
        self.modelo = modelo
        self._abrir = abrir

    def preguntar(self, texto: str, imagen: bytes | None = None, tipo_imagen: str = "image/jpeg", sistema: str | None = None) -> str:
        """Manda una pregunta (y opcionalmente una foto) y devuelve la respuesta en texto."""
        contenido: list[dict] = [{"type": "text", "text": texto}]
        if imagen is not None:
            b64 = base64.b64encode(imagen).decode("ascii")
            contenido.append({"type": "image_url", "image_url": {"url": f"data:{tipo_imagen};base64,{b64}"}})
        mensajes = []
        if sistema:
            mensajes.append({"role": "system", "content": sistema})
        mensajes.append({"role": "user", "content": contenido})
        cuerpo = json.dumps({"model": self.modelo, "messages": mensajes}).encode("utf-8")
        cabeceras = {"Content-Type": "application/json"}
        if self.api_key:
            cabeceras["Authorization"] = f"Bearer {self.api_key}"
        peticion = urllib.request.Request(self.url, data=cuerpo, headers=cabeceras, method="POST")
        try:
            with self._abrir(peticion, timeout=60) as respuesta:
                datos = json.loads(respuesta.read().decode("utf-8"))
            return datos["choices"][0]["message"]["content"]
        except Exception as error:
            raise IANoDisponible(f"El proveedor de IA ha fallado: {error}") from error


def crear_cliente_ia(cfg: Config):
    if cfg.ia_proveedor in ("", "ninguno"):
        return SinIA()
    url = cfg.ia_url_base or PROVEEDORES.get(cfg.ia_proveedor)
    if not url:
        opciones = ", ".join(["ninguno", *PROVEEDORES])
        raise IANoDisponible(f"Proveedor '{cfg.ia_proveedor}' desconocido. Usa uno de estos: {opciones}")
    return ClienteIA(url, cfg.ia_api_key, cfg.ia_modelo)
