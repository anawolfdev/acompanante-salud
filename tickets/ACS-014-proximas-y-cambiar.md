# ACS-014 · Quitar /proximas, cambiar y añadir citas desde el bot

**Tiempo estimado:** 1 h 30 min  
**Tamaño:** pequeño  
**Antes hace falta:** ACS-013

## Para qué sirve

Que en Telegram haya un solo comando para ver las citas y que se pueda añadir
una cita o cambiar su día y hora sin abrir la terminal.

## Qué hay que hacer

1. Quitar el comando `/proximas`. `/citas` queda como el único para ver las citas.
   Si alguien escribe `/proximas`, el bot responde: "Ahora se llama /citas".
   También hay que quitar `/proximas` de la ayuda (`AYUDA`).
2. Añadir el comando `/añadir Título de la cita | DD/MM/AAAA HH:MM | Lugar`
   para apuntar una cita nueva. El lugar es opcional.
3. Antes de guardar la cita nueva, el bot enseña cómo quedará y pregunta
   "¿La guardo? Responde sí o no". Solo guarda si la persona responde que sí.
4. Si falta el título, la fecha o la hora, o la fecha está mal escrita, el bot
   contesta con un mensaje claro y amable que incluye un ejemplo.
5. Reutilizar la lógica de la terminal (orden `nueva-cita`). Si hace falta, mover
   la creación de la cita a `acciones.py` para usarla en los dos sitios, sin
   duplicarla.
6. Añadir el comando `/cambiar N DD/MM/AAAA HH:MM` para cambiar la fecha y la hora
   de la cita con ese número (el mismo que sale en `/citas`).
7. Antes de cambiar la cita, el bot enseña cómo está y cómo quedará, y pregunta
   "¿La cambio? Responde sí o no". Solo cambia si la persona responde que sí.
8. Si el número no existe, o la fecha o la hora están mal escritas, el bot contesta
   con un mensaje claro y amable que incluye un ejemplo.
9. Reutilizar la lógica de la terminal (orden `cambiar-cita`). Si hace falta, mover
   el guardado con el recálculo de avisos a `acciones.py` para usarlo en los dos
   sitios, sin duplicarlo.
10. Al cambiar la fecha o la hora, los avisos de esa cita se recalculan igual que
    en la terminal: se olvidan los ya enviados para que vuelvan a salir.
11. Actualizar `AYUDA` con los comandos `/añadir` y `/cambiar`.
12. Añadir pruebas con datos ficticios. No usar datos reales ni tocar el archivo `.env`.

## Criterios de aceptación (cuándo está terminado)

- [ ] `/proximas` ya no enseña citas: responde "Ahora se llama /citas".
- [ ] `/proximas` ya no aparece en la ayuda.
- [ ] `/añadir Título | DD/MM/AAAA HH:MM | Lugar` enseña cómo quedará la cita antes de guardarla.
- [ ] La cita solo se guarda cuando se responde que sí.
- [ ] `/añadir` funciona también sin lugar.
- [ ] Si falta algo o la fecha está mal escrita, el mensaje es claro e incluye un ejemplo.
- [ ] La cita nueva usa la misma preparación sugerida que la terminal.
- [ ] `/cambiar N DD/MM/AAAA HH:MM` enseña la cita actual y la nueva antes de cambiar.
- [ ] La cita solo cambia cuando se responde que sí.
- [ ] Un número que no existe da un mensaje claro y amable.
- [ ] Una fecha o una hora mal escrita da un mensaje claro con un ejemplo.
- [ ] Al cambiar la fecha, los avisos de esa cita vuelven a salir.
- [ ] `AYUDA` incluye `/añadir` y `/cambiar`.
- [ ] La terminal sigue funcionando igual con `nueva-cita` y `cambiar-cita`.
- [ ] Todas las pruebas pasan.

## Qué revisa Ana

Que `/citas` sigue enseñando las citas con su número, que `/proximas` avisa del
cambio de nombre, que `/añadir` no guarda nada hasta responder que sí y que
`/cambiar` no cambia nada hasta responder que sí. También que los mensajes se
entienden escuchados con el lector de pantalla.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md, tickets/ACS-014-proximas-y-cambiar.md, acompanante/conversacion.py,
acompanante/cli.py y acompanante/acciones.py. Haz solo este ticket.
No toques .env ni uses datos reales.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has
cambiado, cómo lo pruebo yo y qué no has hecho.
```
