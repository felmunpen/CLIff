"""Tests de precisión matemática para `cliff.engine_math`."""

import random
import unittest

from cliff import engine_math
from cliff.models import DensityEnum, ScaleEnum, SongConfig, TonicEnum, TonicRecurrence, beats_to_ticks

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
                # todas las notas (incluida la última) deben pertenecer al pool
                for d in durations:
                    self.assertIn(d, allowed)

    def test_last_note_in_pool(self):
        random.seed(42)
        allowed = [480, 360, 240, 120]
        for pattern_ticks in (1920, 3360, 4560):
            for density in (DensityEnum.LOW, DensityEnum.MEDIUM, DensityEnum.HIGH):
                target = engine_math.resolve_density(density, pattern_ticks, allowed)
                durations = engine_math.generate_rhythm_pattern(pattern_ticks, allowed, target)
                self.assertIn(durations[-1], allowed)

    def test_no_note_exceeds_max(self):
        random.seed(42)
        allowed = [480, 360, 240, 120]
        for pattern_ticks in (1920, 3360, 4560):
            for density in (DensityEnum.LOW, DensityEnum.MEDIUM, DensityEnum.HIGH):
                target = engine_math.resolve_density(density, pattern_ticks, allowed)
                durations = engine_math.generate_rhythm_pattern(pattern_ticks, allowed, target)
                self.assertTrue(all(d <= max(allowed) for d in durations))

    def test_property_feasible_configs(self):
        allowed = [480, 360, 240, 120]
        for seed in range(20):
            random.seed(seed)
            for pattern_ticks in (1920, 3360, 4560):
                for density in (DensityEnum.LOW, DensityEnum.MEDIUM, DensityEnum.HIGH):
                    target = engine_math.resolve_density(density, pattern_ticks, allowed)
                    durations = engine_math.generate_rhythm_pattern(pattern_ticks, allowed, target)
                    self.assertEqual(len(durations), target)
                    self.assertEqual(sum(durations), pattern_ticks)
                    for d in durations:
                        self.assertIn(d, allowed)

    def test_infeasible_falls_back(self):
        # 8 notas de {480, 120} no pueden sumar 3360: el backtracking degrada al
        # fallback, que mantiene suma y longitud exactas (la última nota puede
        # quedar fuera del pool).
        random.seed(1)
        durations = engine_math.generate_rhythm_pattern(3360, [480, 120], 8)
        self.assertEqual(len(durations), 8)
        self.assertEqual(sum(durations), 3360)
        for d in durations[:-1]:
            self.assertIn(d, [480, 120])

    def test_deterministic_under_seed(self):
        random.seed(5)
        first = engine_math.generate_rhythm_pattern(3360, [480, 360, 240, 120], 10)
        random.seed(5)
        second = engine_math.generate_rhythm_pattern(3360, [480, 360, 240, 120], 10)
        self.assertEqual(first, second)

    def test_variation_across_seeds(self):
        results = set()
        for seed in range(10):
            random.seed(seed)
            durations = engine_math.generate_rhythm_pattern(3360, [480, 360, 240, 120], 10)
            results.add(tuple(durations))
        self.assertGreater(len(results), 1)


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
        self.assertEqual(sum(n.duration_ticks for n in seq.bass_notes),
                         total_ticks * config.repetitions)

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
        total_ticks = config.total_bars * 4 * TICKS * config.repetitions
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
        hats = [n for n in notes if n.pitch == 46]
        self.assertEqual(len(hats), 2 * 4)

    def test_double_time_hat_eighths(self):
        notes = engine_math.build_percussion_notes([], total_bars=2, velocity=100, double_time=True)
        hats = [n for n in notes if n.pitch == 46]
        self.assertEqual(len(hats), 2 * 8)

    def test_sequence_double_time(self):
        random.seed(7)
        config = SongConfig(total_bars=8, pattern_beats=7.0, double_time=True)
        seq = engine_math.generate_sequence(config)
        snare = [n for n in seq.percussion_notes if n.pitch == 38]
        bar_ticks = 4 * TICKS
        self.assertEqual(len(snare), 16 * config.repetitions)
        self.assertTrue(all(n.start_tick % bar_ticks in (TICKS, 3 * TICKS) for n in snare))

    def test_cymbal_pitch_override(self):
        notes = engine_math.build_percussion_notes([], total_bars=1, velocity=100, cymbal_pitch=51)
        ride = [n for n in notes if n.pitch == 51]
        self.assertEqual(len(ride), 4)

    def test_default_cymbal_open_hihat(self):
        random.seed(7)
        config = SongConfig(total_bars=2)
        seq = engine_math.generate_sequence(config)
        hats = [n for n in seq.percussion_notes if n.pitch == 46]
        self.assertEqual(len(hats), 2 * 4 * config.repetitions)


class TestGuitar(unittest.TestCase):
    def test_follows_bass_one_octave_up(self):
        random.seed(7)
        config = SongConfig(total_bars=8, pattern_beats=7.0)
        seq = engine_math.generate_sequence(config)
        self.assertEqual(len(seq.guitar_notes), len(seq.bass_notes))
        for g, b in zip(seq.guitar_notes, seq.bass_notes):
            self.assertEqual(g.pitch, b.pitch + 12)
            self.assertEqual(g.start_tick, b.start_tick)
            self.assertEqual(g.duration_ticks, b.duration_ticks)


class TestRepetitions(unittest.TestCase):
    def test_bass_total_is_n_times_structure(self):
        random.seed(7)
        config = SongConfig(total_bars=8, pattern_beats=7.0, repetitions=3)
        seq = engine_math.generate_sequence(config)
        structure_ticks = config.total_bars * 4 * TICKS
        self.assertEqual(sum(n.duration_ticks for n in seq.bass_notes), structure_ticks * 3)

    def test_structure_resets_to_tonic(self):
        random.seed(7)
        config = SongConfig(total_bars=8, pattern_beats=7.0, repetitions=2)
        seq = engine_math.generate_sequence(config)
        structure_ticks = config.total_bars * 4 * TICKS
        first_pitch = seq.bass_notes[0].pitch
        second_starts = [n for n in seq.bass_notes if n.start_tick == structure_ticks]
        self.assertTrue(second_starts)
        self.assertTrue(all(n.pitch == first_pitch for n in second_starts))

    def test_percussion_spans_all_bars(self):
        random.seed(7)
        config = SongConfig(total_bars=4, pattern_beats=7.0, repetitions=2)
        seq = engine_math.generate_sequence(config)
        snare = [n for n in seq.percussion_notes if n.pitch == 38]
        self.assertEqual(len(snare), 4 * 2)  # 4 compases × 2 repeticiones

    def test_pad_drone_spans_full_piece(self):
        random.seed(7)
        config = SongConfig(pad_breath_bars=0, pad_mode="Mono", repetitions=3)
        seq = engine_math.generate_sequence(config)
        structure_ticks = config.total_bars * 4 * TICKS
        self.assertEqual(len(seq.pad_notes), 1)
        self.assertEqual(seq.pad_notes[0].duration_ticks, structure_ticks * 3)

    def test_repetitions_one_is_single_structure(self):
        random.seed(7)
        config = SongConfig(total_bars=8, pattern_beats=7.0, repetitions=1)
        seq = engine_math.generate_sequence(config)
        structure_ticks = config.total_bars * 4 * TICKS
        self.assertEqual(sum(n.duration_ticks for n in seq.bass_notes), structure_ticks)


class TestTonicRecurrence(unittest.TestCase):
    def test_full_probability_forces_all_tonics(self):
        random.seed(1)
        indices = engine_math.generate_melody_indices(8, 3, 15, tonic_prob=1.0)
        self.assertEqual(indices, [0] * 8)

    def test_zero_probability_is_pure_walk(self):
        random.seed(12345)
        indices = engine_math.generate_melody_indices(6, 3, 15, tonic_prob=0.0)
        self.assertEqual(indices, [0, 3, 5, 4, 1, 0])

    def test_monotonic_tonic_count(self):
        counts = []
        for p in (0.0, 0.45, 1.0):
            random.seed(12345)
            indices = engine_math.generate_melody_indices(6, 3, 15, tonic_prob=p)
            counts.append(sum(1 for i in indices if i == 0))
        self.assertEqual(counts, sorted(counts))  # no decrece
        self.assertEqual(counts[-1], 6)           # p=1.0 -> todas tónicas

    def test_first_note_always_tonic_and_in_bounds(self):
        for p in (0.0, 0.25, 0.45, 1.0):
            random.seed(9)
            indices = engine_math.generate_melody_indices(10, 5, 15, tonic_prob=p)
            self.assertEqual(indices[0], 0)
            self.assertTrue(all(0 <= i < 15 for i in indices))

    def test_recurrence_increases_tonics(self):
        # Mismo seed: el walk subyacente es idéntico, solo cambia la sobreescritura.
        random.seed(7)
        libre = engine_math.generate_sequence(SongConfig(tonic_recurrence=TonicRecurrence.LIBRE))
        random.seed(7)
        high = engine_math.generate_sequence(SongConfig(tonic_recurrence=TonicRecurrence.HIGH))
        self.assertEqual(len(libre.bass_notes), len(high.bass_notes))
        tonic_pitch = libre.bass_notes[0].pitch  # la tónica (índice 0)
        libre_tonics = sum(1 for n in libre.bass_notes if n.pitch == tonic_pitch)
        high_tonics = sum(1 for n in high.bass_notes if n.pitch == tonic_pitch)
        self.assertGreaterEqual(high_tonics, libre_tonics)


if __name__ == "__main__":
    unittest.main()
