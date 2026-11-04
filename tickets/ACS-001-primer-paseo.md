# ACS-001 · Primer paseo con OpenCode (practicar el bucle)

**Tiempo estimado:** 30 min  
**Tamaño:** muy pequeño  
**Antes hace falta:** fases 0, 1 y 2 de la GUIA.md

## Para qué sirve

Aprender el bucle de trabajo (rama, OpenCode, revisar, pruebas, subir) con un cambio que no puede romper nada.

## Qué hay que hacer

1. Sigue el bucle de la GUIA.md con la rama `acs-001`.
2. OpenCode primero te explica el proyecto sin tocar nada.
3. Después añade al final del README una sección "Responsable" con tu nombre.
4. Revisa el cambio con `git diff`, pasa las pruebas y súbelo con un pull request.

## Criterios de aceptación (cuándo está terminado)

- [ ] OpenCode te ha explicado el proyecto en frases que entiendes, sin cambiar archivos en ese primer paso.
- [ ] `git diff` solo enseña las líneas nuevas del README.
- [ ] `python -m pytest` sigue en verde.
- [ ] El cambio está en la rama main de GitHub y la pestaña Actions sale en verde.

## Qué revisa Ana

Que entiendes la explicación de OpenCode y que el pull request ha entrado en main con el check verde.

## Prompt para pegar en OpenCode

```
Lee AGENTS.md y tickets/ACS-001-primer-paseo.md. Primero explícame en 5 frases sencillas cómo está organizado el proyecto y para qué sirve cada carpeta, sin cambiar nada. Después añade al final de README.md una sección "## Responsable" con el texto "Ana (anawolfdev)". No cambies nada más.
Cuando termines, ejecuta python -m pytest y dime en español sencillo: qué has cambiado, cómo lo pruebo yo y qué no has hecho.
```
