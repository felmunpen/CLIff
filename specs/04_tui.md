# Spec 04: Interfaz TUI y Flujo de Usuario

## 1. Módulo `cliff/tui.py`

### 1.0 Estética / Tema

- **Estilo retro "fósforo verde":** el texto y la marca se muestran en verde fósforo
  suavizado `#33ff33`; las alertas y avisos (`warn`) en ámbar.
- **`Theme` propio** (`cliff.brand/accent/muted/warn/ok/info/value`):
  - `brand` y `accent`: verde `#33ff33` (bold para los acentos).
  - `warn`: ámbar.
  - `info`: teal `#5fd7d7` (acento secundario: despedida y textos de progreso).
  - `value`: verde suave `#d8ffd8` (valores de datos, para evitar blanco puro).
  - `muted`: atenuado (dim).
  - `ok`: verde (estado correcto).
- **Alineación:** todo el texto se muestra pegado a la izquierda (alineación por defecto),
  sin centrados (incluidos los títulos y captions de las tablas, `title_justify="left"`).
- **`questionary`:** la paleta se replica en sus estilos (prompt_toolkit) para que prompts,
  selects y checkboxes usen el mismo verde; si no, quedarían en blanco por defecto.
  El `qmark` de cada pregunta es un cuadrado relleno `■` en verde.

### 1.1 Pantallas y Pasos Interactivos (`questionary`)

1. **Header:** Logo **CLIff** en texto plano (subtítulo, motivo y tagline), sin `Panel`,
   alineado a la izquierda y en verde (`cliff.brand`). Es la **pantalla de inicio**: espera
   `Enter` para continuar (`Ctrl+C` o `Ctrl+G` salen). A partir de ahí, cada sección se
   muestra tras un **clear** con un **header compacto** (`CLIff` + ayuda) persistente arriba.
   Cada sección se titula con un texto en
   **bold** ("Configuración Global", "Estructura", "Reglas Algorítmicas", "Mezclador",
   "Lote") con su índice de paginación (`[N/5]`, p. ej. `Reglas Algorítmicas [3/5]`),
   seguido de un **subrayado** de la misma longitud (`─` en `dim`).
2. **Paso 1: Configuración Global**
   - `bpm`: Entero (40–240, default 120).
   - Se muestra el compás actual (`4/4`, fijo en el MVP) antes de pedir los compases.
   - `total_bars`: Entero (4–64, default 4).
   - Se muestra la multiplicación `total_bars × BEATS_PER_BAR = beats por estructura`.
3. **Paso 2: Polimetría y Pad**
   - `pattern_beats`: Flotante/Entero (ej. 3, 5, 7, 9.5). **Validado** como múltiplo de la menor duración permitida (0.25).
   - `tail_vary`: Confirm y/n "¿Variar la melodía del tail? (mismos tiempos, otros pitches)" (default Sí), mostrado justo después de `pattern_beats` y antes del diagrama de bloques.
   - `repetitions` ("Número de loops"): Entero (1–8, default 2). Nº de veces que se repite la estructura completa (ciclos completos + tail) para observar el truncamiento.
   - `intro`: Confirm y/n "¿Intro de 4 golpes de hi-hat?" (default No) — count-in antes de la pieza.
   - `pad_breath_bars`: Entero (`0` = Drone Infinito, `1-8` = re-disparo).
   - `pad_mode`: Select (`Mono`, `Acorde`).
   - `pad_register`: Select (`Grave`, `Agudo`).

   **Nota:** la previsualización (diagrama de bloques) se muestra dentro del paso
   `tail_vary` (justo tras su respuesta) y **no** como un paso independiente. Si fuera un
   paso solo-visual aparte, al retroceder desde `repetitions` ("Número de loops") la
   navegación se atascaría: el paso visual se completa solo y vuelve a pedir loops.
4. **Paso 3: Reglas Algorítmicas**
   - `tonic`: Texto (nota central, 12 notas solo sostenidos: `C`, `C#`, `D`, ..., `B`),
     con ↑/↓ para subir/bajar el pitch (acotado: C el más grave, B el más agudo, sin
     envolver); el prompt incluye una pista breve.
   - `scale`: Select (`Mayor`, `Menor (Eólica)`, `Menor Armónica`, `Frigio`, `Frigio Dominante`).
   - `allowed_durations`: Checkbox (`Negra [1.0]`, `Corchea con puntillo [0.75]`, `Corchea [0.5]`, `Semicorchea [0.25]`). Si la combinación elegida no puede rellenar exactamente el patrón (`pattern_is_combinable` devuelve `False`), se muestra un aviso y se vuelve a pedir (o el usuario puede retroceder con Ctrl+C para cambiar la duración del patrón).
   - `max_jump`: Slider/Int (1–7).
   - `density`: Select (`Baja`, `Media`, `Alta`) — prompt "Densidad de notas".
   - `tonic_recurrence`: Select (`Libre`, `Baja`, `Media`, `Alta`) — recurrencia de la tónica en el riff.
   - `cymbal`: Select (`Hi-hat abierto`, `Hi-hat cerrado`, `Ride`, `Crash`, `China`).
   - `cymbal_vary`: Confirm y/n "¿Variar el plato en cada loop? (aleatorio)" (default Sí), solo si `repetitions > 1`.
   - `fill`: Confirm y/n "¿Fill entre loops? (roll de caja + plato_alt)" (default No), solo si `repetitions > 1`.
   - `double_time`: Confirm y/n (solo 4/4) — plato a corcheas y caja en 2 y 4.
5. **Paso 4: Mezclador**
   - Confirm `y/n`: "¿Personalizar volumen y velocity de las pistas?" (default No).
   - Si **No**: se usan los valores por defecto (`velocity=100`, `volume=100`) en las 5 pistas.
   - Si **Sí**, por cada pista (Pad, Bass, Guitarra, Arpeggiator, Percusión):
     - `velocity`: Int (0–127).
     - `volume`: Int (0–100).
6. **Paso 5: Lote**
   - `variations`: Entero (1–5, default 1). Nº de variaciones (MIDIs) a generar con los mismos parámetros.
7. **Generar**
   - Se ejecuta `engine_math` + `engine_midi` una vez por variación (MIDI en memoria),
     con una barra de progreso (`rich.progress`) durante la generación del lote.
8. **Navegación:**
   - Los campos numéricos aceptan ↑/↓ para incrementar/decrementar su valor
     (enteros ±1; `pattern_beats` ±0.25), acotado al rango válido.
   - La nota central (`tonic`) también cambia con ↑/↓ (subir/bajar el pitch, acotado a C–B).
   - **Ctrl+C** retrocede a la pregunta anterior. En la **primera pregunta de una sección**,
     retrocede a la **última pregunta de la sección anterior** (en la primera sección, sale).
   - **Ctrl+G** sale del programa en cualquier momento (en cualquier pregunta).
   - Cada sección se muestra tras un **clear** de la terminal, dejando arriba un **header
     compacto** (`CLIff` + ayuda en `dim`) y el título con su índice `[N/5]`; las preguntas
     de la sección empiezan desde el tope. Al retroceder a otra sección, la pantalla se
     limpia y se vuelve a renderizar el header + título de esa sección.
   - El header compacto muestra la ayuda (`Ctrl+C` / `Ctrl+G`) como texto `dim`.

### 1.2 Previsualización de Polimetría (`rich`)

Tras completar el **Paso 2** (cuando ya se conocen `total_bars` y `pattern_beats`),
la TUI muestra una previsualización (titulada "Previsualización de polimetría" en
`cliff.brand`) calculada con `engine_math.polymetry_summary`:

1. **Total de beats:** `total_bars × BEATS_PER_BAR` por estructura (con su equivalencia en
   compases), en `cliff.value`.
2. **Mapa gráfico:** una barra de bloques que representa **una estructura**:
   - Los **ciclos completos** del patrón se dibujan en **cian**.
   - El **tail** final se dibuja en **amarillo**.
   - **Separación:** los bloques se separan con un espacio simple (sin corchetes).
   - **Resolución:** 1 bloque = 1 beat. Cuando `pattern_beats` o el tail tienen
     fracciones de cuarto (0.25/0.5/0.75), se usa resolución de semicorchea
     (0.25 beat = 1 bloque) para que todos los segmentos tengan longitud entera.
   - **Escalado:** si la barra supera ~60 bloques, se reduce proporcionalmente
     (manteniendo las proporciones) para caber en el ancho de la terminal.
3. **Leyenda:** "N ciclos completos + tail de M beats".

Ejemplo (8 compases en 4/4, patrón de 7 beats):

```text
32 beats por estructura (8 compases × 4)
███████ ███████ ███████ ███████ ████
4 ciclos completos + tail de 4 beats
```

### 1.3 Vista de Resultados (`rich.table`)

Tras generar, se limpia la terminal y se muestra:

1. **Resumen** (`box.SIMPLE`, con título y caption, precedido de una línea en blanco):
   métricas de polimetría (beats por estructura, loops, duración del patrón, ciclos, tail)
   más los parámetros de la pieza (BPM, tónica, escala, densidad de notas, recurrencia de
   tónica, salto melódico, duraciones permitidas, plato y double time).
   La columna **Valor** se muestra en `cliff.value` (verde suave).
2. **Mezclador** (`box.SIMPLE`): por pista (Pad, Bajo, Guitarra, Arpegiador, Percusión)
   el instrumento GM, velocity y volumen (valores en `cliff.value`).
3. **Selector de acciones** (sin leyenda): un `questionary.select` con las opciones
   "Exportar", "Volver" y "Salir" (texto plano, sin emojis).

Ejemplo del resumen (8 compases, patrón de 7 beats):

```text
Resumen

  Métrica                             Valor
 ─────────────────────────────────────────────────────────────────
  Beats por Estructura                32 (8 compases en 4/4)
  Loops                               2
  Duración del Patrón                 7.0 beats
  Ciclos Completos (por estructura)   4 ciclos (28.0 beats)
  Residuo / Tail (por estructura)     4.0 beats
  BPM                                 120
  Tónica                              C
  Escala                              Menor (Eólica)
  Densidad de notas                   Media
  Recurrencia de tónica               Media
  Salto melódico máximo               3
  Duraciones permitidas               Negra, Corchea, Semicorchea
  Plato                               Hi-hat abierto
  Double time                         No
  Tail                                Truncado
  Fill entre loops                    No
  Intro                               No
```

> Si `cymbal_vary` está activo, la fila **Plato** muestra `Hi-hat abierto (varía por loop)`.
> La fila **Tail** muestra `Variación melódica` cuando `tail_vary` está activo.

- **💾 Exportar**: guarda los `.mid` con el nombre `{tónica}_{escala}_{compás}_{bpm}bpm_{fechaDDMMYYYY}_{nº}.mid` (p. ej. `c_eolian_44_146bpm_05102026_3.mid`). El `nº` es el siguiente libre en la carpeta de destino (evita sobreescritura); en lote se asignan números consecutivos.
- Los tiempos y duraciones se muestran al usuario con **nombres de nota** (negra, corchea…), nunca en ticks enteros.
