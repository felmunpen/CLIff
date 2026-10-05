# Spec 03: Motor MIDI

## 1. Módulo `cliff/engine_midi.py`

### 1.1 Mapeo de Pistas y Canales

Convención: en la documentación se usa la **notación General MIDI (1-indexada)**.
En código (`mido` es 0-indexado) se resta 1: `canal_mido = canal_gm - 1`.

| Pista | Canal GM | Canal mido | Instrumento GM | Notas / Función |
| :--- | :--- | :--- | :--- | :--- |
| **Pad** | 1 | 0 | GM 89 (Warm Pad) | Acorde de tónica o nota única; Drone |
| **Bass** | 2 | 1 | GM 33 (Finger Bass) | Riff melódico (patrón principal), dos octavas por debajo de la escala base |
| **Arpeggiator** | 3 | 2 | GM 80 (Square Lead) | Pista fantasma (vacía en MVP) |
| **Guitar** | 4 | 3 | GM 29 (Overdriven Guitar) | Duplica el bajo una octava por encima |
| **Percussion** | 10 | 9 | Set estándar de percusión | Snare (38), Plato (46/42/51/49/52), Kick (36) |

El archivo `.mid` tiene **5 pistas**. La de Arpeggiator se incluye **vacía**
(solo con su `program_change`), reservada para una feature futura.

> La escala usada en todas las pistas es la **transpuesta según la tónica** elegida
> (`SCALE_PITCHES[scale] + TONIC_SEMITONES[tonic]`), calculada en `engine_math`.

### 1.2 Reglas Especiales de Construcción

#### A. Regla de Drone Infinito (Pad)
- Si `pad_breath_bars == 0`:
  - En el tick 0 de la pieza: enviar `Note On` para el acorde/nota del Pad.
  - En el tick final del último compás: enviar `Note Off`.
- Si `pad_breath_bars > 0`: re-disparar el acorde/nota cada `pad_breath_bars` compases.

#### B. Nota/Acorde del Pad (derivado de la escala)
- `CHORD`: `[SCALE_PITCHES[0], SCALE_PITCHES[2], SCALE_PITCHES[4]]` (grados 1, 3 y 5).
- `MONO`: `[SCALE_PITCHES[0]]` (tónica).
- Registrar: sumar `PAD_REGISTER_OFFSET[pad_register]` a cada nota (`LOW=0`, `HIGH=+12`).

#### C. Clonación del Kick (Percusión)
- La pista de Percusión analiza los tiempos absolutos de `Note On` de la pista **Bass**.
- En cada instante donde el Bass dispara, añade un `Note On` de Kick (nota 36).
- Mantiene Snare fijo (nota 38) en el beat 3 de cada compás (en 2 y 4 con *double time*).
- Plato (nota configurable según `CYMBAL_PITCHES`) en negras por defecto (1 beat); en *double time*, corcheas (0.5 beats).

#### D. Volume y Velocity
- **Velocity** (0-127): plano, un único valor por pista (`TrackConfig.velocity`).
- **Volume** (0-100): emitido como `Control Change` CC7 **una vez al inicio** de cada pista, con mapeo lineal:
  `cc7 = round(volume * 127 / 100)`.
- Orden de eventos al inicio de cada pista: `program_change` → `control_change` (CC7) → notas.

#### E. Conversión Beats a Ticks
- `TICKS_PER_BEAT = 480`.
- `ticks = round(duración_en_beats * 480)`.
- Los tiempos acumulados se calculan en **ticks enteros** (sin coma flotante).
