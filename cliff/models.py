"""Modelos de datos, enums y constantes de CLIff."""

from dataclasses import dataclass, field
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


TICKS_PER_BEAT = 480  # ppq usada por mido
BEATS_PER_BAR = 4     # métrica por compás (4/4 fija en el MVP; futura configurabilidad)

# Opciones de duración rítmica disponibles en la TUI (nombre, beats)
DURATION_OPTIONS: list[tuple[str, float]] = [
    ("Negra", 1.0),
    ("Corchea con puntillo", 0.75),
    ("Corchea", 0.5),
    ("Semicorchea", 0.25),
]

# Fracción del rango factible [min_notes, max_notes] que usa cada nivel de
# densidad para fijar el número de notas objetivo (relativo a la factibilidad).
DENSITY_FRACTIONS: dict[DensityEnum, float] = {
    DensityEnum.LOW: 0.35,
    DensityEnum.MEDIUM: 0.5,
    DensityEnum.HIGH: 0.65,
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
    PadRegister.HIGH: 12,   # C4 (MIDI 60)
}

# Mapeo de notas MIDI relativas a C3 (MIDI 48). Dos octavas (15 notas).
SCALE_PITCHES: dict[ScaleEnum, list[int]] = {
    ScaleEnum.MAJOR:             [48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72],
    ScaleEnum.MINOR_AEOLIAN:     [48, 50, 51, 53, 55, 56, 58, 60, 62, 63, 65, 67, 68, 70, 72],
    ScaleEnum.HARMONIC_MINOR:    [48, 50, 51, 53, 55, 56, 59, 60, 62, 63, 65, 67, 68, 71, 72],
    ScaleEnum.PHRYGIAN:          [48, 49, 51, 53, 55, 56, 58, 60, 61, 63, 65, 67, 68, 70, 72],
    ScaleEnum.PHRYGIAN_DOMINANT: [48, 49, 52, 53, 55, 56, 58, 60, 61, 64, 65, 67, 68, 70, 72],
}

# Nota central (tónica) elegible. Solo sostenidos en el MVP.
# TONIC_SEMITONES: semitonos respecto a C; TONIC_SLUGS: slug para nombre de archivo.
TONIC_SEMITONES: dict[TonicEnum, int] = {
    TonicEnum.C: 0,
    TonicEnum.C_SHARP: 1,
    TonicEnum.D: 2,
    TonicEnum.D_SHARP: 3,
    TonicEnum.E: 4,
    TonicEnum.F: 5,
    TonicEnum.F_SHARP: 6,
    TonicEnum.G: 7,
    TonicEnum.G_SHARP: 8,
    TonicEnum.A: 9,
    TonicEnum.A_SHARP: 10,
    TonicEnum.B: 11,
}

TONIC_SLUGS: dict[TonicEnum, str] = {
    TonicEnum.C: "c",
    TonicEnum.C_SHARP: "cs",
    TonicEnum.D: "d",
    TonicEnum.D_SHARP: "ds",
    TonicEnum.E: "e",
    TonicEnum.F: "f",
    TonicEnum.F_SHARP: "fs",
    TonicEnum.G: "g",
    TonicEnum.G_SHARP: "gs",
    TonicEnum.A: "a",
    TonicEnum.A_SHARP: "as",
    TonicEnum.B: "b",
}

# Desplazamiento del Bajo respecto a la escala base (dos octavas abajo, -> C1).
BASS_PITCH_OFFSET = -24

# Desplazamiento de la Guitarra respecto al Bajo (una octava arriba, -> C2).
GUITAR_PITCH_OFFSET = 12

# Nota MIDI de cada plato en el mapa de percusión de General MIDI (canal 10).
CYMBAL_PITCHES: dict[CymbalEnum, int] = {
    CymbalEnum.OPEN_HI_HAT: 46,
    CymbalEnum.CLOSED_HI_HAT: 42,
    CymbalEnum.RIDE: 51,
    CymbalEnum.CRASH: 49,
    CymbalEnum.CHINA: 52,
}

# Slug por escala para nombres de archivo (ascii, sin espacios ni '_').
SCALE_SLUGS: dict[ScaleEnum, str] = {
    ScaleEnum.MAJOR: "major",
    ScaleEnum.MINOR_AEOLIAN: "eolian",
    ScaleEnum.HARMONIC_MINOR: "harmonicminor",
    ScaleEnum.PHRYGIAN: "phrygian",
    ScaleEnum.PHRYGIAN_DOMINANT: "phrygiandom",
}


def beats_to_ticks(beats: float) -> int:
    """Convierte beats a ticks enteros (redondeando una única vez)."""
    return round(beats * TICKS_PER_BEAT)


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
    arp_config: TrackConfig = field(default_factory=TrackConfig)   # reservado (pista fantasma)
    guitar_config: TrackConfig = field(default_factory=TrackConfig)
    drums_config: TrackConfig = field(default_factory=TrackConfig)
    double_time: bool = False           # platos a corcheas y caja en 2/4 (solo 4/4)
    cymbal: CymbalEnum = CymbalEnum.OPEN_HI_HAT
    cymbal_vary: bool = False           # variar el plato (aleatorio) en cada loop si repetitions > 1
    tail_vary: bool = False             # tail con melodía nueva (mismo ritmo, tónica inicial)
    fill: bool = False                  # fill (roll de caja + plato_alt) entre loops
    intro: bool = False                 # count-in de 4 golpes de hi-hat antes de la pieza


@dataclass
class NoteEvent:
    """Nota individual. Los tiempos se expresan en ticks enteros (exactos)."""
    pitch: int
    start_tick: int
    duration_ticks: int
    velocity: int


@dataclass
class SequenceData:
    """Salida de `engine_math`, consumida por `engine_midi` y la TUI.

    Los campos de resumen están en beats (para mostrar); el timing real
    de los eventos está en ticks enteros dentro de `NoteEvent`.
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
    intro_beats: float = 0.0            # beats del intro (count-in) antes de la pieza
