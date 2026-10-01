# Spec 03: Motor MIDI y Audio

## 1. Módulo `cliff/engine_midi.py`

### 1.1 Mapeo de Pistas y Canales

Convención: en la documentación se usa la **notación General MIDI (1-indexada)**.
En código (`mido` es 0-indexado) se resta 1: `canal_mido = canal_gm - 1`.

| Pista | Canal GM | Canal mido | Instrumento GM | Notas / Función |
| :--- | :--- | :--- | :--- | :--- |
| **Pad** | 1 | 0 | GM 89 (Warm Pad) | Acorde de tónica o nota única; Drone |
| **Bass** | 2 | 1 | GM 33 (Finger Bass) | Riff melódico (patrón principal) |
| **Arpeggiator** | 3 | 2 | GM 80 (Square Lead) | Pista fantasma (vacía en MVP) |
| **Percussion** | 10 | 9 | Set estándar de percusión | Snare (38), HiHat (42), Kick (36) |

El archivo `.mid` tiene **4 pistas**. La de Arpeggiator se incluye **vacía**
(solo con su `program_change`), reservada para una feature futura.

### 1.2 Reglas Especiales de Construcción

#### A. Regla de Drone Infinito (Pad)
- Si `pad_breath_bars == 0`:
  - En el tick 0 de la pieza: enviar `Note On` para el acorde/nota del Pad.
  - En el tick final del último compás: enviar `Note Off`.
- Si `pad_breath_bars > 0`: re-disparar el acorde/nota cada `pad_breath_bars` compases.

#### B. Nota/Acorde del Pad (derivado de la escala)
- `CHORD`: `[SCALE_PITCHES[0], SCALE_PITCHES[2], SCALE_PITCHES[4]]` (grados 1, 3 y 5).
- `MONO`: `[SCALE_PITCHES[0]]` (tónica).
- Registrar: sumar `PAD_REGISTER_OFFSET[pad_register]` a cada nota (`LOW=-12`, `MID=0`, `HIGH=+12`).

#### C. Clonación del Kick (Percusión)
- La pista de Percusión analiza los tiempos absolutos de `Note On` de la pista **Bass**.
- En cada instante donde el Bass dispara, añade un `Note On` de Kick (nota 36).
- Mantiene Snare fijo (nota 38) en los beats 2 y 4 de cada compás.
- Hi-Hat (nota 42) en corcheas constantes (0.5 beats).

#### D. Volume y Velocity
- **Velocity** (0-127): plano, un único valor por pista (`TrackConfig.velocity`).
- **Volume** (0-100): emitido como `Control Change` CC7 **una vez al inicio** de cada pista, con mapeo lineal:
  `cc7 = round(volume * 127 / 100)`.
- Orden de eventos al inicio de cada pista: `program_change` → `control_change` (CC7) → notas.

#### E. Conversión Beats a Ticks
- `TICKS_PER_BEAT = 480`.
- `ticks = round(duración_en_beats * 480)`.
- Los tiempos acumulados se calculan en **ticks enteros** (sin coma flotante).

## 2. Módulo `cliff/engine_audio.py`

### 2.1 Renderizado con FluidSynth (perezoso)
**Función:** `render_midi_to_wav(midi_path: str, sf2_path: str, output_wav_path: str) -> bool`

**Implementación (vía subprocess con el binario `fluidsynth`):**

```python
import subprocess

def render_midi_to_wav(midi_path, sf2_path, output_wav_path):
    cmd = [
        "fluidsynth", "-ni", sf2_path, midi_path,
        "-F", output_wav_path, "-r", "44100",
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0
```

> Se ejecuta **solo cuando** el usuario pulsa ▶ Play o 💾 Exportar (no en la generación).

### 2.2 Reproducción (best-effort)
**Función:** `play_audio(wav_path: str) -> None`

Usa el reproductor por defecto del sistema vía subprocess:

```python
import sys
import subprocess

def play_audio(wav_path):
    if sys.platform == "darwin":                 # macOS
        cmd = ["afplay", wav_path]
    elif sys.platform.startswith("win"):         # Windows
        cmd = ["powershell", "-c",
               f'(New-Object Media.SoundPlayer "{wav_path}").PlaySync()']
    else:                                        # Linux
        cmd = ["aplay", wav_path]                # fallback: paplay
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
```

- **Best-effort**: si el reproductor no existe o falla, no se interrumpe la ejecución;
  simplemente se informa de la ruta del `.wav`.
