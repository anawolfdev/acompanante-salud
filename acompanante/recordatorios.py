"""Decide qué avisos tocan y escribe su texto.

Reglas de la etapa 1:
- Aviso "previo": DIAS_ANTES días antes de la cita, a la HORA_AVISO_PREVIO.
- Aviso "dia": el mismo día a la HORA_AVISO_DIA, o una hora antes de la cita
  si la cita es muy temprano (lo que ocurra antes).
- Nunca se avisa de una cita que ya ha pasado.
- Si los dos avisos tocan a la vez (por ejemplo, la cita se apuntó tarde),
  solo se manda el del día.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable

from acompanante import db
from acompanante.config import Config
from acompanante.modelos import TIPOS, Cita
from acompanante.textos import cuando, fecha_larga, hora_texto, parsear_hora


@dataclass
class Aviso:
    cita: Cita
    tipo: str  # 'previo' o 'dia'
    momento: datetime
    texto: str
    cubre: list[str] = field(default_factory=list)  # tipos que quedan atendidos con este envío


def momentos_de_aviso(cita: Cita, cfg: Config) -> dict[str, datetime]:
    dia_previo = cita.fecha_hora.date() - timedelta(days=cfg.dias_antes)
    previo = datetime.combine(dia_previo, parsear_hora(cfg.hora_aviso_previo))
    mismo_dia = datetime.combine(cita.fecha_hora.date(), parsear_hora(cfg.hora_aviso_dia))
    dia = min(mismo_dia, cita.fecha_hora - timedelta(hours=1))
    return {"previo": previo, "dia": dia}


def texto_aviso(cita: Cita, ahora: datetime) -> str:
    """Mensaje claro, sin emojis ni abreviaturas, pensado para lectores de pantalla."""
    que = cita.titulo or TIPOS[cita.tipo]
    relativo = cuando(cita.fecha_hora.date(), ahora.date())
    lineas = [
        "Recordatorio de salud.",
        f"{relativo.capitalize()}, {fecha_larga(cita.fecha_hora)}, a las "
        f"{hora_texto(cita.fecha_hora)}: {que}.",
    ]
    if cita.lugar:
        lineas.append(f"Dónde: {cita.lugar}.")
    if cita.preparacion:
        lineas.append("Para prepararte:")
        for numero, paso in enumerate(cita.preparacion, start=1):
            paso = paso.strip().rstrip(".")
            lineas.append(f"{numero}. {paso}.")
    else:
        lineas.append("No hay nada apuntado que preparar. Lleva tu tarjeta sanitaria.")
    if cita.notas:
        lineas.append(f"Nota: {cita.notas.strip()}")
    return "\n".join(lineas)


def avisos_pendientes(
    citas: list[Cita],
    ahora: datetime,
    cfg: Config,
    ya_enviado: Callable[[int, str], bool],
) -> list[Aviso]:
    """Lista de avisos que hay que mandar ahora mismo."""
    pendientes: list[Aviso] = []
    for cita in citas:
        if cita.fecha_hora <= ahora:
            continue
        momentos = momentos_de_aviso(cita, cfg)
        tocan = [
            tipo
            for tipo, momento in momentos.items()
            if momento <= ahora and not ya_enviado(cita.id, tipo)
        ]
        if not tocan:
            continue
        tipo = "dia" if "dia" in tocan else "previo"
        pendientes.append(
            Aviso(cita=cita, tipo=tipo, momento=momentos[tipo], texto=texto_aviso(cita, ahora), cubre=tocan)
        )
    return pendientes


def enviar_avisos(con: sqlite3.Connection, notificador, ahora: datetime, cfg: Config, simular: bool = False) -> list[Aviso]:
    """Manda los avisos que tocan y los apunta para no repetirlos.

    Con simular=True solo los devuelve, sin mandar ni apuntar nada.
    """
    citas = db.listar_citas(con, desde=ahora)
    avisos = avisos_pendientes(citas, ahora, cfg, lambda cid, t: db.aviso_enviado(con, cid, t))
    if simular:
        return avisos
    for aviso in avisos:
        notificador.enviar(aviso.texto)
        for tipo in aviso.cubre:
            db.marcar_aviso_enviado(con, aviso.cita.id, tipo, ahora)
    return avisos
