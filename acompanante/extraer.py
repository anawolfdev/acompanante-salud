"""Convierte una frase normal en los datos de una cita.

La IA solo propone los datos. La aplicación comprueba que la fecha y la hora
se entienden y no se inventa nada si faltan.
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from acompanante.config import Config, cargar_env, leer_config
from acompanante.ia import crear_cliente_ia
from acompanante.modelos import TIPOS
from acompanante.plantillas import preparacion_sugerida
from acompanante.textos import fecha_larga, parsear_fecha, parsear_hora


class ErrorExtraccion(Exception):
    """La IA no ha devuelto algo que se pueda entender."""


SISTEMA = (
    "Eres un ayudante que apunta citas médicas en español. "
    "Devuelve SOLO un objeto JSON, sin explicaciones y sin bloques de código. "
    'Las claves son: "titulo", "tipo", "fecha", "hora", "lugar" y "preparacion". '
    '"titulo" es una frase corta con lo que es la cita. '
    '"tipo" es una de estas palabras: cita, analitica, vacuna, prueba, otro. '
    '"fecha" va en formato AAAA-MM-DD. '
    '"hora" va en formato HH:MM, en 24 horas. '
    '"lugar" es el sitio, o una cadena vacía. '
    '"preparacion" es una lista de frases cortas con lo que hay que preparar. '
    'Si la frase no dice el día, la hora o el lugar, deja "" en ese dato. '
    "No inventes datos que no estén en la frase. "
    "No des consejos médicos ni diagnósticos."
)


@dataclass
class PropuestaCita:
    """Lo que la IA ha entendido de la frase, antes de guardarlo."""

    titulo: str
    tipo: str = "cita"
    fecha_hora: datetime | None = None
    lugar: str = ""
    preparacion: list[str] = field(default_factory=list)

    @property
    def faltan_datos(self) -> bool:
        return self.fecha_hora is None


def _sin_tildes(texto: str) -> str:
    return "".join(
        letra for letra in unicodedata.normalize("NFD", texto)
        if unicodedata.category(letra) != "Mn"
    )


def _normalizar_tipo(valor) -> str:
    texto = _sin_tildes(str(valor or "").strip().lower())
    if texto in TIPOS:
        return texto
    if "analitic" in texto:
        return "analitica"
    if "vacun" in texto:
        return "vacuna"
    if "prueba" in texto or "radiograf" in texto or "ecograf" in texto:
        return "prueba"
    if any(palabra in texto for palabra in ("cita", "consulta", "medic", "revision")):
        return "cita"
    return "otro" if texto else "cita"


def _lista_preparacion(valor) -> list[str]:
    if isinstance(valor, str):
        partes = valor.replace(";", "\n").splitlines()
    elif isinstance(valor, (list, tuple)):
        partes = [str(parte) for parte in valor]
    else:
        partes = []
    return [parte.strip() for parte in partes if parte.strip()]


def _json_de_respuesta(respuesta: str) -> dict:
    """Acepta el JSON solo o dentro de un bloque de código."""
    texto = respuesta.strip()
    if texto.startswith("```"):
        lineas = texto.splitlines()
        if lineas and lineas[0].startswith("```"):
            lineas = lineas[1:]
        if lineas and lineas[-1].strip().startswith("```"):
            lineas = lineas[:-1]
        texto = "\n".join(lineas).strip()

    inicio = texto.find("{")
    fin = texto.rfind("}")
    if inicio == -1 or fin == -1 or fin < inicio:
        raise ErrorExtraccion("La IA no ha devuelto un JSON.")
    try:
        datos = json.loads(texto[inicio:fin + 1])
    except json.JSONDecodeError as error:
        raise ErrorExtraccion("La IA no ha devuelto un JSON válido.") from error
    if not isinstance(datos, dict):
        raise ErrorExtraccion("La IA no ha devuelto un JSON válido.")
    return datos


def _texto_peticion(texto: str, ahora: datetime, con_imagen: bool = False) -> str:
    lineas = [f"Hoy es {fecha_larga(ahora)} de {ahora.year}, en hora de Madrid."]
    if con_imagen:
        lineas.append("La persona ha mandado una foto del papel de la cita.")
        lineas.append("Lee en la foto la fecha, la hora, el lugar y lo que hay que preparar.")
        if texto.strip():
            lineas.append(f"Además ha escrito: {texto.strip()}")
    else:
        lineas.append(f"Frase de la persona: {texto}")
    lineas.append("Devuelve el JSON de la cita.")
    return "\n".join(lineas)


def extraer_cita(
    texto: str,
    cfg: Config | None = None,
    ahora: datetime | None = None,
    cliente=None,
    imagen: bytes | None = None,
) -> PropuestaCita:
    """Pide a la IA los datos de la cita y los devuelve ya comprobados.

    'imagen' son los bytes de una foto del papel de la cita, si la hay.
    'cliente' sirve para las pruebas: así no hace falta Internet.
    """
    if cfg is None:
        cargar_env()
        cfg = leer_config()
    if ahora is None:
        ahora = datetime.now(ZoneInfo(cfg.zona_horaria)).replace(second=0, microsecond=0)
    if cliente is None:
        cliente = crear_cliente_ia(cfg)

    respuesta = cliente.preguntar(
        _texto_peticion(texto, ahora, con_imagen=imagen is not None),
        imagen=imagen,
        sistema=SISTEMA,
    )
    datos = _json_de_respuesta(respuesta)

    tipo = _normalizar_tipo(datos.get("tipo"))
    titulo = str(datos.get("titulo") or "").strip() or TIPOS.get(tipo, "Cita")

    fecha_hora = None
    fecha = str(datos.get("fecha") or "").strip()
    hora = str(datos.get("hora") or "").strip()
    if fecha and hora:
        try:
            fecha_hora = datetime.combine(parsear_fecha(fecha), parsear_hora(hora))
        except ValueError:
            fecha_hora = None

    preparacion = _lista_preparacion(datos.get("preparacion"))
    if not preparacion:
        preparacion = preparacion_sugerida(tipo)

    return PropuestaCita(
        titulo=titulo,
        tipo=tipo,
        fecha_hora=fecha_hora,
        lugar=str(datos.get("lugar") or "").strip(),
        preparacion=preparacion,
    )
