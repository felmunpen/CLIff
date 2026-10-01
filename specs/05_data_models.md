# Spec 05: Modelos de Datos y Constantes

## 1. Módulo `cliff/models.py`

```python
from dataclasses import dataclass, field
from enum import Enum

class ScaleEnum(str, Enum):
    MAJOR = "Mayor"
    MINOR_AEOLIAN = "Menor (Eólica)"
    HARMONIC_MINOR = "Menor Armónica"
    PHRYGIAN = "Frigio"
    PHRYGIAN_DOMINANT = "Frigio Dominante"

# Mapeo de notas MIDI relativas a C3 (MIDI 48)
SCALE_PITCHES: dict[ScaleEnum, list[int]] = {
    ScaleEnum.MAJOR: [48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72],
    ScaleEnum.MINOR_AEOLIAN: [48, 50, 51, 53, 55, 56, 58, 60, 62, 63, 65, 67, 68, 70, 72],
    ScaleEnum.HARMONIC_MINOR: [48, 50, 51, 53, 55, 56, 59, 60, 62, 63, 65, 67, 68, 71, 72],
    ScaleEnum.PHRYGIAN: [48, 49, 51, 53, 55, 56, 58, 60, 61, 63, 65, 67, 68, 70, 72],
    ScaleEnum.PHRYGIAN_DOMINANT: [48, 49, 52, 53, 55, 56, 58, 60, 61, 64, 65, 67, 68, 70, 72],
}

@dataclass
class TrackConfig:
    velocity: int = 100
    volume: int = 100

@dataclass
class SongConfig:
    bpm: int = 120
    total_bars: int = 8
    pattern_beats: float = 7.0
    pad_breath_bars: int = 0
    scale: ScaleEnum = ScaleEnum.MINOR_AEOLIAN
    allowed_durations: list[float] = field(default_factory=lambda: [1.0, 0.5, 0.25])
    max_jump: int = 3
    bass_config: TrackConfig = field(default_factory=TrackConfig)
    pad_config: TrackConfig = field(default_factory=TrackConfig)
    arp_config: TrackConfig = field(default_factory=TrackConfig)
    drums_config: TrackConfig = field(default_factory=TrackConfig)

@dataclass
class NoteEvent:
    pitch: int
    duration_beats: float
    start_beat: float
    velocity: int
```