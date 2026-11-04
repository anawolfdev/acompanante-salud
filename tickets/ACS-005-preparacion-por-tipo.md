# ACS-005 · Lista de preparación sugerida según el tipo de cita

**Tiempo estimado:** 45 min  
**Tamaño:** pequeño  
**Antes hace falta:** ACS-001

## Para qué sirve

Para no tener que acordarte de qué llevar: si es una analítica, te sugiere ayunas, muestra de orina y volante.

## Qué hay que hacer

1. Crear `acompanante/plantillas.py` con una lista sugerida por tipo. Analítica: "Ve en ayunas si te lo han indicado", "Lleva la muestra de orina si te la han pedido", "Lleva el volante del médico", "Lleva la tarjeta sanitaria". Vacuna: "Lleva la tarjeta sanitaria", "Lleva la cartilla de vacunación si la tienes". Cita y prueba: "Lleva la tarjeta sanitaria" y "Lleva los informes o papeles que te hayan dado".
2. En `nueva-cita`, si no se escribe ningún `--preparar`, se usa la lista sugerida del tipo.
3. Opción `--sin-sugerencias` para no usarla.
4. Ana puede cambiar las frases en un solo sitio (plantillas.py).

## Criterios de aceptación (cuándo está terminado)

- [ ] Una analítica nueva sin --preparar sale con la lista de analítica en el aviso.
- [ ] Si escribes tu propio --preparar, se usa el tuyo y no la sugerencia.
- [ ] Todas las pruebas pasan.

## Qué revisa Ana

Que las frases de cada lista son las que tú usarías y están en un español claro. Cámbialas a tu gusto en plantillas.py.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md y tickets/ACS-005-preparacion-por-tipo.md. Haz solo este ticket.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```
