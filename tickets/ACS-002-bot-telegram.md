# ACS-002 · Crear tu bot de Telegram y mandar un mensaje de prueba

**Tiempo estimado:** 45 min  
**Tamaño:** pequeño  
**Antes hace falta:** ACS-001

## Para qué sirve

Que los avisos te lleguen al móvil. El bot ya lo creaste en la fase 0; ahora el programa aprende a escribirte.

## Qué hay que hacer

1. (Lo haces tú) Comprueba que el token del bot (fase 0, paso 0.8) está en `.env` como TELEGRAM_TOKEN y que le has escrito "hola" a tu bot.
2. (OpenCode) Añade la orden `python -m acompanante mi-chat`, que pregunta a Telegram (método getUpdates) y enseña el número de chat de quien escribió al bot.
3. (Lo haces tú) Pega ese número en `.env` como TELEGRAM_CHAT_ID y cambia CANAL=telegram.
4. (OpenCode) Añade la orden `python -m acompanante probar-telegram`, que manda "Hola, soy tu Acompañante de salud. Los avisos te llegarán por aquí." usando `NotificadorTelegram`.
5. Pruebas con respuestas falsas de Telegram, sin Internet.

## Criterios de aceptación (cuándo está terminado)

- [ ] Con el token puesto, `mi-chat` enseña tu número de chat.
- [ ] `probar-telegram` hace que te llegue el mensaje de saludo al móvil.
- [ ] Si falta el token, sale un mensaje claro que dice qué falta y dónde ponerlo (sin errores en inglés).
- [ ] Con `CANAL=telegram`, `python -m acompanante avisos --ahora "…"` manda el aviso a Telegram.
- [ ] Todas las pruebas pasan.

## Qué revisa Ana

Que te llega el saludo al móvil y que, con el lector de pantalla del móvil, el aviso de la demo se entiende bien.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md y tickets/ACS-002-bot-telegram.md. Haz solo la parte de OpenCode de este ticket: las órdenes mi-chat y probar-telegram, con sus pruebas. No uses librerías nuevas, usa urllib como en notificador.py.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```
