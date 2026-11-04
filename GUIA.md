# Guía paso a paso

Esta guía te lleva desde cero hasta el último ticket de la etapa 1.

**Cómo leerla.** Cada paso tiene cuatro partes: qué haces (la orden exacta o el clic), para qué sirve, cómo sabes que ha ido bien y qué hacer si falla.

**Regla de oro:** una cosa cada vez. No pases al paso siguiente hasta que el actual haya ido bien.

Las órdenes son para Linux y Mac. Si usas Windows, se indica la diferencia en «Si falla».

## Palabras que vas a ver

- **Terminal:** La ventana donde escribes órdenes.
- **Repositorio (repo):** La carpeta del proyecto con todo su historial.
- **Commit:** Una foto guardada del proyecto, con un mensaje que dice qué cambió.
- **Rama:** Una copia de trabajo para un cambio; main es la versión buena.
- **Push / pull:** Subir tus commits a GitHub / bajar los de GitHub.
- **Pull request:** Propuesta para unir una rama a main, con revisión.
- **Diff:** La lista de líneas añadidas y quitadas.
- **Entorno virtual:** Caja aislada con las librerías del proyecto.
- **Prueba (test):** Un programa pequeño que comprueba que otro hace lo que debe.
- **Token / clave API:** Contraseña que usa un programa para entrar en un servicio.
- **.env:** Archivo con tus ajustes y claves. Nunca se sube.
- **Prompt:** Las instrucciones que le escribes a la IA.

## Fase 0 · Preparar el ordenador (unos 45 min, una sola vez)

Instalas y compruebas las herramientas. Si algo ya lo tienes de la fábrica de agentes, compruébalo y pasa al siguiente paso.

### 0.1 · Comprobar que tienes Python

**Qué haces:**

```
python3 --version
```

**Para qué:** El proyecto está escrito en Python y necesita la versión 3.10 o una más nueva.

**Cómo sé que ha ido bien:** Sale algo como «Python 3.12.3» (3.10 o más).

**Si falla:** Si dice «command not found», instálalo. Ubuntu: sudo apt install python3 python3-venv. Mac: brew install python. Windows: winget install Python.Python.3.12, y cierra y abre la terminal. En Windows se escribe python en vez de python3.

### 0.2 · Comprobar que tienes git

**Qué haces:**

```
git --version
```

**Para qué:** git guarda el historial de cada cambio y es lo que sube el código a GitHub.

**Cómo sé que ha ido bien:** Sale algo como «git version 2.43.0».

**Si falla:** Instálalo. Ubuntu: sudo apt install git. Mac: brew install git. Windows: winget install Git.Git.

### 0.3 · Decirle a git quién eres

**Qué haces:**

```
git config --global user.name "Ana"
git config --global user.email "el-correo-de-tu-github@ejemplo.com"
```

**Para qué:** Cada cambio guardado (commit) lleva la firma de quien lo hizo. Solo se hace una vez por ordenador.

**Cómo sé que ha ido bien:** git config --global user.name responde «Ana».

**Si falla:** Si ya lo hiciste en la fábrica, no hace falta repetirlo.

### 0.4 · Comprobar que puedes subir a GitHub

**Qué haces:**

```
gh auth status
```

**Para qué:** GitHub no acepta tu contraseña normal desde la terminal; la herramienta gh deja la sesión iniciada de forma segura.

**Cómo sé que ha ido bien:** Sale «Logged in to github.com account anawolfdev».

**Si falla:** Si gh no existe, instálalo (Ubuntu: sudo apt install gh · Mac: brew install gh · Windows: winget install GitHub.cli). Luego gh auth login y elige: GitHub.com, HTTPS, Login with a web browser.

### 0.5 · Comprobar que tienes OpenCode

**Qué haces:**

```
opencode --version
```

**Para qué:** OpenCode es el agente que escribe el código por ti, ticket a ticket.

**Cómo sé que ha ido bien:** Sale un número de versión.

**Si falla:** Instálalo con: curl -fsSL https://opencode.ai/install | bash (Linux y Mac) o npm install -g opencode-ai (Windows, con Node.js instalado).

### 0.6 · Elegir un modelo gratis en OpenCode

**Qué haces:**

```
opencode
/models
```

**Para qué:** Los modelos gratis cambian cada pocas semanas; en esa lista ves los que hay hoy.

**Cómo sé que ha ido bien:** Eliges uno que ponga «Free» y su nombre aparece en la parte de abajo de OpenCode. Para salir: Ctrl + C.

**Si falla:** Si no ves ninguno gratis, actualiza OpenCode (repite la instalación del paso 0.5) y vuelve a mirar.

### 0.7 · Tener Telegram en el móvil

**Qué haces:**

```
Instala Telegram desde la tienda del móvil y entra con tu número.
```

**Para qué:** Por Telegram te llegarán los avisos. Es gratis, funciona en móvil, ordenador y web, y se lleva bien con TalkBack y VoiceOver.

**Cómo sé que ha ido bien:** Puedes abrir Telegram y escribir a cualquier contacto.

**Si falla:** Si ya lo usas, pasa al siguiente paso.

### 0.8 · Crear tu bot con BotFather

**Qué haces:**

```
En Telegram, busca @BotFather (con la marca azul de verificado) y pulsa Iniciar.
Escribe /newbot
Nombre: Mi acompañante de salud
Usuario: uno que acabe en bot, por ejemplo ana_acompanante_salud_bot
Abre tu bot nuevo, pulsa Iniciar y escríbele «hola».
```

**Para qué:** El bot es el contacto que te mandará los avisos. BotFather te da un token, que es la contraseña del bot. Le escribes «hola» porque Telegram no deja que un bot escriba a quien no le ha hablado antes.

**Cómo sé que ha ido bien:** BotFather responde «Done! Congratulations on your new bot» y un token largo, del tipo 123456789:ABC… Guárdalo en tu gestor de contraseñas.

**Si falla:** Si dice que el usuario ya existe, prueba otro que acabe en bot. Si alguna vez se publica el token por error, en BotFather escribe /revoke y saca uno nuevo.

### 0.9 · Sacar una clave gratis de IA (Gemini)

**Qué haces:**

```
Entra en aistudio.google.com/apikey con tu cuenta de Google.
Pulsa «Create API key» y copia la clave.
```

**Para qué:** La usarán los tickets ACS-010 y ACS-011, para entender frases y fotos de los papeles. El plan gratuito no pide tarjeta.

**Cómo sé que ha ido bien:** Tienes una clave larga de letras y números guardada en tu gestor de contraseñas.

**Si falla:** Si te pide datos de pago, no los pongas: para este proyecto basta el plan gratuito. Nunca pegues la clave en el código ni en GitHub.

## Fase 1 · Crear el repositorio y subir el proyecto (unos 20 min)

El repositorio es la carpeta del proyecto en GitHub, con todo su historial.

### 1.1 · Descomprimir el paquete

**Qué haces:**

```
mkdir -p ~/proyectos
cd ~/proyectos
unzip ~/Descargas/acompanante-salud-starter.zip
```

**Para qué:** Pones el proyecto en una carpeta fija, separada de Descargas.

**Cómo sé que ha ido bien:** ls acompanante-salud enseña README.md, GUIA.md, AGENTS.md, acompanante, tests y tickets.

**Si falla:** Si el zip está en otra carpeta, cambia la ruta. Si unzip no existe: sudo apt install unzip. En Windows: botón derecho, «Extraer todo».

### 1.2 · Entrar en la carpeta del proyecto

**Qué haces:**

```
cd acompanante-salud
```

**Para qué:** Todas las órdenes siguientes se escriben desde aquí.

**Cómo sé que ha ido bien:** pwd termina en /acompanante-salud.

**Si falla:** Si dice «No such file or directory», comprueba con ls dónde se descomprimió.

### 1.3 · Crear el repositorio vacío en GitHub

**Qué haces:**

```
En el navegador: github.com/new
Owner: anawolfdev · Repository name: acompanante-salud
Público (si lo quieres enseñar en X) o Privado
NO marques «Add a README», ni .gitignore, ni licencia
Pulsa «Create repository»
```

**Para qué:** Tiene que estar vacío porque el proyecto ya trae esos archivos; si GitHub crea otros, chocan al subir. El código no lleva datos personales, así que puede ser público.

**Cómo sé que ha ido bien:** GitHub enseña la página «Quick setup» con la dirección https://github.com/anawolfdev/acompanante-salud.git

**Si falla:** Si dice que ya existe, abre el que hay: si está vacío, úsalo.

### 1.4 · Convertir la carpeta en repositorio

**Qué haces:**

```
git init -b main
```

**Para qué:** git empieza a vigilar la carpeta. main es la rama principal, la versión buena.

**Cómo sé que ha ido bien:** Sale «Initialized empty Git repository».

**Si falla:** Si no reconoce -b (git antiguo): git init y después git checkout -b main.

### 1.5 · Primer commit

**Qué haces:**

```
git add -A
git status
git commit -m "Paquete de arranque del Acompañante de salud"
```

**Para qué:** Un commit es una foto del proyecto en un momento. git status te enseña qué va a entrar antes de hacerla.

**Cómo sé que ha ido bien:** git status lista los archivos en verde y NO aparecen .env, .venv ni datos. El commit dice algo como «41 files changed».

**Si falla:** Si aparece .env en la lista, para y comprueba que existe el archivo .gitignore.

### 1.6 · Conectar con GitHub y subir

**Qué haces:**

```
git remote add origin https://github.com/anawolfdev/acompanante-salud.git
git push -u origin main
```

**Para qué:** origin es el nombre corto de tu repositorio en GitHub. push sube tus commits.

**Cómo sé que ha ido bien:** Al recargar la página de GitHub ves todos los archivos y el README.

**Si falla:** «Authentication failed»: repite el paso 0.4. «rejected (fetch first)»: el repositorio no estaba vacío; bórralo en Settings y créalo otra vez sin marcar nada.

### 1.7 · Ver las pruebas en GitHub

**Qué haces:**

```
En GitHub, pestaña «Actions»
```

**Para qué:** GitHub ejecuta las pruebas solo cada vez que subes algo: un segundo par de ojos gratis.

**Cómo sé que ha ido bien:** En 1 o 2 minutos aparece «Pruebas» con un círculo verde.

**Si falla:** Si sale una cruz roja, ábrela, copia el error y pégaselo a OpenCode, o pásamelo.

## Fase 2 · Ponerlo en marcha en tu ordenador (unos 15 min)

Comprobar que el esqueleto funciona antes de tocar nada. Si algo falla después, sabrás que fue el último cambio.

### 2.1 · Crear el entorno virtual

**Qué haces:**

```
python3 -m venv .venv
```

**Para qué:** Es una caja aislada para las librerías de este proyecto, para no mezclarlas con el resto del ordenador.

**Cómo sé que ha ido bien:** Aparece una carpeta .venv (ls -a la enseña).

**Si falla:** «ensurepip is not available»: sudo apt install python3-venv y repite.

### 2.2 · Activar el entorno

**Qué haces:**

```
source .venv/bin/activate
```

**Para qué:** A partir de aquí, python y pip usan la caja del proyecto. Hay que activarlo cada vez que abras una terminal nueva para este proyecto.

**Cómo sé que ha ido bien:** La línea de la terminal empieza por (.venv).

**Si falla:** Windows: .venv\Scripts\activate. Si dice que la ejecución de scripts está deshabilitada: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned.

### 2.3 · Instalar lo necesario

**Qué haces:**

```
pip install -r requirements-dev.txt
```

**Para qué:** Instala pytest, el programa que pasa las pruebas, y los datos de zonas horarias.

**Cómo sé que ha ido bien:** Termina con «Successfully installed …».

**Si falla:** Si falla por la red, vuelve a intentarlo. Si dice «pip: command not found», el entorno no está activado (paso 2.2).

### 2.4 · Pasar las pruebas

**Qué haces:**

```
python -m pytest
```

**Para qué:** Las pruebas comprueban solas que todo hace lo que debe. Es tu red de seguridad para cada ticket.

**Cómo sé que ha ido bien:** La última línea dice «32 passed» en verde.

**Si falla:** «No module named pytest»: activa el entorno (2.2). Si alguna falla, copia el error y pásamelo.

### 2.5 · Ver la demo

**Qué haces:**

```
python -m acompanante demo
```

**Para qué:** Apunta 3 citas de ejemplo y te enseña cómo te llegarían los avisos.

**Cómo sé que ha ido bien:** Ves las 3 citas y dos avisos de la analítica: 2 días antes y el mismo día, con la lista de preparación.

**Si falla:** Si quieres empezar de cero, borra la carpeta datos: rm -rf datos

### 2.6 · Crear tu archivo de configuración

**Qué haces:**

```
cp .env.example .env
```

**Para qué:** En .env van tus ajustes y tus claves. Está en .gitignore, así que nunca se sube a GitHub.

**Cómo sé que ha ido bien:** git status no menciona .env.

**Si falla:** Windows: copy .env.example .env

### 2.7 · Pegar tus claves en .env

**Qué haces:**

```
nano .env
TELEGRAM_TOKEN= el token del paso 0.8
IA_API_KEY= la clave del paso 0.9
Guardar: Ctrl + O, Intro. Salir: Ctrl + X
```

**Para qué:** El programa lee las claves de aquí. CANAL se queda en consola hasta el ticket ACS-002.

**Cómo sé que ha ido bien:** grep TELEGRAM_TOKEN .env enseña tu token.

**Si falla:** Sin espacios alrededor del signo =. Puedes usar cualquier editor de texto en vez de nano.

## El bucle de cada ticket

Desde la fase 3, cada fase es un ticket, y todos se hacen igual: estos 9 pasos. El ejemplo usa ACS-002; cambia el número por el de tu ticket.

### B1 · Partir de la versión buena

**Qué haces:**

```
git checkout main
git pull
```

**Para qué:** Empiezas siempre desde lo último que está bien en GitHub.

**Cómo sé que ha ido bien:** «Already up to date» o se descargan cambios.

**Si falla:** Si dice que tienes cambios sin guardar, termina o descarta el ticket anterior antes.

### B2 · Crear una rama para el ticket

**Qué haces:**

```
git checkout -b acs-002
```

**Para qué:** Una rama es una copia de trabajo. Si el ticket sale mal, main sigue intacto. Cambia el número por el del ticket.

**Cómo sé que ha ido bien:** Sale «Switched to a new branch 'acs-002'».

**Si falla:** «already exists»: usa git checkout acs-002.

### B3 · Abrir OpenCode en limpio

**Qué haces:**

```
opencode
/new
```

**Para qué:** Una conversación nueva por ticket evita que el modelo arrastre confusiones de antes.

**Cómo sé que ha ido bien:** OpenCode está abierto, con la conversación vacía.

**Si falla:** Si no abre, vuelve al paso 0.5.

### B4 · Pegar el prompt del ticket

**Qué haces:**

```
Copia el «Prompt para pegar en OpenCode» del ticket y pégalo.
```

**Para qué:** El prompt le dice qué ticket hacer, que lea las normas (AGENTS.md) y que termine con un resumen para ti.

**Cómo sé que ha ido bien:** Termina con «Qué he cambiado», «Cómo lo pruebas tú» y «Qué no he hecho».

**Si falla:** Si se lía, /undo deshace su último cambio; /new empieza de nuevo. Tras 2 intentos fallidos, prueba otro modelo gratis con /models.

### B5 · Revisar qué ha cambiado

**Qué haces:**

```
git status
git diff
```

**Para qué:** Tú eres la jefa: ves exactamente qué ha tocado antes de aceptarlo. En git diff, el verde es lo añadido y el rojo lo quitado; q para salir.

**Cómo sé que ha ido bien:** Solo cambian los archivos que menciona el ticket, más pruebas en tests/.

**Si falla:** Si ha tocado algo que no debía: pídele «Deshaz los cambios en ese archivo, no eran del ticket», o git restore nombre-del-archivo.

### B6 · Pasar las pruebas

**Qué haces:**

```
python -m pytest
```

**Para qué:** Comprueba que lo nuevo funciona y que no se ha roto nada de antes.

**Cómo sé que ha ido bien:** Todo «passed», y hay más pruebas que antes.

**Si falla:** Copia el error en rojo y pégaselo a OpenCode: «Falla esta prueba: … Arréglalo sin salirte del ticket».

### B7 · Probarlo tú

**Qué haces:**

```
Las órdenes de «Cómo lo pruebas tú» y el apartado «Qué revisa Ana» del ticket.
```

**Para qué:** Las pruebas automáticas no lo ven todo: tú compruebas que hace lo que querías, en Telegram cuando toque.

**Cómo sé que ha ido bien:** Puedes marcar todos los criterios de aceptación del ticket.

**Si falla:** Si algo no te convence, díselo a OpenCode con tus palabras y repite desde B5.

### B8 · Guardar y subir la rama

**Qué haces:**

```
git add -A
git commit -m "ACS-002: bot de Telegram"
git push -u origin acs-002
```

**Para qué:** Guardas el trabajo con un nombre claro y lo subes a GitHub en su rama.

**Cómo sé que ha ido bien:** El push termina sin errores y enseña un enlace para crear un pull request.

**Si falla:** Si git status enseña .env, NO sigas: comprueba .gitignore.

### B9 · Unir el cambio a main en GitHub

**Qué haces:**

```
En GitHub: «Compare & pull request», «Create pull request»
Espera al check verde
«Merge pull request» y «Confirm merge»
```

**Para qué:** Un pull request es una propuesta de cambio que se revisa antes de entrar en la versión buena.

**Cómo sé que ha ido bien:** El cambio se ve en la rama main de GitHub. El ticket está terminado.

**Si falla:** Si sale una cruz roja, vuelve a B6. Si GitHub habla de «conflicts», pídele ayuda a OpenCode o pásamelo.

Truco para X: al terminar cada ticket, apunta en una línea qué has aprendido. El viernes ya tienes el material para tu publicación.

## Fase 3 · ACS-001 · Primer paseo con OpenCode (practicar el bucle) (30 min)

**Para qué:** Aprender el bucle de trabajo (rama, OpenCode, revisar, pruebas, subir) con un cambio que no puede romper nada.

**Prompt para pegar en OpenCode (paso B4):**

```
Lee AGENTS.md y tickets/ACS-001-primer-paseo.md. Primero explícame en 5 frases sencillas cómo está organizado el proyecto y para qué sirve cada carpeta, sin cambiar nada. Después añade al final de README.md una sección "## Responsable" con el texto "Ana (anawolfdev)". No cambies nada más.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```

**Está terminado cuando:**

- [ ] OpenCode te ha explicado el proyecto en frases que entiendes, sin cambiar archivos en ese primer paso.
- [ ] `git diff` solo enseña las líneas nuevas del README.
- [ ] `python -m pytest` sigue en verde.
- [ ] El cambio está en la rama main de GitHub y la pestaña Actions sale en verde.

**Qué revisas tú:** Que entiendes la explicación de OpenCode y que el pull request ha entrado en main con el check verde.

Detalle completo: `tickets/ACS-001-primer-paseo.md`

## Fase 4 · ACS-002 · Crear tu bot de Telegram y mandar un mensaje de prueba (45 min)

**Para qué:** Que los avisos te lleguen al móvil. El bot ya lo creaste en la fase 0; ahora el programa aprende a escribirte.

**Prompt para pegar en OpenCode (paso B4):**

```
Lee AGENTS.md y tickets/ACS-002-bot-telegram.md. Haz solo la parte de OpenCode de este ticket: las órdenes mi-chat y probar-telegram, con sus pruebas. No uses librerías nuevas, usa urllib como en notificador.py.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```

**Está terminado cuando:**

- [ ] Con el token puesto, `mi-chat` enseña tu número de chat.
- [ ] `probar-telegram` hace que te llegue el mensaje de saludo al móvil.
- [ ] Si falta el token, sale un mensaje claro que dice qué falta y dónde ponerlo (sin errores en inglés).
- [ ] Con `CANAL=telegram`, `python -m acompanante avisos --ahora "…"` manda el aviso a Telegram.
- [ ] Todas las pruebas pasan.

**Qué revisas tú:** Que te llega el saludo al móvil y que, con el lector de pantalla del móvil, el aviso de la demo se entiende bien.

Detalle completo: `tickets/ACS-002-bot-telegram.md`

## Fase 5 · ACS-003 · Que los avisos salgan solos (1 h)

**Para qué:** Ahora hay que escribir `avisos` a mano. Con esto, el programa se queda encendido y revisa cada pocos minutos.

**Prompt para pegar en OpenCode (paso B4):**

```
Lee AGENTS.md y tickets/ACS-003-avisos-automaticos.md. Haz solo este ticket. La función de espera tiene que poder cambiarse en las pruebas para que no tarden.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```

**Está terminado cuando:**

- [ ] Con `vigilar` encendido, un aviso que toca en los próximos minutos llega solo a Telegram.
- [ ] No llega dos veces el mismo aviso.
- [ ] Control + C lo para con un mensaje de despedida, sin errores en pantalla.
- [ ] Todas las pruebas pasan.

**Qué revisas tú:** Apunta una cita para dentro de 2 días y 5 minutos, deja `vigilar` encendido y comprueba que te llega el aviso.

Detalle completo: `tickets/ACS-003-avisos-automaticos.md`

## Fase 6 · ACS-004 · Cambiar y borrar citas (1 h)

**Para qué:** Las citas cambian: te la mueven de día o la anulas.

**Prompt para pegar en OpenCode (paso B4):**

```
Lee AGENTS.md y tickets/ACS-004-editar-borrar-citas.md. Haz solo este ticket.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```

**Está terminado cuando:**

- [ ] Borrar pide confirmación y, tras decir que sí, la cita ya no sale en `citas`.
- [ ] Cambiar la hora de una cita hace que el aviso vuelva a salir con la hora nueva.
- [ ] Un ID que no existe da un mensaje claro: "No hay ninguna cita con el número 7".
- [ ] Todas las pruebas pasan.

**Qué revisas tú:** Que borrar pide confirmación y que, al cambiar una cita de día, el aviso sale con el día nuevo (pruébalo con `avisos --simular --ahora`).

Detalle completo: `tickets/ACS-004-editar-borrar-citas.md`

## Fase 7 · ACS-005 · Lista de preparación sugerida según el tipo de cita (45 min)

**Para qué:** Para no tener que acordarte de qué llevar: si es una analítica, te sugiere ayunas, muestra de orina y volante.

**Prompt para pegar en OpenCode (paso B4):**

```
Lee AGENTS.md y tickets/ACS-005-preparacion-por-tipo.md. Haz solo este ticket.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```

**Está terminado cuando:**

- [ ] Una analítica nueva sin --preparar sale con la lista de analítica en el aviso.
- [ ] Si escribes tu propio --preparar, se usa el tuyo y no la sugerencia.
- [ ] Todas las pruebas pasan.

**Qué revisas tú:** Que las frases de cada lista son las que tú usarías y están en un español claro. Cámbialas a tu gusto en plantillas.py.

Detalle completo: `tickets/ACS-005-preparacion-por-tipo.md`

## Fase 8 · ACS-006 · Aviso la noche antes si hay que ir en ayunas (45 min)

**Para qué:** Si la analítica es a las 8:30, el aviso de las 7:30 llega tarde para el ayuno. Hace falta uno la noche anterior.

**Prompt para pegar en OpenCode (paso B4):**

```
Lee AGENTS.md y tickets/ACS-006-aviso-ayunas.md. Haz solo este ticket. Sigue el mismo estilo que los avisos 'previo' y 'dia' de recordatorios.py.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```

**Está terminado cuando:**

- [ ] Una analítica con "ayunas" a las 8:30 da 3 avisos: 2 días antes, la noche antes a las 21:00 y el mismo día.
- [ ] Una vacuna no tiene aviso la noche antes.
- [ ] Todas las pruebas pasan.

**Qué revisas tú:** Que el mensaje de la noche anterior es claro y llega a una hora que te viene bien.

Detalle completo: `tickets/ACS-006-aviso-ayunas.md`

## Fase 9 · ACS-007 · Recordatorios que se repiten (como tomarse la tensión) (1 h 30 min)

**Para qué:** Las cosas de cada semana: "tómate la tensión el lunes a las 9:00".

**Prompt para pegar en OpenCode (paso B4):**

```
Lee AGENTS.md y tickets/ACS-007-recordatorios-que-se-repiten.md. Haz solo este ticket. Las tareas se apuntan como enviadas igual que las citas, para no repetirse.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```

**Está terminado cuando:**

- [ ] Una tarea de los lunes a las 9:00 avisa el lunes a las 9:00 y no se repite ese día.
- [ ] Una tarea pausada no avisa.
- [ ] Todas las pruebas pasan.

**Qué revisas tú:** Crea tu tarea real de la tensión y comprueba con `avisos --simular --ahora` que sale el día y la hora correctos.

Detalle completo: `tickets/ACS-007-recordatorios-que-se-repiten.md`

## Fase 10 · ACS-008 · Apuntar la tensión (1 h)

**Para qué:** Guardar cada toma de tensión para llevarla al médico, en vez de un papel.

**Prompt para pegar en OpenCode (paso B4):**

```
Lee AGENTS.md y tickets/ACS-008-apuntar-tension.md. Haz solo este ticket. Recuerda: la aplicación no interpreta valores médicos.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```

**Está terminado cuando:**

- [ ] Una toma guardada sale en el historial con fecha y valores.
- [ ] El historial se entiende leído en voz alta.
- [ ] Todas las pruebas pasan.

**Qué revisas tú:** Que el historial se oye bien con el lector de pantalla y que sirve para enseñárselo al médico.

Detalle completo: `tickets/ACS-008-apuntar-tension.md`

## Fase 11 · ACS-009 · Hablar con el bot desde Telegram (2 h)

**Para qué:** Usarlo desde el móvil sin abrir el ordenador: preguntar qué citas tienes o apuntar la tensión.

**Prompt para pegar en OpenCode (paso B4):**

```
Lee AGENTS.md y tickets/ACS-009-hablar-con-el-bot.md. Haz solo este ticket. Separa la parte que entiende el mensaje (fácil de probar) de la parte que habla con Telegram.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```

**Está terminado cuando:**

- [ ] Desde el móvil, /proximas responde con tus citas.
- [ ] /tension guarda la toma y sale después en `historial-tension`.
- [ ] Un mensaje desde otra cuenta de Telegram no recibe respuesta.
- [ ] Todas las pruebas pasan.

**Qué revisas tú:** Que puedes usar /proximas y /tension desde el móvil con el lector de pantalla, y que a otra cuenta no le contesta.

Detalle completo: `tickets/ACS-009-hablar-con-el-bot.md`

## Fase 12 · ACS-010 · Apuntar una cita escribiendo una frase normal (con IA gratis) (2 h)

**Para qué:** Escribir "analítica el 12 de noviembre a las 8:30 en el centro de salud, en ayunas" y que se apunte sola.

**Prompt para pegar en OpenCode (paso B4):**

```
Lee AGENTS.md y tickets/ACS-010-cita-desde-una-frase.md. Haz solo este ticket. Usa ia.py; no llames a Gemini directamente.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```

**Está terminado cuando:**

- [ ] Con la frase de ejemplo, el bot propone la cita con fecha, hora, lugar y preparación correctas.
- [ ] No se guarda nada sin un "sí".
- [ ] Las pruebas usan una IA falsa (sin Internet) y pasan.

**Qué revisas tú:** Prueba 5 frases distintas, como las dirías tú, y apunta en cuáles se equivoca.

Detalle completo: `tickets/ACS-010-cita-desde-una-frase.md`

## Fase 13 · ACS-011 · Foto del papel de la cita (2 h)

**Para qué:** Hacer una foto al papel de la cita o al volante y que el bot apunte fecha, hora, lugar y qué preparar.

**Prompt para pegar en OpenCode (paso B4):**

```
Lee AGENTS.md y tickets/ACS-011-foto-del-papel.md. Haz solo este ticket. Reutiliza la función de ACS-010.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```

**Está terminado cuando:**

- [ ] Con la foto de un papel de cita (de ejemplo, sin datos reales), el bot propone la cita correcta.
- [ ] No se guarda nada sin un "sí".
- [ ] Todas las pruebas pasan.

**Qué revisas tú:** Prueba con 3 papeles (tapa tus datos personales) y comprueba que la fecha y la hora están bien antes de decir que sí.

Detalle completo: `tickets/ACS-011-foto-del-papel.md`

## Fase 14 · ACS-012 · Revisión de accesibilidad y demo (1 h 30 min)

**Para qué:** Comprobar que lo usa bien una persona ciega o con poca visión, y preparar una demo de 2 minutos.

**Prompt para pegar en OpenCode (paso B4):**

```
Lee AGENTS.md, tickets/ACS-012-accesibilidad-y-demo.md y docs/accesibilidad.md. Corrige las frases que aparecen como difíciles de entender. No cambies nada más.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```

**Está terminado cuando:**

- [ ] Todos los mensajes se entienden escuchados, sin mirar la pantalla.
- [ ] El guion de demo funciona de principio a fin.
- [ ] Todas las pruebas pasan.

**Qué revisas tú:** Que tu padre (o alguien con lector de pantalla) entiende los avisos sin ayuda.

Detalle completo: `tickets/ACS-012-accesibilidad-y-demo.md`
