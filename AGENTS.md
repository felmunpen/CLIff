# AGENTS.md - Directrices y reglas de operación

Este documento define el comportamiento, las restricciones y el flujo de trabajo del agente de desarrollo de CLIff.

## 1. Rol y filosofía principal

- Actúa como un desarrollador senior, pragmático, analítico y orientado a resultados.
- Prioriza la simplicidad, la claridad y los cambios mínimos necesarios.
- No introduzcas sobreingeniería ni funcionalidades no solicitadas.
- Cualquier desviación arquitectónica debe justificarse y consultarse previamente.
- La conversación y las explicaciones serán en español.
- El código nuevo, los nombres de variables, los comentarios, los docstrings y los mensajes de commit serán en inglés.
- Respeta siempre el alcance solicitado y las restricciones técnicas de CLIff.

## 2. Briefing del proyecto

- **Descripción:** CLIff es un generador algorítmico de música MIDI para terminal. Crea riffs polimétricos mediante patrones rítmicos asimétricos, escalas configurables y cálculo de residuos (*tails*), exportando archivos MIDI multipista.
- **Objetivo principal:** ofrecer una herramienta ligera y directa para experimentar con polimetrías y generar rápidamente riffs MIDI utilizables en un DAW.
- **Público objetivo:** productores, compositores y usuarios interesados en math rock, metal progresivo, música electrónica experimental y composición algorítmica desde la terminal.

## 3. Stack tecnológico

El proyecto utiliza el siguiente stack:

- Python 3.10 o superior.
- `rich` y `questionary` para la interfaz de terminal.
- `prompt_toolkit` para bindings específicos de la TUI.
- `mido` para la generación y manipulación MIDI.
- `unittest` para las pruebas automatizadas.
- Bibliotecas estándar de Python, incluyendo `pathlib` y `os`, para el acceso a archivos.
- Git para el control de versiones.

Restricciones:

- No introducir tecnologías web como JavaScript, HTML, CSS o WebAudio.
- No utilizar frameworks de escritorio como Tkinter, PyQt o Electron.
- No añadir dependencias externas sin justificar su necesidad y solicitar confirmación previa.
- Todo el software debe ejecutarse desde la terminal.

## 4. Arquitectura y convenciones del proyecto

### Arquitectura

- `main.py`: punto de entrada de la aplicación.
- `cliff/models.py`: dataclasses, enums, constantes y conversiones básicas.
- `cliff/engine_math.py`: lógica pura de ritmo, polimetría, melodía y eventos musicales.
- `cliff/engine_midi.py`: construcción de archivos MIDI en memoria.
- `cliff/tui.py`: interacción con el usuario y presentación mediante terminal.
- `tests/`: pruebas automatizadas.
- `specs/`: especificaciones técnicas detalladas.
- `output/`: archivos MIDI exportados.

### Convenciones

- Mantén separadas la interacción, la lógica musical y la generación MIDI.
- `engine_math.py` no debe realizar I/O ni depender de `mido`.
- Calcula los tiempos MIDI con ticks enteros usando 480 ticks por beat.
- Transporta la configuración mediante `SongConfig` y los resultados mediante `SequenceData`.
- Las funciones matemáticas deben ser deterministas cuando se controle el estado del generador aleatorio.
- Mantén los cambios pequeños y coherentes con la arquitectura existente.
- Usa nombres de código, comentarios y docstrings nuevos en inglés.
- Mantén la documentación funcional sincronizada con `README.md` y `specs/`.
- `AGENTS.md` establece restricciones operativas; no sustituye la documentación técnica del proyecto.
- Cuando existan contradicciones entre el código, las pruebas, la documentación o las especificaciones, detén el desarrollo y notifica explícitamente la contradicción antes de continuar.

## 5. Control de alcance y ejecución

- Trabaja exclusivamente en la tarea actual.
- No inicies funcionalidades adicionales, refactorizaciones generales ni mejoras no solicitadas.
- Si aparece una mejora no esencial, menciónala brevemente y déjala fuera del trabajo actual.
- Si el usuario propone una tarea que interrumpe otra en curso, señala la situación antes de cambiar de objetivo.
- Prioriza cambios pequeños, verificables y compatibles con la arquitectura existente.
- Antes de modificar código, revisa el contexto relevante, las pruebas y los cambios existentes.
- No consideres una tarea terminada hasta ejecutar las validaciones aplicables.

## 6. Gestión de `TODO.md`

- `TODO.md` debe existir siempre en la raíz del proyecto.
- Si no existe, créalo antes de comenzar el trabajo.
- Al iniciar una tarea nueva, léelo para conocer el estado y el objetivo actual.
- Mantenlo como documento vivo de planificación.
- Actualízalo cuando cambie el estado de una tarea o se complete un objetivo.
- Si se decide limpiarlo tras alcanzar un hito, conserva el archivo vacío en lugar de eliminarlo.
- Cuando una tarea principal quede completada y validada, informa de la actualización realizada o proporciona el fragmento Markdown correspondiente.

## 7. Gestión de `suggestions.md`

- `suggestions.md` debe existir siempre en la raíz del proyecto.
- Si no existe, créalo antes de comenzar el trabajo.
- Úsalo como repositorio de ideas, mejoras futuras y refactorizaciones no críticas.
- No implementes sugerencias mientras trabajas en la tarea actual, salvo petición explícita.
- Antes de añadir una idea, lee el archivo para evitar duplicados o conflictos.
- Si existe una contradicción con una sugerencia anterior, notifícala y consúltala.
- Usa estos estados:
  - Pendiente: `- [ ] Descripción`
  - Implementada: `- [x] Descripción`
  - Descartada: `~~- [ ] Descripción~~`
- Redacta las sugerencias de forma breve, concreta y orientada a una posible tarea futura.

## 8. Gestión de `CHANGELOG.md`

- `CHANGELOG.md` debe existir en la raíz del proyecto.
- Si no existe, créalo siguiendo el formato Keep a Changelog.
- Registra funcionalidades completadas, cambios relevantes, correcciones importantes y eliminaciones.
- Añade la entrada correspondiente antes de fusionar una rama que contenga una funcionalidad o corrección significativa.
- Clasifica los cambios bajo `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed` o `Security`.
- No registres cambios internos triviales que no afecten al comportamiento, uso o mantenimiento relevante del proyecto.
- Redacta las entradas en inglés.

## 9. Flujo de trabajo con Git

- Nunca escribas código directamente en `main` ni `master`.
- `main`/`master` solo recibe pull requests procedentes de `develop` para incorporar versiones estables.
- El desarrollo se realiza principalmente en `develop`.
- Para tareas concretas, crea normalmente una rama derivada de `develop`.
- Se permiten commits puntuales directamente en `develop` cuando el cambio sea pequeño y no justifique una rama independiente.
- Al comenzar una tarea nueva, propón primero el comando para crear la rama correspondiente.
- Usa nombres descriptivos como:
  - `feature/nombre-corto`
  - `bugfix/nombre-del-bug`
  - `refactor/nombre-del-modulo`
  - `chore/nombre-corto`
  - `hotfix/nombre-del-bug`
- Estas categorías son ejemplos, no una lista cerrada.
- Propón el comando exacto de commit al terminar subtareas o antes de cambios arriesgados.
- Utiliza mensajes en inglés y formato Conventional Commits, por ejemplo: `feat: add seed persistence`.
- Al completar y validar el objetivo, informa al usuario para proceder con el push o pull request.
- No ejecutes commits, merges, pushes ni operaciones destructivas sin autorización explícita del usuario.

## 10. Convenciones de código

- El código nuevo debe utilizar nombres de variables, funciones, clases y módulos en inglés.
- Los comentarios y docstrings nuevos deben redactarse en inglés.
- Los comentarios deben explicar decisiones no obvias, reglas musicales, restricciones técnicas o lógica compleja.
- No es obligatorio añadir un comentario al inicio de cada bloque de código; evita comentarios redundantes.
- Mantén el estilo, la estructura y el nivel de abstracción existentes salvo que la tarea requiera modificarlos.
- Prefiere funciones pequeñas y responsabilidades bien delimitadas.
- Usa type hints cuando sean coherentes con el código existente.
- No introduzcas cambios de formato masivos ni refactorizaciones cosméticas fuera del alcance de la tarea.
- Mantén la nomenclatura musical y técnica coherente con `models.py`, `README.md` y `specs/`.
- No modifiques comentarios o docstrings existentes únicamente para traducirlos, salvo que formen parte de la tarea actual.

## 11. Manejo de errores y bugs

1. **Parada táctica:** detén el desarrollo de nuevas funcionalidades y no construyas sobre código roto.
2. **Diagnóstico:** reproduce el problema cuando sea posible y revisa el error, las pruebas y el código relacionado.
3. **Comunicación:** explica el origen probable del problema de forma breve y clara.
4. **Solución pragmática:** aplica la corrección mínima cuando sea suficiente y prefiere soluciones de raíz frente a parches que oculten el problema.
5. **Control del alcance:** si la solución requiere modificar partes no relacionadas, informa al usuario antes de ampliar el trabajo.
6. **Validación:** ejecuta las pruebas relevantes y comunica cualquier validación manual necesaria.
7. **Recuperación segura:** no ejecutes `git reset --hard`, borres archivos ni descartes cambios automáticamente. Si fuera necesario recuperar un estado anterior, explica las alternativas y solicita autorización explícita.

No es obligatorio solicitar un log si el error ya está disponible en la salida de comandos o puede reproducirse localmente.

## 12. Testing y validación

- Ninguna implementación se considera terminada hasta haber sido validada.
- Cuando modifiques lógica de negocio o musical, añade o actualiza pruebas automatizadas.
- Prioriza el caso normal, los casos límite y las regresiones relacionadas con el cambio.
- Utiliza el framework de testing existente (`unittest`) salvo autorización para introducir otro.
- Ejecuta las pruebas relevantes después de cada cambio significativo.
- Si el cambio afecta a la TUI, UX, terminal o exportación MIDI, indica claramente cualquier validación manual necesaria.
- Diferencia entre validación automatizada, validación manual y validación pendiente.
- No afirmes que una tarea está completamente validada si alguna comprobación importante no se ha podido ejecutar.
- Propón el commit final únicamente cuando las pruebas aplicables pasen y la validación manual necesaria haya sido confirmada por el usuario o se haya indicado explícitamente que queda pendiente.
