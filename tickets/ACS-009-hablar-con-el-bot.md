# ACS-009 · Hablar con el bot desde Telegram

**Tiempo estimado:** 2 h  
**Tamaño:** mediano  
**Antes hace falta:** ACS-003 y ACS-008

## Para qué sirve

Usarlo desde el móvil sin abrir el ordenador: preguntar qué citas tienes o apuntar la tensión.

## Qué hay que hacer

1. Dentro de `vigilar`, leer los mensajes nuevos del bot (getUpdates de Telegram, sin librerías nuevas).
2. Responder SOLO al TELEGRAM_CHAT_ID del `.env`; a cualquier otra persona, nada.
3. /proximas: las próximas 5 citas.
4. /tension 130 85 72: guarda la toma y responde "Apuntado: 130 de alta, 85 de baja, pulso 72".
5. /ayuda: qué puede hacer, en 4 líneas.
6. Cualquier otra cosa: "No te he entendido. Escribe /ayuda para ver lo que sé hacer."

## Criterios de aceptación (cuándo está terminado)

- [ ] Desde el móvil, /proximas responde con tus citas.
- [ ] /tension guarda la toma y sale después en `historial-tension`.
- [ ] Un mensaje desde otra cuenta de Telegram no recibe respuesta.
- [ ] Todas las pruebas pasan.

## Qué revisa Ana

Que puedes usar /proximas y /tension desde el móvil con el lector de pantalla, y que a otra cuenta no le contesta.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md y tickets/ACS-009-hablar-con-el-bot.md. Haz solo este ticket. Separa la parte que entiende el mensaje (fácil de probar) de la parte que habla con Telegram.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```
