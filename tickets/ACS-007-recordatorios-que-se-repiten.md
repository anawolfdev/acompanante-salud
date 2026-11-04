# ACS-007 · Recordatorios que se repiten (como tomarse la tensión)

**Tiempo estimado:** 1 h 30 min  
**Tamaño:** mediano  
**Antes hace falta:** ACS-003

## Para qué sirve

Las cosas de cada semana: "tómate la tensión el lunes a las 9:00".

## Qué hay que hacer

1. Tabla nueva `tareas` en `db.py`: título, días de la semana, hora, activa sí o no.
2. Orden `nueva-tarea --titulo "Tomarte la tensión" --dias lunes --hora 9:00` (acepta varios días: "lunes,jueves").
3. Órdenes `tareas` (lista) y `pausar-tarea ID`.
4. `avisos` y `vigilar` mandan también estas tareas cuando toca, una vez por día y hora.
5. Texto: "Recordatorio: hoy lunes toca tomarte la tensión."

## Criterios de aceptación (cuándo está terminado)

- [ ] Una tarea de los lunes a las 9:00 avisa el lunes a las 9:00 y no se repite ese día.
- [ ] Una tarea pausada no avisa.
- [ ] Todas las pruebas pasan.

## Qué revisa Ana

Crea tu tarea real de la tensión y comprueba con `avisos --simular --ahora` que sale el día y la hora correctos.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md y tickets/ACS-007-recordatorios-que-se-repiten.md. Haz solo este ticket. Las tareas se apuntan como enviadas igual que las citas, para no repetirse.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```
