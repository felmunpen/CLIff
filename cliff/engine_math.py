"""Lógica matemática: polimetría, densidad, riff melódico y construcción de pistas.

Puramente determinista (dado el RNG) y sin I/O ni dependencias MIDI.
Todo el cálculo de tiempos se hace en ticks enteros (sin coma flotante).
"""

import math
import random

from .models import (
    BEATS_PER_BAR,
    DENSITY_RANGES,
    PAD_REGISTER_OFFSET,
    SCALE_PITCHES,
    TICKS_PER_BEAT,
    DensityEnum,
    NoteEvent,
    PadMode,
    SequenceData,
    SongConfig,
    beats_to_ticks,
)


def resolve_density(density: DensityEnum, pattern_ticks: int, allowed_ticks: list[int]) -> int:
    """Devuelve el número de notas objetivo, acotado a la factibilidad."""
    lo, hi = DENSITY_RANGES[density]
    min_notes = math.ceil(pattern_ticks / max(allowed_ticks))
    max_notes = math.floor(pattern_ticks / min(allowed_ticks))
    target = random.randint(lo, hi)
    return max(min_notes, min(target, max_notes))


def generate_rhythm_pattern(pattern_ticks: int, allowed_ticks: list[int], target_notes: int) -> list[int]:
    """Genera exactamente `target_notes` duraciones (ticks) que suman `pattern_ticks`.

    Las duraciones intermedias se eligen del pool; la última es el resto exacto
    (ajuste dinámico) para cuadrar la suma sin desviación.
    """
    durations: list[int] = []
    remaining = pattern_ticks
    min_next = min(allowed_ticks)
    for i in range(target_notes):
        if i == target_notes - 1:
            durations.append(remaining)  # resto exacto
        else:
            notes_left = target_notes - 1 - i
            # reservar al menos min_next para cada nota restante
            cap = remaining - notes_left * min_next
            candidates = [d for d in allowed_ticks if d <= cap]
            d = random.choice(candidates if candidates else [min_next])
            durations.append(d)
            remaining -= d
    return durations


def build_tail_rhythm(pattern_rhythm_ticks: list[int], tail_ticks: int) -> list[int]:
    """Extrae el prefijo del patrón que suma exactamente `tail_ticks` (truncado)."""
    if tail_ticks <= 0:
        return []
    result: list[int] = []
    acc = 0
    for d in pattern_rhythm_ticks:
        if acc + d >= tail_ticks:
            result.append(tail_ticks - acc)
            return result
        result.append(d)
        acc += d
    return result


def generate_melody_indices(event_count: int, max_jump: int, scale_len: int) -> list[int]:
    """Genera una frase (riff) de `event_count` índices, empezando SIEMPRE en 0."""
    indices = [0]
    for _ in range(1, event_count):
        direction = random.choice([1, -1])
        step = random.randint(1, max_jump)
        new = indices[-1] + direction * step
        if new >= scale_len:
            new = (scale_len - 1) - (new - (scale_len - 1))
        elif new < 0:
            new = abs(new)
        indices.append(new)
    return indices


def build_bass_notes(pattern_rhythm_ticks, tail_rhythm_ticks, riff, full_loops, pattern_ticks,
                     scale_pitches, velocity) -> list[NoteEvent]:
    """Ensambla la línea del bajo: ciclos completos (riff repetido) + tail (truncado)."""
    notes: list[NoteEvent] = []
    # ciclos completos
    for loop in range(full_loops):
        start = loop * pattern_ticks
        for i, dur in enumerate(pattern_rhythm_ticks):
            notes.append(NoteEvent(pitch=scale_pitches[riff[i]], start_tick=start,
                                   duration_ticks=dur, velocity=velocity))
            start += dur
    # tail
    if tail_rhythm_ticks:
        start = full_loops * pattern_ticks
        for i, dur in enumerate(tail_rhythm_ticks):
            notes.append(NoteEvent(pitch=scale_pitches[riff[i]], start_tick=start,
                                   duration_ticks=dur, velocity=velocity))
            start += dur
    return notes


def build_pad_notes(scale_pitches, pad_mode, pad_register, total_ticks, pad_breath_bars,
                    velocity) -> list[NoteEvent]:
    """Construye las notas del Pad (mono/acorde, registro, drone/respiración)."""
    degrees = [0, 2, 4] if pad_mode == PadMode.CHORD else [0]
    offset = PAD_REGISTER_OFFSET[pad_register]
    pitches = [scale_pitches[d] + offset for d in degrees]

    notes: list[NoteEvent] = []
    if pad_breath_bars == 0:
        # Drone Infinito
        for p in pitches:
            notes.append(NoteEvent(pitch=p, start_tick=0, duration_ticks=total_ticks, velocity=velocity))
    else:
        breath_ticks = pad_breath_bars * BEATS_PER_BAR * TICKS_PER_BEAT
        start = 0
        while start < total_ticks:
            dur = min(breath_ticks, total_ticks - start)
            for p in pitches:
                notes.append(NoteEvent(pitch=p, start_tick=start, duration_ticks=dur, velocity=velocity))
            start += breath_ticks
    return notes


def build_percussion_notes(bass_notes, total_bars, velocity) -> list[NoteEvent]:
    """Construye la percusión: kick (clona el bajo), snare (2 y 4) y hi-hat (corcheas)."""
    notes: list[NoteEvent] = []
    hit_ticks = 120  # duración fija de los golpes

    # Kick: clona los ataques del bajo
    for b in bass_notes:
        notes.append(NoteEvent(pitch=36, start_tick=b.start_tick, duration_ticks=hit_ticks, velocity=velocity))

    # Snare: beats 2 y 4 de cada compás
    bar_ticks = BEATS_PER_BAR * TICKS_PER_BEAT
    for bar in range(total_bars):
        base = bar * bar_ticks
        notes.append(NoteEvent(pitch=38, start_tick=base + TICKS_PER_BEAT, duration_ticks=hit_ticks, velocity=velocity))
        notes.append(NoteEvent(pitch=38, start_tick=base + 3 * TICKS_PER_BEAT, duration_ticks=hit_ticks, velocity=velocity))

    # Hi-Hat: corcheas constantes
    for tick in range(0, total_bars * bar_ticks, TICKS_PER_BEAT // 2):
        notes.append(NoteEvent(pitch=42, start_tick=tick, duration_ticks=hit_ticks, velocity=velocity))

    notes.sort(key=lambda n: n.start_tick)
    return notes


def polymetry_summary(total_bars: int, pattern_beats: float) -> tuple[int, int]:
    """Devuelve (full_loops, tail_ticks) en ticks enteros.

    Fuente única de verdad del residuo polimétrico; la usan `generate_sequence`
    y la TUI para la previsualización.
    """
    total_ticks = total_bars * BEATS_PER_BAR * TICKS_PER_BEAT
    pattern_ticks = beats_to_ticks(pattern_beats)
    full_loops = total_ticks // pattern_ticks
    tail_ticks = total_ticks % pattern_ticks
    return full_loops, tail_ticks


def generate_sequence(config: SongConfig) -> SequenceData:
    """Orquesta el cálculo completo y devuelve un `SequenceData`."""
    total_ticks = config.total_bars * BEATS_PER_BAR * TICKS_PER_BEAT
    allowed_ticks = [beats_to_ticks(d) for d in config.allowed_durations]
    pattern_ticks = beats_to_ticks(config.pattern_beats)

    target_notes = resolve_density(config.density, pattern_ticks, allowed_ticks)
    pattern_rhythm_ticks = generate_rhythm_pattern(pattern_ticks, allowed_ticks, target_notes)

    full_loops, tail_ticks = polymetry_summary(config.total_bars, config.pattern_beats)
    tail_rhythm_ticks = build_tail_rhythm(pattern_rhythm_ticks, tail_ticks)

    scale_pitches = SCALE_PITCHES[config.scale]
    riff = generate_melody_indices(len(pattern_rhythm_ticks), config.max_jump, len(scale_pitches))

    bass_notes = build_bass_notes(
        pattern_rhythm_ticks, tail_rhythm_ticks, riff, full_loops, pattern_ticks,
        scale_pitches, config.bass_config.velocity,
    )
    pad_notes = build_pad_notes(
        scale_pitches, config.pad_mode, config.pad_register, total_ticks,
        config.pad_breath_bars, config.pad_config.velocity,
    )
    percussion_notes = build_percussion_notes(bass_notes, config.total_bars, config.drums_config.velocity)

    return SequenceData(
        total_beats=config.total_bars * BEATS_PER_BAR,
        pattern_beats=config.pattern_beats,
        full_loops=full_loops,
        tail_beats=tail_ticks / TICKS_PER_BEAT,
        pad_notes=pad_notes,
        bass_notes=bass_notes,
        arp_notes=[],
        percussion_notes=percussion_notes,
    )
