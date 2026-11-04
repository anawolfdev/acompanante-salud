"""Los datos con los que trabaja la aplicación."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

# Tipos de cita y cómo se nombran en los mensajes.
TIPOS = {
    "cita": "cita médica",
    "analitica": "analítica",
    "vacuna": "vacuna",
    "prueba": "prueba médica",
    "otro": "cita",
}


@dataclass
class Cita:
    titulo: str
    fecha_hora: datetime  # hora local de Madrid, sin zona (naive)
    tipo: str = "cita"
    lugar: str = ""
    preparacion: list[str] = field(default_factory=list)
    notas: str = ""
    id: int | None = None

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS:
            opciones = ", ".join(TIPOS)
            raise ValueError(f"Tipo '{self.tipo}' no válido. Usa uno de estos: {opciones}")
        if not self.titulo.strip():
            raise ValueError("La cita necesita un título, por ejemplo: Analítica de sangre")
