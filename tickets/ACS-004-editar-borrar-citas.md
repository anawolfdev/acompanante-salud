# ACS-004 · Cambiar y borrar citas

**Tiempo estimado:** 1 h  
**Tamaño:** pequeño  
**Antes hace falta:** ACS-001

## Para qué sirve

Las citas cambian: te la mueven de día o la anulas.

## Qué hay que hacer

1. Orden `borrar-cita ID` (el ID es el número entre corchetes que sale en `citas`). Pide confirmación: "¿Seguro que quieres borrar…? (s/n)".
2. Orden `cambiar-cita ID` con las mismas opciones que `nueva-cita` (todas opcionales): solo cambia lo que se indique.
3. Si cambia la fecha o la hora, se borran los avisos ya enviados de esa cita, para que vuelvan a salir.
4. Pruebas para las dos órdenes.

## Criterios de aceptación (cuándo está terminado)

- [ ] Borrar pide confirmación y, tras decir que sí, la cita ya no sale en `citas`.
- [ ] Cambiar la hora de una cita hace que el aviso vuelva a salir con la hora nueva.
- [ ] Un ID que no existe da un mensaje claro: "No hay ninguna cita con el número 7".
- [ ] Todas las pruebas pasan.

## Qué revisa Ana

Que borrar pide confirmación y que, al cambiar una cita de día, el aviso sale con el día nuevo (pruébalo con `avisos --simular --ahora`).

## Prompt para pegar en OpenCode

```
Lee AGENTS.md y tickets/ACS-004-editar-borrar-citas.md. Haz solo este ticket.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```
