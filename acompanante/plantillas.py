"""Frases de preparación sugeridas para cada tipo de cita.

Ana puede cambiar las frases en este archivo. El resto de la aplicación
usa estas listas tal cual.
"""

CITA_Y_PRUEBA = [
    "Lleva la tarjeta sanitaria",
    "Lleva los informes o papeles que te hayan dado",
]

PREPARACION_POR_TIPO = {
    "analitica": [
        "Ve en ayunas si te lo han indicado",
        "Lleva la muestra de orina si te la han pedido",
        "Lleva el volante del médico",
        "Lleva la tarjeta sanitaria",
    ],
    "vacuna": [
        "Lleva la tarjeta sanitaria",
        "Lleva la cartilla de vacunación si la tienes",
    ],
    "cita": CITA_Y_PRUEBA,
    "prueba": CITA_Y_PRUEBA,
    "otro": CITA_Y_PRUEBA,
}


def preparacion_sugerida(tipo: str) -> list[str]:
    """Devuelve una copia de la lista del tipo, para no cambiar la original."""
    return list(PREPARACION_POR_TIPO.get(tipo, CITA_Y_PRUEBA))
