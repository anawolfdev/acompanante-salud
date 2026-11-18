# ACS-018A · Prueba de conexión nube-Telegram con el Mac en reposo

**Tiempo estimado:** — (sin registrar)  
**Tamaño:** pequeño  
**Antes hace falta:** ninguno

## Para qué sirve

Guardar y documentar una prueba pequeña hecha en Cloudflare. La prueba comprueba si la nube puede mandar un aviso a Telegram con datos de mentira, con el Mac en reposo.

No migra el bot completo ni cambia el bot actual.

## Qué se ha guardado

1. Se han copiado sin modificar a `nube-prueba/` estos archivos de la prueba:
   - `worker.js`
   - `schema.sql`
   - `wrangler.jsonc`
2. Se ha creado `nube-prueba/README.md` con la explicación de la prueba, sus límites y cómo repetirla o retirarla.
3. Se han añadido pruebas automáticas sin conexión a Internet para revisar el esquema, la configuración y el comportamiento simulado del Worker.
4. Se ha añadido este ticket a la tabla de `tickets/README.md`.

## Hechos documentados de la prueba

- Se creó la base D1 `salud-prueba` seleccionando jurisdicción Unión Europea, con dos citas ficticias.
- Se desplegó `acompanante-prueba` y se vinculó la base como `DB`. Los secretos se guardaron directamente en Cloudflare, nunca en el código.
- Se recibieron dos mensajes en Telegram con el Mac en reposo. Esto valida la conexión nube-Telegram. No demuestra que el bot completo esté migrado ni que los recordatorios lleguen a su hora.
- El Worker reserva cada intento antes de llamar a Telegram y solo permite enviar en los primeros seis intentos totales. Un fallo consume un intento. Después del límite puede seguir escribiendo filas si se deja el cron activo.
- Se eliminó el activador de cada cinco minutos y se comprobó en el panel que no quedaban activadores configurados. Añadirlos o borrarlos puede tardar hasta quince minutos en propagarse.
- No se han probado datos reales de testers, aislamiento multiusuario ni rendimiento del bot completo.

## Criterios de aceptación (cuándo está terminado)

- [ ] `nube-prueba/worker.js`, `nube-prueba/schema.sql` y `nube-prueba/wrangler.jsonc` están copiados sin modificar su contenido.
- [ ] `nube-prueba/README.md` explica la prueba, sus límites, cómo repetirla con datos ficticios, qué pasa si se consumen los seis intentos y cómo retirar el cron.
- [ ] La configuración se mantiene sin activadores cron.
- [ ] Hay pruebas offline del esquema (idempotencia), de la configuración sin cron y, si el entorno lo permite, del Worker con base y Telegram simulados.
- [ ] Las pruebas nuevas y la suite completa pasan sin llamadas reales a Telegram ni a Cloudflare.
- [ ] `tickets/README.md` incluye una fila para ACS-018A con la descripción acotada.
- [ ] No se han tocado `.env`, `docs/guion-demo.md` ni `adjuntos-18a/`.

## Qué revisa Ana

Que la carpeta `nube-prueba/` y el ticket dejen claro qué se probó de verdad, qué no se probó todavía y cómo dejar la prueba apagada. También que no haya secretos ni activadores cron en los archivos guardados.
