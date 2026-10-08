# Spec 04: Interfaz TUI y Flujo de Usuario

## 1. Módulo `cliff/tui.py`

### 1.1 Pantallas y Pasos Interactivos (`questionary`)

1. **Header:** Logo **CLIff** en un `Panel` (subtítulo, motivo y tagline) con un `Theme`
   propio (`cliff.brand/accent/muted/warn/ok`). Cada paso se separa con un `Rule`
   titulado: "Configuración Global", "Estructura", "Reglas Algorítmicas", "Mezclador", "Lote".
2. **Paso 1: Configuración Global**
   - `bpm`: Entero (40–240, default 120).
   - Se muestra el compás actual (`4/4`, fijo en el MVP) antes de pedir los compases.
   - `total_bars`: Entero (4–64, default 4).
   - Se muestra la multiplicación `total_bars × BEATS_PER_BAR = beats por estructura`.
3. **Paso 2: Polimetría y Pad**
   - `pattern_beats`: Flotante/Entero (ej. 3, 5, 7, 9.5). **Validado** como múltiplo de la menor duración permitida (0.25).
   - `tail_vary`: Confirm y/n "¿Variar la melodía del tail? (mismos tiempos, otros pitches)" (default No), mostrado justo después del diagrama de bloques.
   - `repetitions` ("Número de loops"): Entero (1–8, default 2). Nº de veces que se repite la estructura completa (ciclos completos + tail) para observar el truncamiento.
   - `intro`: Confirm y/n "¿Intro de 4 golpes de hi-hat?" (default No) — count-in antes de la pieza.
   - `pad_breath_bars`: Entero (`0` = Drone Infinito, `1-8` = re-disparo).
   - `pad_mode`: Select (`Mono`, `Acorde`).
   - `pad_register`: Select (`Grave`, `Agudo`).
4. **Paso 3: Reglas Algorítmicas**
   - `tonic`: Select (nota central, 12 notas solo sostenidos: `C`, `C#`, `D`, ..., `B`).
   - `scale`: Select (`Mayor`, `Menor (Eólica)`, `Menor Armónica`, `Frigio`, `Frigio Dominante`).
   - `allowed_durations`: Checkbox (`Negra [1.0]`, `Corchea con puntillo [0.75]`, `Corchea [0.5]`, `Semicorchea [0.25]`). Si la combinación elegida no puede rellenar exactamente el patrón (`pattern_is_combinable` devuelve `False`), se muestra un aviso y se vuelve a pedir (o el usuario puede retroceder con Ctrl+C para cambiar la duración del patrón).
   - `max_jump`: Slider/Int (1–5).
   - `density`: Select (`Baja`, `Media`, `Alta`).
   - `tonic_recurrence`: Select (`Libre`, `Baja`, `Media`, `Alta`) — recurrencia de la tónica en el riff.
   - `cymbal`: Select (`Hi-hat abierto`, `Hi-hat cerrado`, `Ride`, `Crash`, `China`).
   - `cymbal_vary`: Confirm y/n "¿Variar el plato en cada loop? (aleatorio)" (default No), solo si `repetitions > 1`.
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
   - **Ctrl+C** retrocede a la pregunta anterior; en el primer prompt sale del programa.
   - El header muestra esta ayuda como texto `dim`.

### 1.2 Previsualización de Polimetría (`rich`)

Tras completar el **Paso 2** (cuando ya se conocen `total_bars` y `pattern_beats`),
la TUI muestra una previsualización calculada con `engine_math.polymetry_summary`:

1. **Total de beats:** `total_bars × BEATS_PER_BAR` por estructura (con su equivalencia en compases).
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

Tras generar, se muestra:

1. **Resumen** (`box.ROUNDED`, con título y caption): métricas de polimetría (beats por
   estructura, loops, duración del patrón, ciclos, tail) más los parámetros de la pieza
   (BPM, tónica, escala, densidad, recurrencia de tónica, salto melódico, duraciones
   permitidas, plato y double time).
2. **Mezclador** (`box.SIMPLE`): por pista (Pad, Bajo, Guitarra, Arpegiador, Percusión)
   el instrumento GM, velocity y volumen.
3. **Selector de acciones** (sin leyenda): un `questionary.select` con las opciones
   💾 Exportar, ↩ Volver y ✕ Salir.

Ejemplo del resumen (8 compases, patrón de 7 beats):

```text
┌───────────────────────────────────┬─────────────────────────────┐
│ Métrica                           │ Valor                       │
├───────────────────────────────────┼─────────────────────────────┤
│ Beats por Estructura              │ 32 (8 compases en 4/4)      │
│ Loops                             │ 2                           │
│ Duración del Patrón               │ 7.0 beats                   │
│ Ciclos Completos (por estructura) │ 4 ciclos (28.0 beats)       │
│ Residuo / Tail (por estructura)   │ 4.0 beats                   │
│ BPM                               │ 120                         │
│ Tónica                            │ C                           │
│ Escala                            │ Menor (Eólica)              │
│ Densidad                          │ Media                       │
│ Recurrencia de tónica             │ Media                       │
│ Salto melódico máximo             │ 3                           │
│ Duraciones permitidas             │ Negra, Corchea, Semicorchea │
│ Plato                             │ Hi-hat abierto              │
│ Double time                       │ No                          │
│ Tail                              │ Truncado                    │
│ Fill entre loops                  │ No                          │
│ Intro                             │ No                          │
└───────────────────────────────────┴─────────────────────────────┘
```

> Si `cymbal_vary` está activo, la fila **Plato** muestra `Hi-hat abierto (varía por loop)`.
> La fila **Tail** muestra `Variación melódica` cuando `tail_vary` está activo.

- **💾 Exportar**: guarda los `.mid` con el nombre `{tónica}_{escala}_{compás}_{bpm}bpm_{fechaDDMMYYYY}_{nº}.mid` (p. ej. `c_eolian_44_146bpm_05102026_3.mid`). El `nº` es el siguiente libre en la carpeta de destino (evita sobreescritura); en lote se asignan números consecutivos.
- Los tiempos y duraciones se muestran al usuario con **nombres de nota** (negra, corchea…), nunca en ticks enteros.
