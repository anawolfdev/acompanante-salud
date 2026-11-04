# ACS-011 · Foto del papel de la cita

**Tiempo estimado:** 2 h  
**Tamaño:** mediano  
**Antes hace falta:** ACS-010

## Para qué sirve

Hacer una foto al papel de la cita o al volante y que el bot apunte fecha, hora, lugar y qué preparar.

## Qué hay que hacer

1. En Telegram, si llega una foto, el bot la descarga (getFile de Telegram).
2. Se la manda a la IA con `preguntar(texto, imagen=...)` y la misma petición de JSON que en ACS-010.
3. El bot lee en voz clara lo que ha entendido y pregunta "¿La guardo? Responde sí o no".
4. Si la foto no se lee bien: "No consigo leer bien el papel. Prueba con más luz, o escríbeme la cita."
5. Pruebas con una foto de ejemplo inventada y una IA falsa.

## Criterios de aceptación (cuándo está terminado)

- [ ] Con la foto de un papel de cita (de ejemplo, sin datos reales), el bot propone la cita correcta.
- [ ] No se guarda nada sin un "sí".
- [ ] Todas las pruebas pasan.

## Qué revisa Ana

Prueba con 3 papeles (tapa tus datos personales) y comprueba que la fecha y la hora están bien antes de decir que sí.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md y tickets/ACS-011-foto-del-papel.md. Haz solo este ticket. Reutiliza la función de ACS-010.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```
