# Spec 03: Motor MIDI y Audio

## 1. Módulo `cliff/engine_midi.py`

### 1.1 Mapeo de Pistas y Canales

| Pista | Nombre | Canal MIDI | Instrumento GM | Notas / Funciones |
| :--- | :--- | :--- | :--- | :--- |
| **0** | Metrónomo | 10 | Percussion (37/42) | Count-in de 4 golpes previos |
| **1** | Pad | 0 (Canal 1) | GM 89 (Warm Pad) | Tríada C-E-G o Drone continuo |
| **2** | Bass | 1 (Canal 2) | GM 33 (Finger Bass) | Notas del algoritmo melódico |
| **3** | Arpeggiator | 2 (Canal 3) | GM 80 (Square Lead) | Subdivisión rápida en escala |
| **4** | Percussion | 9 (Canal 10)| Percussion Set | Snare (38), HiHat (42), Kick (36) |

---

### 1.2 Reglas Especiales de Construcción

#### A. Regla de Drone Infinito (Pad)
- Si `pad_breath_bars == 0`:
  - En el tick 0 de la pieza: Enviar `Note On` para el acorde de la tónica.
  - En el tick final del último compás: Enviar `Note Off`.

#### B. Clonación de Acenso Kick (Percusión)
- La pista de Percusión analiza los tiempos absolutos de disparo (`Note On`) de la pista de **Bass**.
- En cada instante donde el Bass dispara una nota, la Percusión añade un evento `Note On` de Kick (Nota General MIDI 36).
- Mantiene Snare fijo en beats 2 y 4 de cada compás.

#### C. Conversión Beats a Ticks
- `mido` utiliza `ticks_per_beat = 480`.
- $\text{ticks} = \text{round}(\text{duración\_en\_beats} \times 480)$.

---

## 2. Módulo `cliff/engine_audio.py`

### 2.1 Renderizado con FluidSynth
**Función:** `render_midi_to_wav(midi_path: str, sf2_path: str, output_wav_path: str) -> bool`

**Implementación (Vía Subprocess):**
```python
import subprocess

def render_midi_to_wav(midi_path, sf2_path, output_wav_path):
    cmd = [
        "fluidsynth", "-ni", sf2_path, midi_path,
        "-F", output_wav_path, "-r", "44100"
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0
```