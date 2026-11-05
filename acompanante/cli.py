"""Órdenes de terminal: python -m acompanante <orden>."""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from acompanante import db
from acompanante.config import Config, cargar_env, leer_config
from acompanante.modelos import TIPOS, Cita
from acompanante.notificador import (
    ErrorDeEnvio,
    NotificadorConsola,
    NotificadorTelegram,
    consultar_chats,
    crear_notificador,
)
from acompanante.plantillas import preparacion_sugerida
from acompanante.recordatorios import enviar_avisos, momentos_de_aviso, texto_aviso
from acompanante.textos import fecha_larga, hora_texto, parsear_fecha, parsear_fecha_hora, parsear_hora


def ahora_local(cfg: Config) -> datetime:
    return datetime.now(ZoneInfo(cfg.zona_horaria)).replace(tzinfo=None, second=0, microsecond=0)


def _linea_cita(cita: Cita) -> str:
    texto = f"[{cita.id}] {fecha_larga(cita.fecha_hora)} a las {hora_texto(cita.fecha_hora)}: {cita.titulo}"
    if cita.lugar:
        texto += f" ({cita.lugar})"
    return texto


def orden_iniciar(args, cfg: Config) -> int:
    db.conectar(cfg.ruta_bd).close()
    print(f"Base de datos lista en {cfg.ruta_bd}")
    return 0


def orden_nueva_cita(args, cfg: Config) -> int:
    preparacion = args.preparar
    if not preparacion:
        preparacion = [] if args.sin_sugerencias else preparacion_sugerida(args.tipo)
    cita = Cita(
        titulo=args.titulo,
        fecha_hora=datetime.combine(parsear_fecha(args.fecha), parsear_hora(args.hora)),
        tipo=args.tipo,
        lugar=args.lugar or "",
        preparacion=preparacion,
        notas=args.notas or "",
    )
    con = db.conectar(cfg.ruta_bd)
    db.guardar_cita(con, cita)
    print("Cita guardada:")
    print(_linea_cita(cita))
    return 0


def orden_borrar_cita(args, cfg: Config) -> int:
    con = db.conectar(cfg.ruta_bd)
    cita = db.obtener_cita(con, args.id)
    print("Vas a borrar esta cita:")
    print(_linea_cita(cita))
    print("¿Seguro que quieres borrar esta cita? (s/n)")
    respuesta = input()
    if respuesta.strip().lower() not in ("s", "si", "sí"):
        print("No se ha borrado nada.")
        return 0
    db.borrar_cita(con, cita.id)
    print("Cita borrada.")
    return 0


def orden_cambiar_cita(args, cfg: Config) -> int:
    con = db.conectar(cfg.ruta_bd)
    cita = db.obtener_cita(con, args.id)

    hay_cambios = any(
        valor is not None
        for valor in (args.titulo, args.fecha, args.hora, args.tipo, args.lugar, args.preparar, args.notas)
    )
    if not hay_cambios:
        print("No has indicado ningún cambio.")
        return 0

    fecha_hora = cita.fecha_hora
    if args.fecha is not None or args.hora is not None:
        fecha = parsear_fecha(args.fecha) if args.fecha is not None else cita.fecha_hora.date()
        hora = parsear_hora(args.hora) if args.hora is not None else cita.fecha_hora.time()
        fecha_hora = datetime.combine(fecha, hora)

    nueva = Cita(
        titulo=args.titulo if args.titulo is not None else cita.titulo,
        fecha_hora=fecha_hora,
        tipo=args.tipo if args.tipo is not None else cita.tipo,
        lugar=args.lugar if args.lugar is not None else cita.lugar,
        preparacion=args.preparar if args.preparar is not None else cita.preparacion,
        notas=args.notas if args.notas is not None else cita.notas,
        id=cita.id,
    )
    if nueva.fecha_hora != cita.fecha_hora:
        db.borrar_avisos_de_cita(con, cita.id)
    db.actualizar_cita(con, nueva)
    print("Cita cambiada:")
    print(_linea_cita(nueva))
    return 0


def orden_citas(args, cfg: Config) -> int:
    con = db.conectar(cfg.ruta_bd)
    desde = None if args.todas else ahora_local(cfg)
    citas = db.listar_citas(con, desde=desde)
    if not citas:
        print("No tienes citas apuntadas.")
        return 0
    print(f"Tienes {len(citas)} cita(s):")
    for cita in citas:
        print(_linea_cita(cita))
    return 0


def orden_avisos(args, cfg: Config) -> int:
    ahora = parsear_fecha_hora(args.ahora) if args.ahora else ahora_local(cfg)
    con = db.conectar(cfg.ruta_bd)
    notificador = NotificadorConsola() if args.simular else crear_notificador(cfg)
    avisos = enviar_avisos(con, notificador, ahora, cfg, simular=args.simular)
    if args.simular:
        for aviso in avisos:
            NotificadorConsola().enviar(aviso.texto)
    if not avisos:
        print("Ahora mismo no toca ningún aviso.")
    else:
        if args.simular:
            print(f"Avisos que tocarían (no se ha mandado nada): {len(avisos)}")
        else:
            print(f"Avisos enviados: {len(avisos)}")
    return 0


def esperar(segundos: float) -> None:
    """Pausa entre revisiones. En las pruebas se cambia por una que no espera."""
    time.sleep(segundos)


def _revisar_avisos_una_vez(con, cfg: Config) -> int:
    """Manda los avisos que tocan ahora. Devuelve cuántos se han mandado."""
    ahora = ahora_local(cfg)
    try:
        notificador = crear_notificador(cfg)
        avisos = enviar_avisos(con, notificador, ahora, cfg)
    except ErrorDeEnvio as error:
        print(f"No se han podido mandar los avisos: {error}")
        print("Se volverá a intentar en la próxima revisión.")
        return 0
    if avisos:
        print(f"Avisos enviados: {len(avisos)}")
    return len(avisos)


def orden_vigilar(args, cfg: Config) -> int:
    """Revisa las citas cada pocos minutos hasta que se pulsa Control + C."""
    print("Vigilando tus citas. Para parar, pulsa Control + C")
    try:
        while True:
            con = db.conectar(cfg.ruta_bd)
            try:
                _revisar_avisos_una_vez(con, cfg)
            finally:
                con.close()
            esperar(cfg.minutos_entre_revisiones * 60)
    except KeyboardInterrupt:
        print()
        print("Vigilancia parada. Hasta luego.")
        return 0


def orden_demo(args, cfg: Config) -> int:
    """Apunta tres citas de ejemplo y enseña cómo llegarían los avisos."""
    hoy = ahora_local(cfg).replace(hour=0, minute=0)
    ejemplos = [
        Cita(
            titulo="Analítica de sangre y orina",
            tipo="analitica",
            fecha_hora=(hoy + timedelta(days=3)).replace(hour=8, minute=30),
            lugar="Centro de salud",
            preparacion=[
                "Ve en ayunas: sin comer nada desde las 12 de la noche",
                "Lleva la muestra de orina de la primera hora de la mañana",
                "Lleva el volante del médico, el papel con lo que te tienen que sacar",
            ],
        ),
        Cita(
            titulo="Vacuna de la gripe",
            tipo="vacuna",
            fecha_hora=(hoy + timedelta(days=6)).replace(hour=11, minute=0),
            lugar="Centro de salud, enfermería",
            preparacion=["Lleva la tarjeta sanitaria"],
        ),
        Cita(
            titulo="Revisión con la médica de cabecera",
            tipo="cita",
            fecha_hora=(hoy + timedelta(days=10)).replace(hour=12, minute=15),
            lugar="Centro de salud, consulta 4",
            preparacion=["Lleva el registro de la tensión de las últimas semanas"],
        ),
    ]
    con = db.conectar(cfg.ruta_bd)
    for cita in ejemplos:
        db.guardar_cita(con, cita)
        print(f"Apuntada: {_linea_cita(cita)}")
    primera = ejemplos[0]
    print()
    for tipo, momento in momentos_de_aviso(primera, cfg).items():
        nombre = f"{cfg.dias_antes} días antes" if tipo == "previo" else "el mismo día"
        print(f"Así te llegará el aviso {nombre} ({fecha_larga(momento)} a las {hora_texto(momento)}):")
        NotificadorConsola().enviar(texto_aviso(primera, momento))
    return 0


TEXTO_DE_SALUDO = "Hola, soy tu Acompañante de salud. Los avisos te llegarán por aquí."


def orden_mi_chat(args, cfg: Config) -> int:
    """Pregunta a Telegram y enseña el número de chat de quien escribió al bot."""
    chats = consultar_chats(cfg.telegram_token)
    if not chats:
        print("Todavía no le has escrito a tu bot.")
        print('Abre Telegram, busca tu bot y escríbele "hola".')
        print("Después vuelve a ejecutar esta orden.")
        return 0
    if len(chats) == 1:
        numero, nombre = chats[0]
        if nombre:
            print(f"Te ha escrito {nombre}.")
        print(f"Tu número de chat es: {numero}")
    else:
        print("Estas personas le han escrito a tu bot:")
        for posicion, (numero, nombre) in enumerate(chats, start=1):
            print(f"{posicion}. {nombre or 'Sin nombre'}: {numero}")
        print("Usa el número de la persona que quieras.")
    print("Copia el número en el archivo .env, en TELEGRAM_CHAT_ID.")
    return 0


def orden_probar_telegram(args, cfg: Config) -> int:
    """Manda el mensaje de saludo al móvil con Telegram."""
    NotificadorTelegram(cfg.telegram_token, cfg.telegram_chat_id).enviar(TEXTO_DE_SALUDO)
    print("Mensaje enviado. Mira tu móvil.")
    return 0


def crear_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m acompanante", description="Acompañante de salud: citas y recordatorios.")
    sub = p.add_subparsers(dest="orden", required=True, metavar="orden")

    s = sub.add_parser("iniciar", help="Crea la base de datos.")
    s.set_defaults(funcion=orden_iniciar)

    s = sub.add_parser("mi-chat", help="Averigua tu número de chat de Telegram.")
    s.set_defaults(funcion=orden_mi_chat)

    s = sub.add_parser("probar-telegram", help="Manda un mensaje de prueba a tu móvil por Telegram.")
    s.set_defaults(funcion=orden_probar_telegram)

    s = sub.add_parser("nueva-cita", help="Apunta una cita, analítica, vacuna o prueba.")
    s.add_argument("--titulo", required=True, help="Por ejemplo: Analítica de sangre")
    s.add_argument("--fecha", required=True, help="Por ejemplo: 12/11/2026")
    s.add_argument("--hora", required=True, help="Por ejemplo: 8:30")
    s.add_argument("--tipo", default="cita", choices=list(TIPOS), help="Tipo de cita (por defecto: cita)")
    s.add_argument("--lugar", help="Por ejemplo: Centro de salud de Coia")
    s.add_argument("--preparar", action="append", help="Algo que preparar. Se puede repetir.")
    s.add_argument(
        "--sin-sugerencias",
        action="store_true",
        help="No añadir la lista de preparación sugerida del tipo de cita.",
    )
    s.add_argument("--notas", help="Cualquier nota extra")
    s.set_defaults(funcion=orden_nueva_cita)

    s = sub.add_parser("borrar-cita", help="Borra una cita. Pide confirmación.")
    s.add_argument("id", type=int, help="El número entre corchetes que sale en citas")
    s.set_defaults(funcion=orden_borrar_cita)

    s = sub.add_parser("cambiar-cita", help="Cambia los datos de una cita.")
    s.add_argument("id", type=int, help="El número entre corchetes que sale en citas")
    s.add_argument("--titulo", help="Por ejemplo: Analítica de sangre")
    s.add_argument("--fecha", help="Por ejemplo: 12/11/2026")
    s.add_argument("--hora", help="Por ejemplo: 8:30")
    s.add_argument("--tipo", choices=list(TIPOS), help="Tipo de cita")
    s.add_argument("--lugar", help="Por ejemplo: Centro de salud de Coia")
    s.add_argument("--preparar", action="append", help="Algo que preparar. Se puede repetir.")
    s.add_argument("--notas", help="Cualquier nota extra")
    s.set_defaults(funcion=orden_cambiar_cita)

    s = sub.add_parser("citas", help="Muestra las próximas citas.")
    s.add_argument("--todas", action="store_true", help="Incluye también las que ya pasaron")
    s.set_defaults(funcion=orden_citas)

    s = sub.add_parser("avisos", help="Manda los avisos que tocan ahora.")
    s.add_argument("--ahora", help="Hacer como si fuera esta fecha y hora, por ejemplo: '10/11/2026 10:00'")
    s.add_argument("--simular", action="store_true", help="Solo enseña los avisos, sin mandarlos ni apuntarlos")
    s.set_defaults(funcion=orden_avisos)

    s = sub.add_parser("vigilar", help="Revisa las citas cada pocos minutos hasta que pares con Control + C.")
    s.set_defaults(funcion=orden_vigilar)

    s = sub.add_parser("demo", help="Apunta citas de ejemplo y enseña cómo serían los avisos.")
    s.set_defaults(funcion=orden_demo)
    return p


def main(argv: list[str] | None = None, cfg: Config | None = None) -> int:
    if cfg is None:
        cargar_env()
        cfg = leer_config()
    args = crear_parser().parse_args(argv)
    try:
        return args.funcion(args, cfg)
    except (ValueError, ErrorDeEnvio) as error:
        print(f"Error: {error}")
        return 1
