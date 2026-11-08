"""Los datos con los que trabaja la aplicación."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time

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


@dataclass
class Tarea:
    """Algo que se repite cada semana, como tomarse la tensión."""

    titulo: str
    dias: list[int]  # 0 es lunes y 6 es domingo
    hora: time
    activa: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.titulo.strip():
            raise ValueError("La tarea necesita un título, por ejemplo: Tomarte la tensión")
        if not self.dias:
            raise ValueError("La tarea necesita al menos un día, por ejemplo: lunes")
        if any(dia < 0 or dia > 6 for dia in self.dias):
            raise ValueError("Los días de la tarea no son válidos. Usa lunes, martes...")
