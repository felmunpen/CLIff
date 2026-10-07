"""Lógica matemática: polimetría, densidad, riff melódico y construcción de pistas.

Puramente determinista (dado el RNG) y sin I/O ni dependencias MIDI.
Todo el cálculo de tiempos se hace en ticks enteros (sin coma flotante).
"""

import math
import random

from .models import (
    BASS_PITCH_OFFSET,
    BEATS_PER_BAR,
    CYMBAL_PITCHES,
    DENSITY_RANGES,
    GUITAR_PITCH_OFFSET,
    PAD_REGISTER_OFFSET,
    SCALE_PITCHES,
    TICKS_PER_BEAT,
    TONIC_RECURRENCE_PROB,
    TONIC_SEMITONES,
    CymbalEnum,
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


def _legacy_leftover(pattern_ticks: int, allowed_ticks: list[int], target_notes: int) -> list[int]:
    """Fallback cuando no existe solución todo-en-pool (patrón no combinable).

    Reproduce el comportamiento anterior: la última nota absorbe el resto exacto,
    que puede quedar fuera del pool de duraciones permitidas.
    """
    durations: list[int] = []
    remaining = pattern_ticks
    min_next = min(allowed_ticks)
    for i in range(target_notes):
        if i == target_notes - 1:
            durations.append(remaining)
        else:
            notes_left = target_notes - 1 - i
            cap = remaining - notes_left * min_next
            candidates = [d for d in allowed_ticks if d <= cap]
            d = random.choice(candidates if candidates else [min_next])
            durations.append(d)
            remaining -= d
    return durations


def generate_rhythm_pattern(pattern_ticks: int, allowed_ticks: list[int], target_notes: int) -> list[int]:
    """Genera exactamente `target_notes` duraciones (ticks) que suman `pattern_ticks`.

    Búsqueda con retroceso aleatorizada: en cada paso se sortean las duraciones que
    dejan el resto rellenable por las notas restantes y se retrocede si un camino
    muere. Así todas las notas (incluida la última) pertenecen al pool. Si no existe
    solución (patrón no combinable con el pool), se degrada a `_legacy_leftover`.
    """
    allowed = sorted(set(allowed_ticks))
    min_next = allowed[0]
    max_next = allowed[-1]

    def search(remaining: int, notes_left: int, acc: list[int]):
        if notes_left == 0:
            return acc if remaining == 0 else None
        low_bound = remaining - (notes_left - 1) * max_next
        high_bound = remaining - (notes_left - 1) * min_next
        candidates = [d for d in allowed if low_bound <= d <= high_bound]
        random.shuffle(candidates)
        for d in candidates:
            found = search(remaining - d, notes_left - 1, acc + [d])
            if found is not None:
                return found
        return None

    solution = search(pattern_ticks, target_notes, [])
    if solution is not None:
        return solution
    return _legacy_leftover(pattern_ticks, allowed, target_notes)


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


def generate_melody_indices(event_count: int, max_jump: int, scale_len: int,
                            tonic_prob: float = 0.0) -> list[int]:
    """Genera una frase (riff) de `event_count` índices, empezando SIEMPRE en 0.

    Primero se genera el random walk puro (dirección ±1, paso 1..max_jump, rebote
    en bordes). Después, cada nota (salvo la primera, ya tónica) se sobreescribe a
    0 con probabilidad `tonic_prob`, superponiendo la recurrencia de la tónica sin
    alterar el contorno de las notas no tocadas.
    """
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
    for i in range(1, event_count):
        if random.random() < tonic_prob:
            indices[i] = 0
    return indices


def build_bass_notes(pattern_rhythm_ticks, tail_rhythm_ticks, riff, full_loops, pattern_ticks,
                     scale_pitches, velocity) -> list[NoteEvent]:
    """Ensambla la línea del bajo: ciclos completos (riff repetido) + tail (truncado)."""
    notes: list[NoteEvent] = []
    # ciclos completos
    for loop in range(full_loops):
        start = loop * pattern_ticks
        for i, dur in enumerate(pattern_rhythm_ticks):
            notes.append(NoteEvent(pitch=scale_pitches[riff[i]] + BASS_PITCH_OFFSET,
                                   start_tick=start, duration_ticks=dur, velocity=velocity))
            start += dur
    # tail
    if tail_rhythm_ticks:
        start = full_loops * pattern_ticks
        for i, dur in enumerate(tail_rhythm_ticks):
            notes.append(NoteEvent(pitch=scale_pitches[riff[i]] + BASS_PITCH_OFFSET,
                                   start_tick=start, duration_ticks=dur, velocity=velocity))
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


def build_percussion_notes(bass_notes, total_bars, velocity, double_time=False,
                           cymbal_pitch=CYMBAL_PITCHES[CymbalEnum.OPEN_HI_HAT]) -> list[NoteEvent]:
    """Construye la percusión: kick (clona el bajo), snare y plato.

    Por defecto: caja en el beat 3 y plato en negras. En double time: caja en
    beats 2 y 4 y plato en corcheas. La colocación de la caja asume compás 4/4;
    si en el futuro se soportan otras métricas, habrá que generalizar esta
    lógica por compás.
    """
    notes: list[NoteEvent] = []
    hit_ticks = 120  # duración fija de los golpes

    # Kick: clona los ataques del bajo
    for b in bass_notes:
        notes.append(NoteEvent(pitch=36, start_tick=b.start_tick, duration_ticks=hit_ticks, velocity=velocity))

    # Snare: default -> beat 3; double time -> beats 2 y 4
    bar_ticks = BEATS_PER_BAR * TICKS_PER_BEAT
    for bar in range(total_bars):
        base = bar * bar_ticks
        if double_time:
            notes.append(NoteEvent(pitch=38, start_tick=base + TICKS_PER_BEAT, duration_ticks=hit_ticks, velocity=velocity))
            notes.append(NoteEvent(pitch=38, start_tick=base + 3 * TICKS_PER_BEAT, duration_ticks=hit_ticks, velocity=velocity))
        else:
            notes.append(NoteEvent(pitch=38, start_tick=base + 2 * TICKS_PER_BEAT, duration_ticks=hit_ticks, velocity=velocity))

    # Plato: default -> negras; double time -> corcheas
    step = TICKS_PER_BEAT // 2 if double_time else TICKS_PER_BEAT
    for tick in range(0, total_bars * bar_ticks, step):
        notes.append(NoteEvent(pitch=cymbal_pitch, start_tick=tick, duration_ticks=hit_ticks, velocity=velocity))

    notes.sort(key=lambda n: n.start_tick)
    return notes


def build_guitar_notes(bass_notes, velocity) -> list[NoteEvent]:
    """Duplica la línea del bajo una octava por encima (C2) para la guitarra."""
    return [
        NoteEvent(pitch=n.pitch + GUITAR_PITCH_OFFSET,
                  start_tick=n.start_tick, duration_ticks=n.duration_ticks, velocity=velocity)
        for n in bass_notes
    ]


def tile_notes(notes: list[NoteEvent], repetitions: int, structure_ticks: int) -> list[NoteEvent]:
    """Repite una estructura (lista de notas) `repetitions` veces, desplazando cada
    copia `structure_ticks` ticks. Devuelve la misma lista si `repetitions == 1`."""
    if repetitions <= 1:
        return notes
    result: list[NoteEvent] = []
    for r in range(repetitions):
        offset = r * structure_ticks
        for n in notes:
            result.append(NoteEvent(pitch=n.pitch, start_tick=n.start_tick + offset,
                                    duration_ticks=n.duration_ticks, velocity=n.velocity))
    return result


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
    total_ticks = config.total_bars * BEATS_PER_BAR * TICKS_PER_BEAT  # una estructura
    piece_ticks = total_ticks * config.repetitions
    allowed_ticks = [beats_to_ticks(d) for d in config.allowed_durations]
    pattern_ticks = beats_to_ticks(config.pattern_beats)

    target_notes = resolve_density(config.density, pattern_ticks, allowed_ticks)
    pattern_rhythm_ticks = generate_rhythm_pattern(pattern_ticks, allowed_ticks, target_notes)

    full_loops, tail_ticks = polymetry_summary(config.total_bars, config.pattern_beats)
    tail_rhythm_ticks = build_tail_rhythm(pattern_rhythm_ticks, tail_ticks)

    scale_pitches = [p + TONIC_SEMITONES[config.tonic] for p in SCALE_PITCHES[config.scale]]
    riff = generate_melody_indices(
        len(pattern_rhythm_ticks), config.max_jump, len(scale_pitches),
        TONIC_RECURRENCE_PROB[config.tonic_recurrence],
    )

    bass_structure = build_bass_notes(
        pattern_rhythm_ticks, tail_rhythm_ticks, riff, full_loops, pattern_ticks,
        scale_pitches, config.bass_config.velocity,
    )
    bass_notes = tile_notes(bass_structure, config.repetitions, total_ticks)
    pad_notes = build_pad_notes(
        scale_pitches, config.pad_mode, config.pad_register, piece_ticks,
        config.pad_breath_bars, config.pad_config.velocity,
    )
    guitar_notes = build_guitar_notes(bass_notes, config.guitar_config.velocity)
    percussion_notes = build_percussion_notes(
        bass_notes, config.total_bars * config.repetitions, config.drums_config.velocity,
        config.double_time, CYMBAL_PITCHES[config.cymbal],
    )

    return SequenceData(
        total_beats=config.total_bars * BEATS_PER_BAR * config.repetitions,
        pattern_beats=config.pattern_beats,
        full_loops=full_loops,
        tail_beats=tail_ticks / TICKS_PER_BEAT,
        repetitions=config.repetitions,
        pad_notes=pad_notes,
        bass_notes=bass_notes,
        arp_notes=[],
        guitar_notes=guitar_notes,
        percussion_notes=percussion_notes,
    )
