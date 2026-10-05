# Spec 02: Motor Matemático, Polimetría y Algoritmos Melódicos

## 1. Módulo `cliff/engine_math.py`

> Todo el cálculo de tiempos se hace en **ticks enteros** (`TICKS_PER_BEAT = 480`).
> No hay aritmética de coma flotante en las posiciones de los eventos.

### 1.1 Resolución de Densidad
**Función:** `resolve_density(density, pattern_ticks, allowed_ticks) -> int`

1. Tomar el rango objetivo `(lo, hi) = DENSITY_RANGES[density]`.
2. Calcular la factibilidad:
   - `min_notes = ceil(pattern_ticks / max(allowed_ticks))`
   - `max_notes = floor(pattern_ticks / min(allowed_ticks))`
3. Elegir `target = random.randint(lo, hi)`.
4. **Clamp:** devolver `max(min_notes, min(target, max_notes))`.

### 1.2 Generación del Patrón Rítmico
**Función:** `generate_rhythm_pattern(pattern_ticks, allowed_ticks, target_notes) -> list[int]`

**Reglas:**
- Producir **exactamente `target_notes` duraciones** (en ticks), todas del pool `allowed_ticks`.
- La **suma total es exactamente `pattern_ticks`**.
- Al elegir cada duración (salvo la última), debe dejar un resto rellenable por las notas restantes:
  - `min_next = min(allowed_ticks)`, `max_next = max(allowed_ticks)`
  - `low_bound = remaining - notas_restantes * max_next`
  - `high_bound = remaining - notas_restantes * min_next`
  - Elegir aleatoriamente una duración de `allowed_ticks` dentro de `[low_bound, high_bound]`.
- La **última** duración es el resto exacto: `remaining`.

**Salida:** lista de duraciones en ticks cuya suma es exactamente `pattern_ticks`.

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
**Función:** `generate_melody_indices(event_count, max_jump, scale_len) -> list[int]`

**Reglas:**
- El evento 0 es **SIEMPRE el índice 0** (tónica elegida).
- Para los eventos intermedios:
  - Dirección aleatoria (`+1` subir, `-1` bajar).
  - Paso `S ∈ [1, max_jump]`.
  - `nuevo = actual + (dirección * S)`.
  - **Bounce:**
    - Si `nuevo >= scale_len`: `ajustado = (scale_len - 1) - (nuevo - (scale_len - 1))`.
    - Si `nuevo < 0`: `ajustado = abs(nuevo)`.
- Retorna la lista de índices de la **frase única** (el riff).

**Riff repetido (interpretación A):**
- El riff se genera **una sola vez** con `event_count = len(pattern_rhythm_ticks)`.
- Los ciclos completos **repiten el mismo riff** (índice 0 en cada reinicio, automático).
- El tail usa `riff[:len(tail_rhythm_ticks)]` (truncado del propio patrón).

### 1.5 Construcción de las Pistas

#### A. Bass (línea melódica principal)
- Pitch por nota: `SCALE_PITCHES[scale][indice] + TONIC_SEMITONES[tonic] + BASS_PITCH_OFFSET` (dos octavas abajo de la escala transpuesta).
- Se combina el riff con el ritmo expandido (ciclos completos + tail).
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
- **Snare (38):** beats 2 y 4 de cada compás (`bar_start + 480` y `bar_start + 1440` ticks).
- **Hi-Hat (42):** corcheas constantes (cada 240 ticks).
- Duración fija de los golpes (p.ej. 120 ticks).
- `velocity` = `drums_config.velocity`.

#### D. Arpeggiator
- **Pista fantasma**: no se generan notas en el MVP (`arp_notes = []`).

### 1.6 Orquestación
**Función:** `generate_sequence(config: SongConfig) -> SequenceData`

0. Transponer la escala según la tónica: `scale_pitches = [p + TONIC_SEMITONES[tonic] for p in SCALE_PITCHES[scale]]`.
1. Resolver densidad y generar el patrón rítmico.
2. Calcular `full_loops` y `tail_ticks` con `polymetry_summary`; construir el tail.
3. Generar el riff y ensamblar `bass_notes`.
4. Construir `pad_notes` y `percussion_notes`.
5. Devolver `SequenceData` con el resumen (en beats) y las cuatro listas de notas
   (`arp_notes = []`).

**Resumen (beats):**
- `total_beats = total_bars * 4.0`
- `pattern_beats = config.pattern_beats`
- `full_loops` (entero)
- `tail_beats = tail_ticks / TICKS_PER_BEAT`
