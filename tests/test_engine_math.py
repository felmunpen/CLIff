"""Tests de precisión matemática para `cliff.engine_math`."""

import random
import unittest

from cliff import engine_math
from cliff.models import DensityEnum, SongConfig, beats_to_ticks

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


if __name__ == "__main__":
    unittest.main()
