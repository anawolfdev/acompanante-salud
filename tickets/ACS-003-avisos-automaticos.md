# ACS-003 · Que los avisos salgan solos

**Tiempo estimado:** 1 h  
**Tamaño:** pequeño  
**Antes hace falta:** ACS-002

## Para qué sirve

Ahora hay que escribir `avisos` a mano. Con esto, el programa se queda encendido y revisa cada pocos minutos.

## Qué hay que hacer

1. Añadir la orden `python -m acompanante vigilar`, que cada 5 minutos ejecuta lo mismo que `avisos`.
2. Al arrancar, escribe "Vigilando tus citas. Para parar, pulsa Control + C".
3. Si Telegram falla una vez, lo apunta en pantalla y lo vuelve a intentar en la siguiente vuelta (no se cierra).
4. Los minutos entre revisiones se leen de `.env` (MINUTOS_ENTRE_REVISIONES, por defecto 5) y se añade al `.env.example`.
5. Pruebas sin esperar de verdad (la espera se puede sustituir en la prueba).

## Criterios de aceptación (cuándo está terminado)

- [ ] Con `vigilar` encendido, un aviso que toca en los próximos minutos llega solo a Telegram.
- [ ] No llega dos veces el mismo aviso.
- [ ] Control + C lo para con un mensaje de despedida, sin errores en pantalla.
- [ ] Todas las pruebas pasan.

## Qué revisa Ana

Apunta una cita para dentro de 2 días y 5 minutos, deja `vigilar` encendido y comprueba que te llega el aviso.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md y tickets/ACS-003-avisos-automaticos.md. Haz solo este ticket. La función de espera tiene que poder cambiarse en las pruebas para que no tarden.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```
