"""Construcción del archivo MIDI (en memoria) a partir de `SequenceData`."""

import mido

from .models import SequenceData, SongConfig


def _volume_cc7(volume_100: int) -> int:
    """Mapea volumen 0-100 a CC7 0-127."""
    return round(volume_100 * 127 / 100)


def _meta_track(config: SongConfig) -> mido.MidiTrack:
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("track_name", name="CLIff", time=0))
    tempo = round(60_000_000 / config.bpm)
    track.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))
    track.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    track.append(mido.MetaMessage("end_of_track", time=0))
    return track


def _note_track(name: str, channel: int, program, track_config, notes) -> mido.MidiTrack:
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("track_name", name=name, time=0))
    if program is not None:
        track.append(mido.Message("program_change", channel=channel, program=program, time=0))
    track.append(mido.Message("control_change", channel=channel, control=7,
                              value=_volume_cc7(track_config.volume), time=0))

    # Recolectar note_on / note_off con tick absoluto
    events = []
    for n in notes:
        events.append((n.start_tick, mido.Message("note_on", channel=channel,
                                                  note=n.pitch, velocity=n.velocity)))
        events.append((n.start_tick + n.duration_ticks,
                       mido.Message("note_off", channel=channel, note=n.pitch, velocity=0)))
    # En el mismo tick, note_off antes que note_on (evita notas atascadas)
    events.sort(key=lambda e: (e[0], 0 if e[1].type == "note_off" else 1))

    current = 0
    for tick, msg in events:
        msg.time = tick - current
        track.append(msg)
        current = tick

    track.append(mido.MetaMessage("end_of_track", time=0))
    return track


def build_midi(config: SongConfig, sequence: SequenceData) -> mido.MidiFile:
    """Construye el `MidiFile` con 4 pistas (Pad, Bass, Arpeggiator, Percussion)."""
    mid = mido.MidiFile(ticks_per_beat=480)
    mid.tracks.append(_meta_track(config))
    mid.tracks.append(_note_track("Pad", 0, 89, config.pad_config, sequence.pad_notes))
    mid.tracks.append(_note_track("Bass", 1, 33, config.bass_config, sequence.bass_notes))
    mid.tracks.append(_note_track("Arpeggiator", 2, 80, config.arp_config, sequence.arp_notes))
    mid.tracks.append(_note_track("Percussion", 9, None, config.drums_config, sequence.percussion_notes))
    return mid
