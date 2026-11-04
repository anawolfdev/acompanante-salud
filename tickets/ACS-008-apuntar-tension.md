# ACS-008 · Apuntar la tensión

**Tiempo estimado:** 1 h  
**Tamaño:** pequeño  
**Antes hace falta:** ACS-001

## Para qué sirve

Guardar cada toma de tensión para llevarla al médico, en vez de un papel.

## Qué hay que hacer

1. Tabla `tensiones` en `db.py`: fecha y hora, alta (sistólica), baja (diastólica), pulso (opcional) y nota.
2. Orden `tension 130 85 --pulso 72 --nota "después de cenar"`.
3. Orden `historial-tension` con las últimas 10 tomas, una por línea: "lunes 9 de noviembre, 9:05: 130 de alta, 85 de baja, pulso 72".
4. No interpreta los valores (nada de "está alta"): solo los guarda y los enseña.
5. Valores imposibles (por ejemplo, alta menor que baja, o letras) dan un mensaje claro.

## Criterios de aceptación (cuándo está terminado)

- [ ] Una toma guardada sale en el historial con fecha y valores.
- [ ] El historial se entiende leído en voz alta.
- [ ] Todas las pruebas pasan.

## Qué revisa Ana

Que el historial se oye bien con el lector de pantalla y que sirve para enseñárselo al médico.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md y tickets/ACS-008-apuntar-tension.md. Haz solo este ticket. Recuerda: la aplicación no interpreta valores médicos.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```
