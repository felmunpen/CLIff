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

class TonicRecurrence(str, Enum):
    """Recurrencia de la tónica en el riff (probabilidad de que una nota se convierta en tónica)."""
    LIBRE = "Libre"
    LOW = "Baja"
    MEDIUM = "Media"
    HIGH = "Alta"

class PadMode(str, Enum):
    MONO = "Mono"
    CHORD = "Acorde"

class PadRegister(str, Enum):
    LOW = "Grave"    # C3
    HIGH = "Agudo"   # C4

class TonicEnum(str, Enum):
    """Nota central (tónica) elegible. Solo sostenidos en el MVP."""
    C = "C"
    C_SHARP = "C#"
    D = "D"
    D_SHARP = "D#"
    E = "E"
    F = "F"
    F_SHARP = "F#"
    G = "G"
    G_SHARP = "G#"
    A = "A"
    A_SHARP = "A#"
    B = "B"

class CymbalEnum(str, Enum):
    """Plato (fuente del pulso) de la pista de percusión."""
    OPEN_HI_HAT = "Hi-hat abierto"
    CLOSED_HI_HAT = "Hi-hat cerrado"
    RIDE = "Ride"
    CRASH = "Crash"
    CHINA = "China"
```

### 1.2 Constantes

```python
TICKS_PER_BEAT = 480  # ppq usada por mido
BEATS_PER_BAR = 4     # métrica por compás (4/4 fija en el MVP; futura configurabilidad)
BASS_PITCH_OFFSET = -24  # bajo dos octavas por debajo de la escala base (-> C1)
GUITAR_PITCH_OFFSET = 12 # guitarra una octava por encima del bajo (-> C2)

# Nota MIDI de cada plato en el mapa de percusión de General MIDI (canal 10).
CYMBAL_PITCHES: dict[CymbalEnum, int] = {
    CymbalEnum.OPEN_HI_HAT: 46,
    CymbalEnum.CLOSED_HI_HAT: 42,
    CymbalEnum.RIDE: 51,
    CymbalEnum.CRASH: 49,
    CymbalEnum.CHINA: 52,
}

# Nota central (tónica): semitonos respecto a C y slug para nombre de archivo.
TONIC_SEMITONES: dict[TonicEnum, int] = {
    TonicEnum.C: 0, TonicEnum.C_SHARP: 1, TonicEnum.D: 2, TonicEnum.D_SHARP: 3,
    TonicEnum.E: 4, TonicEnum.F: 5, TonicEnum.F_SHARP: 6, TonicEnum.G: 7,
    TonicEnum.G_SHARP: 8, TonicEnum.A: 9, TonicEnum.A_SHARP: 10, TonicEnum.B: 11,
}

TONIC_SLUGS: dict[TonicEnum, str] = {
    TonicEnum.C: "c", TonicEnum.C_SHARP: "cs", TonicEnum.D: "d", TonicEnum.D_SHARP: "ds",
    TonicEnum.E: "e", TonicEnum.F: "f", TonicEnum.F_SHARP: "fs", TonicEnum.G: "g",
    TonicEnum.G_SHARP: "gs", TonicEnum.A: "a", TonicEnum.A_SHARP: "as", TonicEnum.B: "b",
}

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

# Probabilidad de que una nota del riff (salvo la primera) se convierta en tónica
TONIC_RECURRENCE_PROB: dict[TonicRecurrence, float] = {
    TonicRecurrence.LIBRE: 0.0,
    TonicRecurrence.LOW: 0.10,
    TonicRecurrence.MEDIUM: 0.25,
    TonicRecurrence.HIGH: 0.45,
}

# Desplazamiento de octava del Pad según registro (en semitonos)
PAD_REGISTER_OFFSET: dict[PadRegister, int] = {
    PadRegister.LOW: 0,     # C3 (MIDI 48)
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
    total_bars: int = 4
    repetitions: int = 2                # nº de veces que se repite la estructura (ciclos + tail)
    pattern_beats: float = 7.0
    pad_breath_bars: int = 0            # 0 = Drone Infinito; 1-8 = re-disparo
    tonic: TonicEnum = TonicEnum.C      # nota central (tónica)
    scale: ScaleEnum = ScaleEnum.MINOR_AEOLIAN
    allowed_durations: list[float] = field(default_factory=lambda: [1.0, 0.5, 0.25])
    max_jump: int = 3
    density: DensityEnum = DensityEnum.MEDIUM
    tonic_recurrence: TonicRecurrence = TonicRecurrence.MEDIUM
    pad_mode: PadMode = PadMode.CHORD
    pad_register: PadRegister = PadRegister.LOW
    bass_config: TrackConfig = field(default_factory=TrackConfig)
    pad_config: TrackConfig = field(default_factory=TrackConfig)
    arp_config: TrackConfig = field(default_factory=TrackConfig)    # reservado (pista fantasma)
    guitar_config: TrackConfig = field(default_factory=TrackConfig)
    drums_config: TrackConfig = field(default_factory=TrackConfig)
    double_time: bool = False           # platos a corcheas y caja en 2/4 (solo 4/4)
    cymbal: CymbalEnum = CymbalEnum.OPEN_HI_HAT

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
    repetitions: int                    # veces que se repite la estructura completa
    pad_notes: list[NoteEvent]
    bass_notes: list[NoteEvent]
    arp_notes: list[NoteEvent]          # vacía en MVP (pista fantasma)
    guitar_notes: list[NoteEvent]       # sigue al bajo una octava arriba
    percussion_notes: list[NoteEvent]
```

## 2. Reglas de Validación (aplicadas en la TUI)

| Campo | Restricción |
| :--- | :--- |
| `bpm` | Entero, 40–240 |
| `total_bars` | Entero, 4–64 |
| `repetitions` | Entero, 1–8 (`1` = estructura única) |
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
