# ACS-006 · Aviso la noche antes si hay que ir en ayunas

**Tiempo estimado:** 45 min  
**Tamaño:** pequeño  
**Antes hace falta:** ACS-005

## Para qué sirve

Si la analítica es a las 8:30, el aviso de las 7:30 llega tarde para el ayuno. Hace falta uno la noche anterior.

## Qué hay que hacer

1. En `recordatorios.py`, nuevo aviso "vispera": la noche anterior a las 21:00 (HORA_AVISO_VISPERA en `.env`), solo si algún paso de preparación contiene la palabra "ayunas".
2. Texto: "Mañana tienes analítica a las 8:30. Desde ahora, no comas nada. Deja preparado: …" con la lista numerada.
3. Las mismas reglas que los otros avisos: no se repite y no sale si la cita ya pasó.
4. Pruebas para: cita con ayunas (sale), cita sin ayunas (no sale).

## Criterios de aceptación (cuándo está terminado)

- [ ] Una analítica con "ayunas" a las 8:30 da 3 avisos: 2 días antes, la noche antes a las 21:00 y el mismo día.
- [ ] Una vacuna no tiene aviso la noche antes.
- [ ] Todas las pruebas pasan.

## Qué revisa Ana

Que el mensaje de la noche anterior es claro y llega a una hora que te viene bien.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md y tickets/ACS-006-aviso-ayunas.md. Haz solo este ticket. Sigue el mismo estilo que los avisos 'previo' y 'dia' de recordatorios.py.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```
