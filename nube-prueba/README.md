# Prueba de conexión en la nube (ACS-018A)

Esta carpeta guarda una prueba pequeña hecha en Cloudflare para comprobar si la nube puede enviar un aviso a Telegram con el Mac en reposo.

No es el bot completo. Solo sirve para validar la conexión entre la nube y Telegram con datos de mentira.

## Qué hay en esta carpeta

- `worker.js`: Worker de Cloudflare que lee citas de prueba de D1 y manda un aviso a Telegram.
- `schema.sql`: tablas y datos de mentira para la base D1.
- `wrangler.jsonc`: configuración del Worker y el enlace con la base D1. No declara activadores cron.

## Qué se probó y qué resultado dio

- Se creó la base D1 `salud-prueba` seleccionando jurisdicción Unión Europea, con dos citas ficticias.
- Se desplegó `acompanante-prueba` y se vinculó la base como `DB`.
- Los secretos (`TELEGRAM_TOKEN` y `TELEGRAM_CHAT_ID`) se guardaron directamente en Cloudflare, nunca en el código ni en estos archivos.
- Se recibieron dos mensajes en Telegram con el Mac en reposo. Esto valida la conexión nube-Telegram.
- Esto **no** demuestra que el bot completo esté migrado ni que los recordatorios lleguen a su hora.

## Límites y comportamiento del Worker

- El Worker reserva cada intento antes de llamar a Telegram: inserta una fila en la tabla `envios` y solo permite enviar en los primeros seis intentos totales.
- Si Telegram falla, ese intento ya se ha reservado y se consume. Es mejor mandar de menos que de más en una prueba.
- Después del límite, el Worker puede seguir escribiendo filas en `envios` si se deja el cron activo, pero no debe mandar más mensajes a Telegram.

## Activador (cron)

- Se eliminó el activador de cada cinco minutos y se comprobó en el panel que no quedaban activadores configurados.
- Añadir o borrar activadores puede tardar hasta quince minutos en propagarse.
- La configuración de esta carpeta se mantiene sin activadores cron a propósito, para que desplegar el repositorio no reactive envíos sin aviso.

## Qué no se ha probado

- Datos reales de personas que prueben el acompañante.
- Aislamiento entre personas usuarias (multiusuario).
- Rendimiento del bot completo.

## Cómo repetir la prueba con datos ficticios

No ejecutes estos pasos ahora si no hace falta. Sirven para repetir la prueba más adelante.

1. Comprueba que en Cloudflare existen la base D1 `salud-prueba` y el Worker `acompanante-prueba`, con los secretos guardados en Cloudflare (no en el código).
2. Si hace falta, carga el esquema y los datos de mentira en la base D1 usando `schema.sql`.
3. Revisa cuántos intentos hay ya en la tabla `envios` (ver el apartado siguiente). Si el contador ya llegó al límite, la prueba no enviará mensajes nuevos.
4. Añade a mano un activador en el panel de Cloudflare (Eventos de activación), solo para la prueba. Ten en cuenta que puede tardar hasta quince minutos en activarse.
5. Espera a que llegue un mensaje de prueba a Telegram. El mensaje debe indicar datos de mentira.
6. Cuando termines, retira el activador (ver más abajo) y comprueba en el panel que no queda ninguno configurado.

## Si el contador ya ha consumido los seis intentos

El límite se cuenta por filas en la tabla `envios`. Cada ejecución reserva un intento antes de llamar a Telegram, así que un fallo también consume intento.

- Si ya hay seis intentos o más, el Worker no enviará mensajes nuevos a Telegram.
- Si el cron sigue activo después del límite, el Worker puede seguir añadiendo filas en `envios`, pero no debe mandar más mensajes.
- Para volver a probar envíos reales, hay que preparar de nuevo la tabla `envios` en la base de prueba con datos ficticios desde Cloudflare, teniendo cuidado de no tocar datos reales. No lo hagas desde este repositorio ni guardes secretos aquí.

## Cómo retirar el cron al terminar

1. Entra en el panel de Cloudflare, en el Worker `acompanante-prueba`.
2. Ve a la sección de eventos de activación (cron/activadores).
3. Elimina el activador usado para la prueba.
4. Comprueba que no queda ningún activador configurado.
5. Espera hasta quince minutos por si el cambio tarda en propagarse, y confirma que no llegan más mensajes de prueba.

Esta carpeta debe seguir sin activadores cron en `wrangler.jsonc`.
