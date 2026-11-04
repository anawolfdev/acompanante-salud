"""Fechas y horas en español de España, escritas para leerse en voz alta."""

from __future__ import annotations

from datetime import date, datetime, time

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def fecha_larga(d: date | datetime) -> str:
    """'jueves 12 de noviembre'."""
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]}"


def hora_texto(t: datetime | time) -> str:
    """'8:30' (sin cero delante, como se dice)."""
    return f"{t.hour}:{t.minute:02d}"


def cuando(dia_cita: date, hoy: date) -> str:
    """'hoy', 'mañana', 'pasado mañana' o 'dentro de 5 días'."""
    diferencia = (dia_cita - hoy).days
    if diferencia == 0:
        return "hoy"
    if diferencia == 1:
        return "mañana"
    if diferencia == 2:
        return "pasado mañana"
    if diferencia > 2:
        return f"dentro de {diferencia} días"
    return "ya pasó"


def parsear_fecha(texto: str) -> date:
    """Acepta '12/11/2026', '12-11-2026' o '2026-11-12'."""
    texto = texto.strip()
    for formato in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            pass
    raise ValueError(f"No entiendo la fecha '{texto}'. Escríbela así: 12/11/2026")


def parsear_hora(texto: str) -> time:
    """Acepta '8:30', '08:30' o '8.30'."""
    texto = texto.strip().replace(".", ":")
    try:
        return datetime.strptime(texto, "%H:%M").time()
    except ValueError:
        raise ValueError(f"No entiendo la hora '{texto}'. Escríbela así: 8:30") from None


def parsear_fecha_hora(texto: str) -> datetime:
    """Acepta '12/11/2026 8:30' o '2026-11-12 08:30'."""
    partes = texto.strip().split()
    if len(partes) != 2:
        raise ValueError(f"No entiendo '{texto}'. Escríbelo así: 12/11/2026 8:30")
    return datetime.combine(parsear_fecha(partes[0]), parsear_hora(partes[1]))
