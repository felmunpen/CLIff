# Spec 05: Modelos de Datos y Constantes

## 1. Módulo `cliff/models.py`

### 1.1 Enumeraciones

```python
from enum import Enum

class ScaleEnum(str, Enum):
    MAJOR = "Mayor"
    MINOR_AEOLIAN = "Menor (Eólica)"
    HARMONIC_MINOR = "Menor Armónica"
    PHRYGIAN = "Frigio"
    PHRYGIAN_DOMINANT = "Frigio Dominante"

class DensityEnum(str, Enum):
    LOW = "Baja"
    MEDIUM = "Media"
    HIGH = "Alta"

class PadMode(str, Enum):
    MONO = "Mono"
    CHORD = "Acorde"

class PadRegister(str, Enum):
    LOW = "Grave"    # C2
    MID = "Medio"    # C3
    HIGH = "Agudo"   # C4
```

### 1.2 Constantes

```python
TICKS_PER_BEAT = 480  # ppq usada por mido
BEATS_PER_BAR = 4     # métrica por compás (4/4 fija en el MVP; futura configurabilidad)
TONIC = "c"           # tónica fija en el MVP (Do); futura configurabilidad (#/b)
BASS_PITCH_OFFSET = -24  # bajo dos octavas por debajo de la escala base (-> C1)

# Opciones de duración rítmica disponibles en la TUI (nombre, beats)
DURATION_OPTIONS: list[tuple[str, float]] = [
    ("Negra", 1.0),
    ("Corchea con puntillo", 0.75),
    ("Corchea", 0.5),
    ("Semicorchea", 0.25),
]

# Rango de notas objetivo (densidad) del patrón principal por nivel
DENSITY_RANGES: dict[DensityEnum, tuple[int, int]] = {
    DensityEnum.LOW: (3, 4),
    DensityEnum.MEDIUM: (5, 6),
    DensityEnum.HIGH: (7, 9),
}

# Desplazamiento de octava del Pad según registro (en semitonos)
PAD_REGISTER_OFFSET: dict[PadRegister, int] = {
    PadRegister.LOW: -12,   # C2 (MIDI 36)
    PadRegister.MID: 0,     # C3 (MIDI 48)
    PadRegister.HIGH: +12,  # C4 (MIDI 60)
}

# Mapeo de notas MIDI relativas a C3 (MIDI 48). Dos octavas (15 notas).
SCALE_PITCHES: dict[ScaleEnum, list[int]] = {
    ScaleEnum.MAJOR:             [48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72],
    ScaleEnum.MINOR_AEOLIAN:     [48, 50, 51, 53, 55, 56, 58, 60, 62, 63, 65, 67, 68, 70, 72],
    ScaleEnum.HARMONIC_MINOR:    [48, 50, 51, 53, 55, 56, 59, 60, 62, 63, 65, 67, 68, 71, 72],
    ScaleEnum.PHRYGIAN:          [48, 49, 51, 53, 55, 56, 58, 60, 61, 63, 65, 67, 68, 70, 72],
    ScaleEnum.PHRYGIAN_DOMINANT: [48, 49, 52, 53, 55, 56, 58, 60, 61, 64, 65, 67, 68, 70, 72],
}

# Slug por escala para nombres de archivo (ascii, sin espacios ni '_').
SCALE_SLUGS: dict[ScaleEnum, str] = {
    ScaleEnum.MAJOR: "major",
    ScaleEnum.MINOR_AEOLIAN: "eolian",
    ScaleEnum.HARMONIC_MINOR: "harmonicminor",
    ScaleEnum.PHRYGIAN: "phrygian",
    ScaleEnum.PHRYGIAN_DOMINANT: "phrygiandom",
}
```

### 1.3 Dataclasses

```python
from dataclasses import dataclass, field

@dataclass
class TrackConfig:
    """Mezcla por pista: velocity plano (0-127) y volumen de canal (0-100)."""
    velocity: int = 100
    volume: int = 100

@dataclass
class SongConfig:
    bpm: int = 120
    total_bars: int = 8
    pattern_beats: float = 7.0
    pad_breath_bars: int = 0            # 0 = Drone Infinito; 1-8 = re-disparo
    scale: ScaleEnum = ScaleEnum.MINOR_AEOLIAN
    allowed_durations: list[float] = field(default_factory=lambda: [1.0, 0.5, 0.25])
    max_jump: int = 3
    density: DensityEnum = DensityEnum.MEDIUM
    pad_mode: PadMode = PadMode.CHORD
    pad_register: PadRegister = PadRegister.MID
    bass_config: TrackConfig = field(default_factory=TrackConfig)
    pad_config: TrackConfig = field(default_factory=TrackConfig)
    arp_config: TrackConfig = field(default_factory=TrackConfig)    # reservado (pista fantasma)
    drums_config: TrackConfig = field(default_factory=TrackConfig)

@dataclass
class NoteEvent:
    """Nota individual. Los tiempos se expresan en ticks enteros (exactos)."""
    pitch: int
    start_tick: int
    duration_ticks: int
    velocity: int

@dataclass
class SequenceData:
    """Salida de `engine_math.py`, consumida por `engine_midi.py` y la TUI.

    Los campos de resumen están en beats (para mostrar al usuario); el
    timing real de los eventos está en ticks enteros dentro de `NoteEvent`.
    """
    total_beats: float
    pattern_beats: float
    full_loops: int
    tail_beats: float
    pad_notes: list[NoteEvent]
    bass_notes: list[NoteEvent]
    arp_notes: list[NoteEvent]          # vacía en MVP (pista fantasma)
    percussion_notes: list[NoteEvent]
```

## 2. Reglas de Validación (aplicadas en la TUI)

| Campo | Restricción |
| :--- | :--- |
| `bpm` | Entero, 40–240 |
| `total_bars` | Entero, 4–64 |
| `pattern_beats` | Múltiplo de la menor duración permitida (0.25 = 120 ticks) |
| `pad_breath_bars` | Entero, 0–8 (`0` = Drone Infinito) |
| `max_jump` | Entero, 1–5 |
| `velocity` | Entero, 0–127 |
| `volume` | Entero, 0–100 |

## 3. Conversión Beats ↔ Ticks

Toda la aritmética de tiempos se hace en ticks enteros (`TICKS_PER_BEAT = 480`).
Los valores de entrada en beats se convierten **una sola vez**:

```python
def beats_to_ticks(beats: float) -> int:
    return round(beats * TICKS_PER_BEAT)
```

Las duraciones permitidas quedan: `1.0 → 480`, `0.75 → 360`, `0.5 → 240`, `0.25 → 120`.
