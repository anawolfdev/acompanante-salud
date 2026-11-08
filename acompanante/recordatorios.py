"""Decide qué avisos tocan y escribe su texto.

Reglas de la etapa 1:
- Aviso "previo": DIAS_ANTES días antes de la cita, a la HORA_AVISO_PREVIO.
- Aviso "vispera": la noche anterior a la HORA_AVISO_VISPERA, solo si la
  preparación incluye la palabra "ayunas".
- Aviso "dia": el mismo día a la HORA_AVISO_DIA, o una hora antes de la cita
  si la cita es muy temprano (lo que ocurra antes).
- Nunca se avisa de una cita que ya ha pasado.
- Si varios avisos tocan a la vez (por ejemplo, la cita se apuntó tarde),
  solo se manda el más importante: primero el del día, luego el de la víspera
  y por último el previo.
- Las tareas (por ejemplo, tomarse la tensión) avisan el día que toca a su
  hora, una sola vez al día.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Callable

from acompanante import db
from acompanante.config import Config
from acompanante.modelos import TIPOS, Cita, Tarea
from acompanante.textos import DIAS, cuando, fecha_larga, hora_texto, parsear_hora


@dataclass
class Aviso:
    cita: Cita
    tipo: str  # 'previo', 'vispera' o 'dia'
    momento: datetime
    texto: str
    cubre: list[str] = field(default_factory=list)  # tipos que quedan atendidos con este envío


@dataclass
class AvisoTarea:
    tarea: Tarea
    momento: datetime
    texto: str


def necesita_ayunas(cita: Cita) -> bool:
    """Mira si algún paso de preparación menciona el ayuno."""
    return any("ayunas" in paso.lower() for paso in cita.preparacion)


def momentos_de_aviso(cita: Cita, cfg: Config) -> dict[str, datetime]:
    dia_previo = cita.fecha_hora.date() - timedelta(days=cfg.dias_antes)
    previo = datetime.combine(dia_previo, parsear_hora(cfg.hora_aviso_previo))
    momentos = {"previo": previo}
    if necesita_ayunas(cita):
        dia_vispera = cita.fecha_hora.date() - timedelta(days=1)
        momentos["vispera"] = datetime.combine(dia_vispera, parsear_hora(cfg.hora_aviso_vispera))
    mismo_dia = datetime.combine(cita.fecha_hora.date(), parsear_hora(cfg.hora_aviso_dia))
    momentos["dia"] = min(mismo_dia, cita.fecha_hora - timedelta(hours=1))
    return momentos


def texto_aviso(cita: Cita, ahora: datetime, tipo: str = "") -> str:
    """Mensaje claro, sin emojis ni abreviaturas, pensado para lectores de pantalla."""
    if not tipo and necesita_ayunas(cita) and (cita.fecha_hora.date() - ahora.date()).days == 1:
        tipo = "vispera"
    que = cita.titulo or TIPOS[cita.tipo]
    relativo = cuando(cita.fecha_hora.date(), ahora.date())
    lineas = [
        "Recordatorio de salud.",
        f"{relativo.capitalize()}, {fecha_larga(cita.fecha_hora)}, a las "
        f"{hora_texto(cita.fecha_hora)}: {que}.",
    ]
    if tipo == "vispera":
        lineas.append("Desde ahora, no comas nada.")
    if cita.lugar:
        lineas.append(f"Dónde: {cita.lugar}.")
    if cita.preparacion:
        lineas.append("Deja preparado:" if tipo == "vispera" else "Para prepararte:")
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
        if "dia" in tocan:
            tipo = "dia"
        elif "vispera" in tocan:
            tipo = "vispera"
        else:
            tipo = "previo"
        pendientes.append(
            Aviso(
                cita=cita,
                tipo=tipo,
                momento=momentos[tipo],
                texto=texto_aviso(cita, ahora, tipo),
                cubre=tocan,
            )
        )
    return pendientes


def texto_tarea(tarea: Tarea, dia: date) -> str:
    """'Recordatorio: hoy lunes toca tomarte la tensión.'"""
    titulo = tarea.titulo.strip()
    titulo = titulo[0].lower() + titulo[1:]
    return f"Recordatorio: hoy {DIAS[dia.weekday()]} toca {titulo}."


def tareas_pendientes(
    tareas: list[Tarea],
    ahora: datetime,
    ya_enviado: Callable[[int, date], bool],
) -> list[AvisoTarea]:
    """Tareas que tocan ahora y que todavía no se han avisado hoy."""
    pendientes: list[AvisoTarea] = []
    for tarea in tareas:
        if not tarea.activa or ahora.weekday() not in tarea.dias:
            continue
        momento = datetime.combine(ahora.date(), tarea.hora)
        if momento > ahora or ya_enviado(tarea.id, ahora.date()):
            continue
        pendientes.append(
            AvisoTarea(
                tarea=tarea,
                momento=momento,
                texto=texto_tarea(tarea, ahora.date()),
            )
        )
    return pendientes


def enviar_avisos(
    con: sqlite3.Connection, notificador, ahora: datetime, cfg: Config, simular: bool = False
) -> list[Aviso | AvisoTarea]:
    """Manda los avisos que tocan y los apunta para no repetirlos.

    Con simular=True solo los devuelve, sin mandar ni apuntar nada.
    """
    citas = db.listar_citas(con, desde=ahora)
    avisos = avisos_pendientes(citas, ahora, cfg, lambda cid, t: db.aviso_enviado(con, cid, t))
    tareas = db.listar_tareas(con, solo_activas=True)
    avisos += tareas_pendientes(
        tareas, ahora, lambda tid, fecha: db.aviso_tarea_enviado(con, tid, fecha)
    )
    if simular:
        return avisos
    for aviso in avisos:
        notificador.enviar(aviso.texto)
        if isinstance(aviso, AvisoTarea):
            db.marcar_aviso_tarea_enviado(con, aviso.tarea.id, ahora.date(), ahora)
        else:
            for tipo in aviso.cubre:
                db.marcar_aviso_enviado(con, aviso.cita.id, tipo, ahora)
    return avisos
