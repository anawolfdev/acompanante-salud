# ACS-012 · Revisión de accesibilidad y demo

**Tiempo estimado:** 1 h 30 min  
**Tamaño:** pequeño  
**Antes hace falta:** los anteriores que quieras enseñar

## Para qué sirve

Comprobar que lo usa bien una persona ciega o con poca visión, y preparar una demo de 2 minutos.

## Qué hay que hacer

1. (Lo haces tú) Escucha todos los mensajes del bot con TalkBack o VoiceOver en el móvil y, si puedes, con tu padre y ZoomText.
2. Apunta en `docs/accesibilidad.md` qué se entiende mal.
3. (OpenCode) Corrige esas frases.
4. Escribe `docs/guion-demo.md`: 5 pasos para enseñar la demo (apuntar una cita, ver el aviso, apuntar la tensión, foto del papel).
5. Haz 2 o 3 capturas del bot para contarlo en X.

## Criterios de aceptación (cuándo está terminado)

- [ ] Todos los mensajes se entienden escuchados, sin mirar la pantalla.
- [ ] El guion de demo funciona de principio a fin.
- [ ] Todas las pruebas pasan.

## Qué revisa Ana

Que tu padre (o alguien con lector de pantalla) entiende los avisos sin ayuda.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md, tickets/ACS-012-accesibilidad-y-demo.md y docs/accesibilidad.md. Corrige las frases que aparecen como difíciles de entender. No cambies nada más.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```
