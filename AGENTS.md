# Instrucciones para el agente (OpenCode)

## El proyecto

"Acompañante de salud": agenda de citas médicas, analíticas, vacunas y pruebas que avisa
a tiempo con lo que hay que preparar. Etapa 1. Python + SQLite. Avisos por Telegram.

La responsable es Ana. Ella revisa y aprueba; no es programadora a tiempo completo.
**Explícale siempre las cosas en español de España, con palabras sencillas.**

## Cómo trabajar

1. Haz **un solo ticket cada vez**: el de `tickets/` que te indique Ana. No adelantes trabajo de otros tickets.
2. Antes de cambiar nada, lee el ticket entero y los archivos que menciona.
3. Cambia lo mínimo necesario. No reorganices ni "mejores" código que el ticket no pide.
4. Cada cambio de comportamiento lleva su prueba en `tests/`.
5. Al terminar, ejecuta `python -m pytest`. Todas las pruebas tienen que pasar.
   Si alguna falla, arréglalo antes de dar el ticket por terminado.
6. Termina siempre con este resumen para Ana:
   - **Qué he cambiado:** 2-4 frases sencillas.
   - **Cómo lo pruebas tú:** las órdenes exactas que tiene que escribir.
   - **Qué no he hecho o no he podido comprobar.**

## Normas del código

- Python 3.10 o superior. Solo la biblioteca estándar. **No añadas dependencias**
  (ni en `requirements.txt` ni con pip) sin que Ana lo apruebe en el ticket.
- Nombres de funciones, variables y mensajes en español (sin tildes en los nombres de código).
- Las fechas se guardan como texto `AAAA-MM-DD HH:MM` en hora de Madrid (`Europe/Madrid`).
- Las fechas que ve la persona se escriben con `textos.py`: "jueves 12 de noviembre a las 8:30".
- La configuración se lee de `.env` con `config.py`. Las claves nunca se escriben en el código.
- La IA se usa a través de `ia.py` (`crear_cliente_ia`). No llames a un proveedor concreto desde otro sitio.
- Las pruebas no usan Internet: usa objetos falsos, como en `tests/test_notificador.py` y `tests/test_ia.py`.

## Normas de los mensajes que ve la persona (accesibilidad)

- Frases cortas. Una idea por línea. Primero lo más importante: qué, cuándo y dónde.
- Listas numeradas ("1.", "2.") para los pasos. Se oyen bien con lectores de pantalla.
- Sin emojis, sin abreviaturas ("c/", "hrs"), sin mayúsculas para gritar.
- Las horas como se dicen: "8:30", no "08:30h".
- Si algo falla, el mensaje dice qué pasó y qué hacer, sin jerga técnica.

## Lo que la aplicación NO hace

- No da consejos médicos ni diagnósticos. Recuerda y organiza; lo que diga el médico manda.
- Si se registra un valor (por ejemplo, la tensión), solo se guarda y se enseña. No se interpreta.

## Seguridad y privacidad

- Nunca subas `.env` ni la carpeta `datos/` a GitHub. Ya están en `.gitignore`: no lo cambies.
- No metas datos personales reales en pruebas ni ejemplos.

## Órdenes útiles

```
python -m pytest                 # pruebas
python -m acompanante demo       # demo con citas de ejemplo
python -m acompanante --help     # todas las órdenes
```
