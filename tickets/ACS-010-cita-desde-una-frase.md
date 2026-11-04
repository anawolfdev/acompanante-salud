# ACS-010 · Apuntar una cita escribiendo una frase normal (con IA gratis)

**Tiempo estimado:** 2 h  
**Tamaño:** mediano  
**Antes hace falta:** ACS-009

## Para qué sirve

Escribir "analítica el 12 de noviembre a las 8:30 en el centro de salud, en ayunas" y que se apunte sola.

## Qué hay que hacer

1. (Lo haces tú) En `.env`: IA_PROVEEDOR=gemini, IA_API_KEY con tu clave (fase 0, paso 0.9) e IA_MODELO con un modelo gratuito que veas en aistudio.google.com.
2. (OpenCode) Función `extraer_cita(texto)` en un archivo nuevo `acompanante/extraer.py` que usa `crear_cliente_ia` y pide a la IA un JSON con titulo, tipo, fecha, hora, lugar y preparacion.
3. Si a la IA le falta la fecha o la hora, no se inventa: se pregunta.
4. En Telegram, un mensaje que no empieza por / se trata como cita nueva: el bot responde con lo que ha entendido y pregunta "¿La guardo? Responde sí o no".
5. Solo se guarda si la respuesta es "sí".
6. Con IA_PROVEEDOR=ninguno, el bot dice que esta función no está activada.

## Criterios de aceptación (cuándo está terminado)

- [ ] Con la frase de ejemplo, el bot propone la cita con fecha, hora, lugar y preparación correctas.
- [ ] No se guarda nada sin un "sí".
- [ ] Las pruebas usan una IA falsa (sin Internet) y pasan.

## Qué revisa Ana

Prueba 5 frases distintas, como las dirías tú, y apunta en cuáles se equivoca.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md y tickets/ACS-010-cita-desde-una-frase.md. Haz solo este ticket. Usa ia.py; no llames a Gemini directamente.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```
