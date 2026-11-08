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


@dataclass
class Tension:
    """Una toma de tensión. Solo se guarda y se enseña; no se interpreta."""

    fecha_hora: datetime  # hora local de Madrid, sin zona (naive)
    alta: int
    baja: int
    pulso: int | None = None
    nota: str = ""
    id: int | None = None

    def __post_init__(self) -> None:
        for nombre, valor in (("alta", self.alta), ("baja", self.baja)):
            if not isinstance(valor, int) or isinstance(valor, bool):
                raise ValueError(f"La tensión de {nombre} tiene que ser un número entero")
            if valor <= 0:
                raise ValueError(f"La tensión de {nombre} tiene que ser mayor que cero")
        if self.pulso is not None:
            if not isinstance(self.pulso, int) or isinstance(self.pulso, bool):
                raise ValueError("El pulso tiene que ser un número entero")
            if self.pulso <= 0:
                raise ValueError("El pulso tiene que ser mayor que cero")
        if self.alta < self.baja:
            raise ValueError(
                "La tensión de alta no puede ser menor que la de baja. Revisa los números"
            )
