# ACS-017 · Medicación e historial de salud

**Tiempo estimado:** 2 h  
**Tamaño:** mediano  
**Antes hace falta:** ACS-016

## Para qué sirve

Tener en el mismo sitio los medicamentos y el historial de salud. Así se puede
consultar qué se toma y qué ha pasado en las revisiones, sin buscar papeles.

También separar las tomas de tensión en su propia orden, porque el historial
ahora sirve para apuntar cualquier cosa de salud.

## Qué hay que hacer

1. Crear la tabla `medicaciones` en `db.py` con el nombre, la dosis, la pauta y
   si está activa. Añadir las funciones para guardar, listar, cambiar y borrar.
2. Crear la tabla `historial` en `db.py` con la descripción y la fecha. Añadir
   las funciones para guardar, listar, cambiar y borrar.
3. Añadir el comando `medicacion`. Enseña solo los medicamentos activos. Cada
   medicamento va en su propio mensaje y debajo lleva los botones "Modificar" y
   "Borrar", igual que las citas y las tomas de tensión.
4. Añadir `medicacion añadir` con un paso a paso: primero el nombre, después la
   dosis y por último la pauta. Al terminar, enseñar el medicamento guardado.
5. Si se pulsa "Modificar" en un medicamento, preguntar el nombre, la dosis y la
   pauta uno a uno. En cada paso se puede escribir "no" para dejar ese dato como
   estaba.
6. Si se pulsa "Borrar" en un medicamento, preguntar antes "¿Lo borro?" con los
   botones "Sí" y "No". Solo borrar cuando la persona responde que sí.
7. Convertir `historial` en el registro general de salud: analíticas, notas del
   médico, diagnósticos y cualquier cosa parecida.
8. Añadir `historial añadir` con un paso a paso: primero la descripción y
   después la fecha. La fecha es opcional: si se escribe "hoy", "no" o se deja
   vacía, se usa el día de hoy.
9. `historial` enseña las entradas de la más nueva a la más antigua. Cada
   entrada va en su propio mensaje, con los botones "Modificar" y "Borrar".
10. Si se pulsa "Modificar" en una entrada, preguntar la descripción y la fecha.
    En cada paso se puede escribir "no" para dejar ese dato como estaba.
11. Si se pulsa "Borrar" en una entrada, pedir confirmación con los botones "Sí"
    y "No". Solo borrar cuando la persona responde que sí.
12. Mover el historial de tomas de tensión al comando `tensiones`. Ese comando
    mantiene los mismos botones "Modificar" y "Borrar" de cada toma.
13. Si no hay medicamentos o entradas, decirlo con un mensaje claro y recordar
    cómo apuntar uno nuevo (`medicacion añadir` o `historial añadir`).
14. Actualizar el texto de `ayuda` y el menú de comandos de Telegram con
    `medicacion`, `medicacion añadir`, `historial` e `historial añadir`, además
    de `tensiones`.
15. Añadir pruebas con datos ficticios. No usar datos reales ni tocar el archivo
    `.env`.

## Criterios de aceptación (cuándo está terminado)

- [ ] `medicacion` enseña los medicamentos activos, cada uno en su mensaje.
- [ ] Cada medicamento lleva debajo los botones "Modificar" y "Borrar".
- [ ] `medicacion añadir` pide el nombre, la dosis y la pauta, y guarda al final.
- [ ] "Modificar" deja cambiar cualquier dato y "no" conserva el que había.
- [ ] "Borrar" pide confirmación y solo borra al responder que sí.
- [ ] `historial` guarda analíticas, notas del médico y diagnósticos.
- [ ] `historial añadir` pide la descripción y una fecha opcional.
- [ ] Sin fecha, la entrada se guarda con el día de hoy.
- [ ] `historial` enseña las entradas de la más nueva a la más antigua.
- [ ] Cada entrada lleva debajo los botones "Modificar" y "Borrar".
- [ ] "Modificar" y "Borrar" de una entrada funcionan igual que en los
      medicamentos.
- [ ] Las tomas de tensión se ven con `tensiones`, con sus mismos botones.
- [ ] Si no hay medicamentos o entradas, se explica cómo apuntar uno nuevo.
- [ ] La ayuda y el menú de Telegram incluyen los comandos nuevos.
- [ ] Todas las pruebas pasan.

## Qué revisa Ana

Que en Telegram cada medicamento y cada entrada del historial llega en su propio
mensaje, con sus botones justo debajo. Que "Modificar" y "Borrar" preguntan lo
que falta antes de tocar nada. También que las tomas de tensión siguen a mano en
`tensiones` y que todo se entiende escuchado con el lector de pantalla.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md y tickets/ACS-017-medicacion-e-historial.md. Haz solo este ticket.
Convierte historial en el registro general de salud y añade los comandos
medicacion, medicacion añadir, historial añadir y tensiones. Mantén los mismos
botones y mensajes que en citas y tomas de tensión.
No toques .env ni uses datos reales.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has
cambiado, cómo lo pruebo yo y qué no he hecho.
```
