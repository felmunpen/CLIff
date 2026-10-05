"""Tests de precisión matemática para `cliff.engine_math`."""

import random
import unittest

from cliff import engine_math
from cliff.models import DensityEnum, ScaleEnum, SongConfig, TonicEnum, beats_to_ticks

TICKS = 480


class TestRhythmPattern(unittest.TestCase):
    def test_sum_and_count_exact(self):
        random.seed(42)
        allowed = [480, 360, 240, 120]
        for pattern_ticks in (1920, 3360, 4560):
            for density in (DensityEnum.LOW, DensityEnum.MEDIUM, DensityEnum.HIGH):
                target = engine_math.resolve_density(density, pattern_ticks, allowed)
                durations = engine_math.generate_rhythm_pattern(pattern_ticks, allowed, target)
                self.assertEqual(len(durations), target)
                self.assertEqual(sum(durations), pattern_ticks)
                # todas menos la última deben pertenecer al pool permitido
                for d in durations[:-1]:
                    self.assertIn(d, allowed)


class TestMelody(unittest.TestCase):
    def test_starts_at_tonic_and_in_bounds(self):
        random.seed(1)
        indices = engine_math.generate_melody_indices(12, 3, 15)
        self.assertEqual(indices[0], 0)
        self.assertTrue(all(0 <= i < 15 for i in indices))


class TestSequence(unittest.TestCase):
    def test_bass_covers_total(self):
        random.seed(7)
        config = SongConfig(total_bars=8, pattern_beats=7.0)
        seq = engine_math.generate_sequence(config)
        total_ticks = config.total_bars * 4 * TICKS
        self.assertEqual(sum(n.duration_ticks for n in seq.bass_notes), total_ticks)

    def test_polymetry_summary(self):
        random.seed(7)
        config = SongConfig(total_bars=8, pattern_beats=7.0)
        seq = engine_math.generate_sequence(config)
        pattern_ticks = beats_to_ticks(7.0)
        total_ticks = config.total_bars * 4 * TICKS
        self.assertEqual(seq.full_loops * pattern_ticks + round(seq.tail_beats * TICKS), total_ticks)

    def test_pad_drone_single_notes(self):
        random.seed(7)
        config = SongConfig(pad_breath_bars=0, pad_mode="Acorde")
        seq = engine_math.generate_sequence(config)
        total_ticks = config.total_bars * 4 * TICKS
        # acorde de 3 notas sostenido durante toda la pieza
        self.assertEqual(len(seq.pad_notes), 3)
        self.assertTrue(all(n.start_tick == 0 and n.duration_ticks == total_ticks for n in seq.pad_notes))


class TestPolymetrySummary(unittest.TestCase):
    def test_loops_and_tail(self):
        self.assertEqual(engine_math.polymetry_summary(8, 7.0), (4, 4 * TICKS))
        self.assertEqual(engine_math.polymetry_summary(8, 8.0), (4, 0))
        self.assertEqual(engine_math.polymetry_summary(4, 3.0), (5, 1 * TICKS))
        self.assertEqual(engine_math.polymetry_summary(8, 7.5), (4, 2 * TICKS))


class TestTonicTransposition(unittest.TestCase):
    def test_transposes_bass_and_pad(self):
        random.seed(1)
        config = SongConfig(tonic=TonicEnum.E, scale=ScaleEnum.MINOR_AEOLIAN,
                            pad_mode="Mono", pad_breath_bars=0)
        seq = engine_math.generate_sequence(config)
        # Tónica E (MIDI 52 en C3). Bajo dos octavas abajo -> E1 = 28.
        self.assertEqual(seq.bass_notes[0].pitch, 28)
        # Pad Mono (drone): raíz en registro Grave -> E3 = 52.
        self.assertEqual(len(seq.pad_notes), 1)
        self.assertEqual(seq.pad_notes[0].pitch, 52)


class TestPercussionDoubleTime(unittest.TestCase):
    def test_default_snare_beat_3(self):
        notes = engine_math.build_percussion_notes([], total_bars=2, velocity=100)
        snare = [n.start_tick for n in notes if n.pitch == 38]
        bar_ticks = 4 * TICKS
        expected = [bar * bar_ticks + 2 * TICKS for bar in range(2)]
        self.assertEqual(sorted(snare), expected)

    def test_double_time_snare_2_and_4(self):
        notes = engine_math.build_percussion_notes([], total_bars=2, velocity=100, double_time=True)
        snare = [n.start_tick for n in notes if n.pitch == 38]
        bar_ticks = 4 * TICKS
        expected = []
        for bar in range(2):
            base = bar * bar_ticks
            expected += [base + TICKS, base + 3 * TICKS]
        self.assertEqual(sorted(snare), expected)

    def test_default_hat_quarters(self):
        notes = engine_math.build_percussion_notes([], total_bars=2, velocity=100)
        hats = [n for n in notes if n.pitch == 42]
        self.assertEqual(len(hats), 2 * 4)

    def test_double_time_hat_eighths(self):
        notes = engine_math.build_percussion_notes([], total_bars=2, velocity=100, double_time=True)
        hats = [n for n in notes if n.pitch == 42]
        self.assertEqual(len(hats), 2 * 8)

    def test_sequence_double_time(self):
        random.seed(7)
        config = SongConfig(total_bars=8, pattern_beats=7.0, double_time=True)
        seq = engine_math.generate_sequence(config)
        snare = [n for n in seq.percussion_notes if n.pitch == 38]
        bar_ticks = 4 * TICKS
        self.assertEqual(len(snare), 16)
        self.assertTrue(all(n.start_tick % bar_ticks in (TICKS, 3 * TICKS) for n in snare))


if __name__ == "__main__":
    unittest.main()
