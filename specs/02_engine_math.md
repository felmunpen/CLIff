# Spec 02: Motor Matemático, Polimetría y Algoritmos Melódicos

## 1. Módulo `cliff/engine_math.py`

> Todo el cálculo de tiempos se hace en **ticks enteros** (`TICKS_PER_BEAT = 480`).
> No hay aritmética de coma flotante en las posiciones de los eventos.

### 1.1 Resolución de Densidad
**Función:** `resolve_density(density, pattern_ticks, allowed_ticks) -> int`

1. Calcular el rango factible `[min_notes, max_notes]`:
   - `min_notes = ceil(pattern_ticks / max(allowed_ticks))`
   - `max_notes = floor(pattern_ticks / min(allowed_ticks))`
2. Interpretar el nivel de densidad como una fracción de ese rango
   (`DENSITY_FRACTIONS`: Baja 0.25, Media 0.5, Alta 0.8):
   - `target = min_notes + round(fraction * (max_notes - min_notes))`.
3. Devolver `max(min_notes, min(target, max_notes))`.

> La densidad es **relativa a la factibilidad**, de modo que los tres niveles se
> distinguen para cualquier longitud de patrón y pool de duraciones (evita que
> Baja/Media colapsen a `min_notes` —p. ej. "todo negras"— cuando la negra está
> en el pool).

### 1.2 Generación del Patrón Rítmico
**Función:** `generate_rhythm_pattern(pattern_ticks, allowed_ticks, target_notes) -> list[int]`

**Reglas:**
- Producir **exactamente `target_notes` duraciones** (en ticks), todas del pool `allowed_ticks`.
- La **suma total es exactamente `pattern_ticks`**.
- Se resuelve por **búsqueda con retroceso aleatorizada** (en lugar de un relleno
  greedy que dejaba la última nota como resto gigante):
  - `allowed = sorted(set(allowed_ticks))`, `min_next = allowed[0]`, `max_next = allowed[-1]`.
  - En cada paso, con `notes_left` notas restantes, la duración `d` debe dejar el resto
    rellenable por las `notes_left - 1` notas restantes, dentro de la ventana:
    - `low_bound = remaining - (notes_left - 1) * max_next`
    - `high_bound = remaining - (notes_left - 1) * min_next`
  - Se barajan (`random.shuffle`) las duraciones del pool dentro de `[low_bound, high_bound]`
    y se avanza; si un camino muere, se **retrocede** y se prueba otra candidata.
  - Con `notes_left == 0`, solo se acepta el resultado si `remaining == 0`.
- **Garantía:** como al quedar 1 nota `low_bound == high_bound == remaining`, la última
  nota queda **dentro del pool** (se elimina el sesgo de la nota final larga).
- **Fallback:** si no existe solución todo-en-pool (patrón no combinable con el pool,
  p. ej. por no ser múltiplo del `gcd` de las duraciones), se degrada a
  `_legacy_leftover`, donde la última nota absorbe el resto exacto (puede quedar fuera
  del pool). La suma y la longitud se mantienen exactas.

**Salida:** lista de duraciones en ticks cuya suma es exactamente `pattern_ticks`.

**Función:** `pattern_is_combinable(pattern_beats, allowed_durations) -> bool`
- Calcula el `gcd` de las duraciones permitidas (en ticks) y devuelve si divide al
  total de ticks del patrón.
- `False` significa que `generate_rhythm_pattern` degradará al fallback (última nota
  fuera del pool). P. ej. patrón `XX.25`/`XX.75` (total impar en unidades de semicorchea)
  con solo negras (4) y corcheas (2) en el pool.
- La TUI usa esta función para bloquear combinaciones no factibles.

### 1.3 Bucle de Polimetría y Cálculo del Tail

**Función pura:** `polymetry_summary(total_bars: int, pattern_beats: float) -> tuple[int, int]`
- `total_ticks = total_bars * BEATS_PER_BAR * TICKS_PER_BEAT`
- `pattern_ticks = beats_to_ticks(pattern_beats)`
- Devuelve `(full_loops, tail_ticks) = (total_ticks // pattern_ticks, total_ticks % pattern_ticks)`.
- Es la **fuente única de verdad** del residuo; la usan `generate_sequence` y la TUI (previsualización).

**Función:** `build_tail_rhythm(pattern_rhythm_ticks, tail_ticks) -> list[int]`
- Recorrer `pattern_rhythm_ticks` desde el inicio, acumulando duraciones **hasta** que la siguiente exceda `tail_ticks`.
- La última duración se ajusta a `tail_ticks - acumulado` (puede ser un truncado exacto).

**Resultado:**
- Ciclos completos: repetir `pattern_rhythm_ticks` `full_loops` veces.
- Tail: `build_tail_rhythm(...)` (los primeros beats del propio patrón).

### 1.4 Algoritmo Melódico (Riff)
**Función:** `generate_melody_indices(event_count, max_jump, scale_len, tonic_prob=0.0) -> list[int]`

**Reglas:**
- El evento 0 es **SIEMPRE el índice 0** (tónica elegida).
- Para los eventos intermedios:
  - Dirección aleatoria (`+1` subir, `-1` bajar).
  - Paso `S ∈ [1, max_jump]`.
  - `nuevo = actual + (dirección * S)`.
  - **Bounce:**
    - Si `nuevo >= scale_len`: `ajustado = (scale_len - 1) - (nuevo - (scale_len - 1))`.
    - Si `nuevo < 0`: `ajustado = abs(nuevo)`.
- **Recurrencia de la tónica (post-procesado):** tras generar el walk puro, se
  recorre cada nota salvo la primera y, con probabilidad `tonic_prob`, se
  sobreescribe a `0` (`TONIC_RECURRENCE_PROB[config.tonic_recurrence]`). No altera
  el contorno de las notas no tocadas.
- Retorna la lista de índices de la **frase única** (el riff).

**Riff repetido (interpretación A):**
- El riff se genera **una sola vez** con `event_count = len(pattern_rhythm_ticks)`.
- Los ciclos completos **repiten el mismo riff** (índice 0 en cada reinicio, automático).
- El tail usa `riff[:len(tail_rhythm_ticks)]` (truncado del propio patrón).
- Con `tail_vary = True`, el tail usa un **riff propio** `generate_melody_indices(len(tail_rhythm_ticks), ...)`
  en lugar del truncado: **mismo ritmo** (duraciones truncadas) y **primera nota = tónica**, pero **pitches distintos**.

### 1.5 Construcción de las Pistas

#### A. Bass (línea melódica principal)
- Pitch por nota: `SCALE_PITCHES[scale][indice] + TONIC_SEMITONES[tonic] + BASS_PITCH_OFFSET` (dos octavas abajo de la escala transpuesta).
- Se combina el riff con el ritmo expandido (ciclos completos + tail).
- La **estructura** (ciclos completos + tail) se construye una sola vez y luego se repite
  `repetitions` veces mediante `tile_notes` (el riff resetea a tónica en cada estructura).
- `velocity` = `bass_config.velocity` (plano).

#### B. Pad
- `CHORD`: grados `[0, 2, 4]` de `SCALE_PITCHES[scale]`.
- `MONO`: grado `[0]`.
- Registrar: `pitch += PAD_REGISTER_OFFSET[pad_register]`.
- **Drone** (`pad_breath_bars == 0`): `Note On` en tick 0, `Note Off` en `total_ticks`.
- **Respiración** (`pad_breath_bars > 0`): re-disparar cada `pad_breath_bars` compases; cada acorde dura hasta el siguiente disparo (o `total_ticks`).
- `velocity` = `pad_config.velocity`.

#### C. Percusión
- **Kick (36):** clona los tiempos absolutos de `Note On` del Bass.
- **Snare (38):** beat 3 de cada compás por defecto (`bar_start + 960` ticks); en *double time*, beats 2 y 4 (`bar_start + 480` y `bar_start + 1440`).
- **Plato:** negras por defecto (cada 480 ticks); en *double time*, corcheas (cada 240 ticks). Nota según `CYMBAL_PITCHES[cymbal]`.
  - Si `cymbal_vary` y `repetitions > 1`, el plato se emite **por loop**: el primer loop usa el plato elegido y cada loop siguiente elige un plato **aleatorio distinto del anterior** (`cymbal_pitches_per_loop`).
- **Fill entre loops** (`fill = True` y `repetitions > 1`): en cada frontera entre loops se añade un
  roll de caja (4 semicorcheas en el último beat del loop que termina) y un `plato_alt` en el
  downbeat del loop siguiente. `plato_alt`: si `cymbal_vary`, es el plato del loop saliente (eco);
  si no, un plato aleatorio distinto del principal (elección fija por generación).
- Duración fija de los golpes (p.ej. 120 ticks).
- `velocity` = `drums_config.velocity`.

#### D. Arpeggiator
- **Pista fantasma**: no se generan notas en el MVP (`arp_notes = []`).

#### E. Guitarra
- Duplica la línea del bajo **una octava por encima** (`pitch = bass.pitch + GUITAR_PITCH_OFFSET`, con `GUITAR_PITCH_OFFSET = 12`).
- Mismo ritmo y duración que el bajo; `velocity` = `guitar_config.velocity`.

#### F. Repetición de la estructura
**Función:** `tile_notes(notes, repetitions, structure_ticks) -> list[NoteEvent]`
- Repite una lista de notas (una estructura) `repetitions` veces, sumando
  `structure_ticks` al `start_tick` de cada copia.
- `structure_ticks` = `total_bars * BEATS_PER_BAR * TICKS_PER_BEAT` (longitud de una estructura).
- Si `repetitions <= 1`, devuelve la lista original sin cambios.

### 1.6 Orquestación
**Función:** `generate_sequence(config: SongConfig) -> SequenceData`

0. Transponer la escala según la tónica: `scale_pitches = [p + TONIC_SEMITONES[tonic] for p in SCALE_PITCHES[scale]]`.
1. Resolver densidad y generar el patrón rítmico.
2. Calcular `full_loops` y `tail_ticks` con `polymetry_summary`; construir el tail.
3. Generar el riff (con `tonic_prob = TONIC_RECURRENCE_PROB[config.tonic_recurrence]`), el
   `tail_riff` si `tail_vary`, y ensamblar `bass_structure` (una única estructura: ciclos completos + tail).
4. Repetir la estructura: `bass_notes = tile_notes(bass_structure, repetitions, total_ticks)`.
5. Construir `pad_notes` (sobre `total_ticks * repetitions`), `guitar_notes` (transposición del
   bajo repetido) y `percussion_notes` (sobre `total_bars * repetitions` compases, con
   `cymbal_pitch = CYMBAL_PITCHES[config.cymbal]`); si `fill`, añadir `build_fill_notes(...)` y reordenar.
6. Devolver `SequenceData` con el resumen (en beats) y las cinco listas de notas
   (`arp_notes = []`).

**Resumen (beats):**
- `total_beats = total_bars * 4.0 * repetitions`
- `pattern_beats = config.pattern_beats`
- `full_loops` (entero, por estructura)
- `tail_beats = tail_ticks / TICKS_PER_BEAT`
- `repetitions = config.repetitions`
