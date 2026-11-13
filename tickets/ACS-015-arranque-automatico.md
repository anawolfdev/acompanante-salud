# ACS-015 · Que el bot arranque solo en el Mac con launchd

**Tiempo estimado:** 45 min  
**Tamaño:** pequeño  
**Antes hace falta:** ACS-003

## Para qué sirve

Que no haya que abrir la terminal y escribir `python -m acompanante vigilar`
cada vez. El Mac arranca el bot solo al encenderse, y si el bot se para por
lo que sea, el Mac lo vuelve a arrancar.

Esto es solo para macOS. En Windows y Linux no se usa.

## Qué hay que hacer

1. Crear la plantilla `deploy/com.anawolfdev.acompanante.plist` para un
   LaunchAgent de launchd, con estos valores:
   - Nombre del servicio (`Label`): `com.anawolfdev.acompanante`.
   - Orden que ejecuta: `python -m acompanante vigilar`, con la ruta completa
     del python (la que sale con `which python3`).
   - `RunAtLoad` y `KeepAlive` en `true`.
   - `WorkingDirectory`: la carpeta del proyecto, para que el bot encuentre
     el `.env` y la carpeta `datos/`.
   - Los mensajes en `~/Library/Logs/acompanante.log` y los errores en
     `~/Library/Logs/acompanante-error.log`.
2. Crear `scripts/instalar-servicio.sh`. Tiene que:
   - Averiguar las rutas de este Mac (proyecto, python y logs).
   - Rellenar la plantilla con esas rutas.
   - Copiar el resultado a `~/Library/LaunchAgents`.
   - Cargarlo con `launchctl`.
   - Decir en pantalla qué ha hecho y cómo se comprueba.
3. Crear `scripts/quitar-servicio.sh`. Tiene que parar el servicio y borrar
   el archivo de `~/Library/LaunchAgents`. No borra las citas, ni el `.env`,
   ni los logs.
4. Explicar todo esto en el `README.md`, en palabras sencillas:
   cómo se instala, cómo se comprueba con `launchctl list | grep acompanante`,
   dónde están los logs y cómo se para.
5. Añadir pruebas en `tests/`. Las pruebas no instalan nada ni llaman a
   `launchctl`: solo leen los archivos y comprueban que son correctos.

## Lo que NO hay que hacer

- No tocar el archivo `.env`.
- No cambiar el código del bot (`acompanante/`).
- No añadir dependencias: todo con la biblioteca estándar.
- No instalar el servicio desde OpenCode. Solo se preparan los archivos.
  Ana lo instala cuando quiera.

## Criterios de aceptación (cuándo está terminado)

- [ ] `deploy/com.anawolfdev.acompanante.plist` existe y es un plist válido
      (`plutil -lint` dice OK).
- [ ] El plist tiene `RunAtLoad` y `KeepAlive` en `true`.
- [ ] El plist ejecuta `-m acompanante vigilar` con una ruta de python completa.
- [ ] `WorkingDirectory` es la carpeta del proyecto.
- [ ] Los logs van a `~/Library/Logs/acompanante.log` y
      `~/Library/Logs/acompanante-error.log`.
- [ ] `scripts/instalar-servicio.sh` existe, se puede ejecutar y rellena las rutas.
- [ ] `scripts/quitar-servicio.sh` existe, se puede ejecutar, para el servicio
      y borra el plist.
- [ ] El `README.md` explica instalar, comprobar, ver logs y parar.
- [ ] El `.env` y el código del bot siguen igual.
- [ ] Todas las pruebas pasan.

## Qué revisa Ana

Que después de `./scripts/instalar-servicio.sh`, la orden
`launchctl list | grep acompanante` enseñe el servicio, que los mensajes
aparezcan en el log y que `./scripts/quitar-servicio.sh` lo pare sin tocar
sus citas. También que las instrucciones del README se entiendan a la primera.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md, tickets/ACS-015-arranque-automatico.md y acompanante/cli.py.
Haz solo este ticket.
Crea deploy/com.anawolfdev.acompanante.plist, scripts/instalar-servicio.sh,
scripts/quitar-servicio.sh, las pruebas en tests/ y la explicación en README.md.
No toques .env ni el código del bot. No instales el servicio: solo prepara los archivos.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has
cambiado, cómo lo pruebo yo y qué no has hecho.
```
