# Acompañante de salud

Una agenda de salud que no se olvida de nada. Apuntas tus citas médicas, analíticas,
vacunas y pruebas, y te avisa a tiempo con lo que tienes que preparar:
"pasado mañana tienes analítica a las 8:30; ve en ayunas, lleva la muestra de orina y el volante".

Está pensada para que la use cualquiera: mensajes cortos, claros y fáciles de escuchar
con un lector de pantalla.

## Qué hace ya (etapa 1, versión 0.1)

- Apunta citas, analíticas, vacunas y pruebas, con fecha, hora, lugar y lo que hay que preparar.
- Calcula los avisos: uno **2 días antes** (a las 10:00) y otro **el mismo día** (a las 7:30,
  o una hora antes si la cita es muy temprano).
- Escribe los avisos en lenguaje sencillo, con la lista de preparación numerada y sin emojis,
  para que se oigan bien con un lector de pantalla.
- No repite un aviso que ya se mandó.
- Puede mandar los avisos por Telegram (gratis) o enseñarlos en pantalla para probar.
- Tiene preparada la conexión con una IA gratuita (Gemini, Groq, OpenRouter u Ollama),
  que se cambia desde el archivo `.env` sin tocar código.

Lo que falta (tensión, recordatorios semanales, foto del papel de la cita…) está en la carpeta
`tickets/`, en orden.

## Ponerlo en marcha en 5 pasos

Si empiezas desde cero (instalar herramientas, crear el bot, subir a GitHub), sigue la **[GUIA.md](GUIA.md)**: lo explica todo paso a paso. Este resumen es para cuando ya lo tengas todo instalado.

Necesitas Python 3.10 o más nuevo.

1. **Entra en la carpeta del proyecto**
   ```
   cd acompanante-salud
   ```
2. **Crea un entorno para el proyecto y actívalo** (en Windows, escribe `python` donde pone `python3`)
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   En Windows, la segunda línea es: `.venv\Scripts\activate`
3. **Instala lo necesario**
   ```
   pip install -r requirements-dev.txt
   ```
4. **Crea tu archivo de configuración**
   ```
   cp .env.example .env
   ```
   En Windows: `copy .env.example .env`
5. **Comprueba que todo funciona**
   ```
   python -m pytest
   python -m acompanante demo
   ```
   Las pruebas tienen que salir en verde ("passed") y la demo te enseña cómo te llegarían los avisos.

## Órdenes que puedes usar

```
python -m acompanante nueva-cita --titulo "Analítica de sangre" --tipo analitica --fecha 12/11/2026 --hora 8:30 --lugar "Centro de salud" --preparar "Ve en ayunas" --preparar "Lleva la muestra de orina" --preparar "Lleva el volante"
python -m acompanante citas
python -m acompanante avisos --simular --ahora "10/11/2026 10:00"
python -m acompanante avisos
```

- `citas` enseña las próximas citas.
- `avisos --simular --ahora "…"` hace como si fuera ese día y esa hora, y te enseña el aviso sin mandarlo.
- `avisos` manda los avisos que tocan ahora (por pantalla o por Telegram, según `CANAL` en el `.env`).

## Que arranque solo al encender el Mac (solo macOS)

Con esto no tienes que lanzar `vigilar` a mano. El Mac arranca el bot solo
y lo vuelve a arrancar si se para.

1. **Instálalo una vez.** Entra en la carpeta del proyecto y escribe:
   ```
   ./scripts/instalar-servicio.sh
   ```
   El script coge el python que tengas activo (`which python3`), rellena la
   plantilla de `deploy/`, copia el archivo a `~/Library/LaunchAgents` y lo
   pone en marcha. No hace falta nada más.

2. **Comprueba que está funcionando.**
   ```
   launchctl list | grep acompanante
   ```
   Tiene que salir una línea con `com.anawolfdev.acompanante`.
   En la primera columna hay un número: es el proceso del bot.
   Si en la primera columna pone `-`, el bot no está arrancado ahora mismo.
   Si no sale ninguna línea, el servicio no está instalado.

3. **Mira los mensajes y los errores.**
   ```
   tail -f ~/Library/Logs/acompanante.log
   tail -f ~/Library/Logs/acompanante-error.log
   ```
   El primero dice qué hace el bot. El segundo dice qué ha fallado.
   Para dejar de mirar, pulsa Control + C (eso no para el bot).
   También puedes abrir los dos archivos con la aplicación TextEdit.

4. **Páralo y quítalo.**
   ```
   ./scripts/quitar-servicio.sh
   ```
   Para el bot y borra el arranque automático.
   Tus citas y tus claves no se tocan.
   Los logs se quedan en `~/Library/Logs` por si los necesitas.

Cosas que conviene saber:

- Si cambias el `.env` o el código, reinicia el servicio para que lo coja:
  ```
  launchctl kickstart -k gui/$(id -u)/com.anawolfdev.acompanante
  ```
- Si mueves la carpeta del proyecto, vuelve a ejecutar el instalador.
- Si usas el entorno `.venv` del proyecto, actívalo antes de instalar.
  El servicio usará ese python. Si borras `.venv`, vuelve a instalar.
- No lances `python -m acompanante vigilar` a mano mientras el servicio
  está funcionando: se pelearían por el mismo archivo de citas.

## Cómo trabajar con OpenCode

1. Abre una terminal en la carpeta del proyecto y escribe `opencode`.
2. Escribe `/models` y elige un modelo que ponga **Free** (gratis).
3. Haz un ticket cada vez: cada ticket de `tickets/` trae al final el prompt exacto para pegar.
4. Sigue el bucle de la GUIA.md: rama nueva, OpenCode, revisar `git diff`, pruebas, probarlo tú, subir y pull request.

El archivo `AGENTS.md` le explica a OpenCode las normas del proyecto. Lo lee solo.

## Cómo está organizado

```
acompanante/        el código
  cli.py            las órdenes de terminal
  recordatorios.py  cuándo toca cada aviso y cómo se escribe
  db.py             dónde se guardan las citas (SQLite, un solo archivo)
  notificador.py    por dónde salen los avisos (pantalla o Telegram)
  ia.py             conexión con la IA gratuita (cambiable)
  textos.py         fechas y horas en español
tests/              las pruebas automáticas
tickets/            el trabajo que falta, en orden
deploy/             plantilla para que el bot arranque solo en el Mac
scripts/            instalar y quitar ese arranque automático
GUIA.md             la guía paso a paso desde cero
docs/               hoja de ruta
```

## Privacidad

- Tus citas se guardan solo en tu ordenador, en `datos/salud.db`. Esa carpeta no se sube a GitHub.
- Las claves (Telegram, IA) van en `.env`, que tampoco se sube.
- Para probar la parte de IA, usa papeles de ejemplo o tapa tus datos personales.

## Hoja de ruta

- **Etapa 1 (ahora):** agenda de salud con avisos.
- **Etapa 2:** explicar con palabras claras lo que dijo el médico, un informe o una receta, y leer en voz alta cartas en papel.
- **Etapa 3:** red de personas voluntarias que acompañan a ir al médico, por videollamada o en persona.

Más detalle en `docs/hoja-de-ruta.md`.

## Responsable

Ana (anawolfdev)
