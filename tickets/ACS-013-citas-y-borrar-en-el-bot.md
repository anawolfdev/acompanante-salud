# ACS-013 · Ver todas las citas y borrar una desde el bot

**Tiempo estimado:** 1 h  
**Tamaño:** pequeño  
**Antes hace falta:** ACS-009 y ACS-010

## Para qué sirve

Que desde Telegram se puedan ver todas las citas futuras y borrar una sin abrir la terminal.

## Qué hay que hacer

1. Comando `/citas`: enseña todas las citas futuras ordenadas por fecha, sin el límite de 5 de `/proximas`. Cada cita sale con su número, igual que en la orden de terminal `citas`.
2. Comando `/borrar N`: busca la cita con ese número. Si el número no existe, contesta con un mensaje claro y amable. Si existe, enseña la cita y pregunta "¿La borro? Responde sí o no". Solo borra si la persona responde que sí.
3. Reutilizar la lógica que ya existe en la terminal para `borrar-cita`, sin copiarla.
4. Actualizar el texto de `/ayuda` (`AYUDA`) para incluir los dos comandos nuevos.
5. Mejorar el texto de `/tension` para que diga: "Para apuntar la tensión escribe: /tension 130 85 72. El primer número es la tensión alta, el segundo la baja y el tercero, si quieres, el pulso."
6. Añadir pruebas con datos ficticios. No usar datos reales ni tocar el archivo `.env`.

## Criterios de aceptación (cuándo está terminado)

- [ ] `/citas` enseña todas las citas futuras, ordenadas por fecha y con su número.
- [ ] `/borrar N` pide confirmación y solo borra cuando se responde que sí.
- [ ] Un número que no existe da un mensaje claro y amable.
- [ ] `/ayuda` incluye `/citas` y `/borrar`.
- [ ] `/tension` explica para qué es cada número.
- [ ] Todas las pruebas pasan.

## Qué revisa Ana

Que `/citas` y `/borrar` se entienden escuchados con el lector de pantalla y que borrar no borra nada sin confirmación.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md y tickets/ACS-013-citas-y-borrar-en-el-bot.md. Haz solo este ticket. No toques .env ni uses datos reales.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```
