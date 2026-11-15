# ACS-016 · Botones y paso a paso en el bot de Telegram

**Tiempo estimado:** 2 h  
**Tamaño:** mediano  
**Antes hace falta:** ACS-013 y ACS-014

## Para qué sirve

Que en Telegram se vea claro qué botones son de cada cita y de cada toma de
tensión. Así no hay que escribir números para cambiar o borrar algo.

También que se pueda apuntar una toma de tensión de otro día, no solo del
momento actual, y que la ayuda se entienda a la primera.

## Qué hay que hacer

1. En `citas`, mandar primero un mensaje de cabecera y después cada cita en su
   propio mensaje. Debajo de cada cita van los botones "Cambiar" y "Borrar".
2. En `historial`, hacer lo mismo con las últimas tomas de tensión: un mensaje
   por toma, con los botones "Modificar" y "Borrar" debajo.
3. Si se pulsa "Cambiar" en una cita, preguntar la fecha y la hora nuevas y
   confirmar el cambio antes de guardarlo.
4. Si se pulsa "Borrar", preguntar antes con los botones "Sí" y "No". Solo
   borrar cuando la persona responde que sí.
5. Si se pulsa "Modificar" en una toma de tensión, pedir los valores nuevos
   (alta, baja y, si se quiere, el pulso). Después preguntar si se quiere
   cambiar también la fecha y la hora. Si se escribe "no", se queda la que
   tenía.
6. Añadir el comando `borrar-tension N` para borrar una toma de tensión. El
   número 1 es la toma más reciente. Antes de borrar, enseñar la toma y pedir
   confirmación.
7. Hacer que `tension` acepte la fecha y la hora al final, con o sin pulso:
   `tension 130 85 72 14/11/2026 8:30` o
   `tension 130 85 14/11/2026 8:30`. Si no se pone fecha, se usa el momento
   actual.
8. Si la fecha o la hora están mal escritas, contestar con un mensaje claro y
   un ejemplo.
9. Simplificar los textos de la ayuda: una línea por comando, con las palabras
   que se dicen. Incluir `historial` y explicar que en `tension` se puede
   añadir la fecha al final.
10. Aceptar las órdenes con o sin barra (`citas` o `/citas`), porque en
    Telegram es más fácil escribirlas sin barra.
11. En el menú de comandos de Telegram, poner `ayuda`, `anadir`, `citas`,
    `tension` e `historial`. El nombre `anadir` va sin tilde porque Telegram
    no admite tildes en los nombres de comando.
12. Si se pulsa un botón de una cita o de una toma que ya no existe, avisar con
    un mensaje claro, sin romperse.
13. Añadir pruebas con datos ficticios. No usar datos reales ni tocar el
    archivo `.env`.

## Criterios de aceptación (cuándo está terminado)

- [ ] `citas` manda cada cita en su propio mensaje, con "Cambiar" y "Borrar"
      debajo.
- [ ] `historial` manda cada toma en su propio mensaje, con "Modificar" y
      "Borrar" debajo.
- [ ] "Cambiar" pide la fecha y la hora nuevas y solo cambia al confirmar.
- [ ] "Borrar" pide confirmación y solo borra al responder que sí.
- [ ] "Modificar" pide alta, baja y pulso, y después la fecha y la hora
      opcionales.
- [ ] Escribir "no" al pedir la fecha conserva la fecha que tenía la toma.
- [ ] `borrar-tension N` pide confirmación y borra la toma indicada.
- [ ] Un número de toma que no existe da un mensaje claro.
- [ ] `tension` acepta la fecha y la hora al final, con o sin pulso.
- [ ] Sin fecha, `tension` usa el momento actual.
- [ ] Una fecha o una hora mal escritas dan un mensaje claro con un ejemplo.
- [ ] La ayuda tiene una línea por comando y explica lo nuevo.
- [ ] Las órdenes funcionan con y sin barra.
- [ ] El menú de Telegram tiene los cinco comandos.
- [ ] Un botón antiguo avisa si la cita o la toma ya no existe.
- [ ] Todas las pruebas pasan.

## Qué revisa Ana

Que en Telegram cada cita y cada toma llega en su propio mensaje, con sus
botones justo debajo. Que "Cambiar", "Modificar" y "Borrar" preguntan lo que
falta antes de tocar nada. También que se puede apuntar una toma de otro día y
que la ayuda se entiende escuchada con el lector de pantalla.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md, tickets/ACS-016-botones-y-paso-a-paso.md y
acompanante/conversacion.py. Haz solo este ticket.
Pon los botones "Cambiar" y "Borrar" debajo de cada cita, y "Modificar" y
"Borrar" debajo de cada toma de tensión. Añade el comando borrar-tension,
permite poner fecha y hora al final de tension y simplifica la ayuda.
No toques .env ni uses datos reales.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has
cambiado, cómo lo pruebo yo y qué no has hecho.
```
