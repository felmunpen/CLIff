"""Tests de precisión matemática para `cliff.engine_math`."""

import random
import unittest

from cliff import engine_math
from cliff.models import (
    CYMBAL_PITCHES,
    CymbalEnum,
    DensityEnum,
    ScaleEnum,
    SongConfig,
    TonicEnum,
    TonicRecurrence,
    beats_to_ticks,
)

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


class TestDensityResolution(unittest.TestCase):
    def test_no_all_quarter_collapse(self):
        # Regresión: con negra en el pool, ningún nivel debe colapsar a
        # "todo negras" (una única duración).
        allowed = [480, 240, 120]
        for density in (DensityEnum.LOW, DensityEnum.MEDIUM, DensityEnum.HIGH):
            random.seed(42)
            target = engine_math.resolve_density(density, 3360, allowed)
            durations = engine_math.generate_rhythm_pattern(3360, allowed, target)
            self.assertEqual(sum(durations), 3360)
            self.assertGreater(len(set(durations)), 1,
                               msg=f"{density} colapsó a una única duración")

    def test_levels_are_ordered(self):
        # A mayor densidad, más notas objetivo.
        allowed = [480, 240, 120]
        low = engine_math.resolve_density(DensityEnum.LOW, 3360, allowed)
        med = engine_math.resolve_density(DensityEnum.MEDIUM, 3360, allowed)
        high = engine_math.resolve_density(DensityEnum.HIGH, 3360, allowed)
        self.assertLessEqual(low, med)
        self.assertLessEqual(med, high)

    def test_single_duration_pool_is_exact(self):
        # Con una única duración, el objetivo es exactamente pattern_ticks / dur.
        self.assertEqual(engine_math.resolve_density(DensityEnum.MEDIUM, 3360, [480]), 7)


class TestCombinability(unittest.TestCase):
    def test_quarter_pattern_needs_odd_duration(self):
        self.assertTrue(engine_math.pattern_is_combinable(7.0, [1.0, 0.5, 0.25]))
        self.assertTrue(engine_math.pattern_is_combinable(7.5, [1.0, 0.5]))
        self.assertFalse(engine_math.pattern_is_combinable(7.25, [1.0, 0.5]))
        self.assertFalse(engine_math.pattern_is_combinable(7.75, [1.0, 0.5]))

    def test_odd_duration_restores_combinability(self):
        self.assertTrue(engine_math.pattern_is_combinable(7.25, [1.0, 0.5, 0.25]))
        self.assertTrue(engine_math.pattern_is_combinable(7.25, [1.0, 0.75]))


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


class TestTailVariation(unittest.TestCase):
    def _tail_notes(self, seq, structure_ticks, full_loops, pattern_ticks):
        tail_start = full_loops * pattern_ticks
        return [n for n in seq.bass_notes
                if tail_start <= n.start_tick < structure_ticks]

    def test_same_rhythm_different_pitches(self):
        random.seed(7)
        config = SongConfig(total_bars=8, pattern_beats=7.0, repetitions=1)
        seq = engine_math.generate_sequence(config)  # tail_vary=False

        random.seed(7)
        config_vary = SongConfig(total_bars=8, pattern_beats=7.0, repetitions=1, tail_vary=True)
        seq_vary = engine_math.generate_sequence(config_vary)

        pattern_ticks = beats_to_ticks(7.0)
        structure_ticks = config.total_bars * 4 * TICKS
        full_loops = seq.full_loops

        tail = self._tail_notes(seq, structure_ticks, full_loops, pattern_ticks)
        tail_vary = self._tail_notes(seq_vary, structure_ticks, full_loops, pattern_ticks)

        self.assertEqual(len(tail), len(tail_vary))
        # mismo ritmo (duraciones idénticas)
        self.assertEqual([n.duration_ticks for n in tail],
                         [n.duration_ticks for n in tail_vary])
        # misma primera nota (tónica)
        self.assertEqual(tail[0].pitch, tail_vary[0].pitch)
        # pitches distintos en algún punto del tail
        self.assertNotEqual([n.pitch for n in tail], [n.pitch for n in tail_vary])

    def test_tail_covers_tail_ticks(self):
        random.seed(7)
        config = SongConfig(total_bars=8, pattern_beats=7.0, repetitions=1, tail_vary=True)
        seq = engine_math.generate_sequence(config)
        self.assertEqual(round(seq.tail_beats * TICKS),
                         sum(n.duration_ticks for n in self._tail_notes(
                             seq, config.total_bars * 4 * TICKS, seq.full_loops,
                             beats_to_ticks(7.0))))

    def test_tail_vary_first_note_is_tonic(self):
        random.seed(3)
        config = SongConfig(total_bars=8, pattern_beats=7.0, repetitions=1, tail_vary=True)
        seq = engine_math.generate_sequence(config)
        tonic_pitch = seq.bass_notes[0].pitch
        tail = self._tail_notes(seq, config.total_bars * 4 * TICKS, seq.full_loops,
                                beats_to_ticks(7.0))
        self.assertEqual(tail[0].pitch, tonic_pitch)


class TestCymbalVariation(unittest.TestCase):
    def _loop_pitches(self, seq, structure_ticks):
        cymbal_pitches = set(CYMBAL_PITCHES.values())
        loops = {}
        for n in seq.percussion_notes:
            if n.pitch in cymbal_pitches:
                loop = n.start_tick // structure_ticks
                loops.setdefault(loop, set()).add(n.pitch)
        return loops

    def test_single_repetition_is_single_cymbal(self):
        random.seed(1)
        config = SongConfig(total_bars=4, repetitions=1, cymbal_vary=True)
        seq = engine_math.generate_sequence(config)
        structure_ticks = config.total_bars * 4 * TICKS
        loops = self._loop_pitches(seq, structure_ticks)
        self.assertEqual(len(loops), 1)
        self.assertEqual(loops[0], {CYMBAL_PITCHES[config.cymbal]})

    def test_variation_first_loop_is_chosen(self):
        random.seed(1)
        config = SongConfig(total_bars=4, repetitions=3, cymbal_vary=True)
        seq = engine_math.generate_sequence(config)
        structure_ticks = config.total_bars * 4 * TICKS
        loops = self._loop_pitches(seq, structure_ticks)
        self.assertEqual(len(loops), 3)
        self.assertEqual(loops[0], {CYMBAL_PITCHES[config.cymbal]})

    def test_variation_no_consecutive_repeat(self):
        random.seed(1)
        config = SongConfig(total_bars=4, repetitions=3, cymbal_vary=True)
        seq = engine_math.generate_sequence(config)
        structure_ticks = config.total_bars * 4 * TICKS
        loops = self._loop_pitches(seq, structure_ticks)
        pitches = [next(iter(loops[i])) for i in sorted(loops)]
        for a, b in zip(pitches, pitches[1:]):
            self.assertNotEqual(a, b)

    def test_default_no_variation(self):
        random.seed(1)
        config = SongConfig(total_bars=4, repetitions=3)  # cymbal_vary=False por defecto
        seq = engine_math.generate_sequence(config)
        structure_ticks = config.total_bars * 4 * TICKS
        loops = self._loop_pitches(seq, structure_ticks)
        pitches = {next(iter(s)) for s in loops.values()}
        self.assertEqual(pitches, {CYMBAL_PITCHES[config.cymbal]})

    def test_cymbal_pitches_per_loop(self):
        random.seed(1)
        pitches = engine_math.cymbal_pitches_per_loop(CymbalEnum.OPEN_HI_HAT, 5)
        self.assertEqual(pitches[0], CYMBAL_PITCHES[CymbalEnum.OPEN_HI_HAT])
        self.assertEqual(len(pitches), 5)
        for a, b in zip(pitches, pitches[1:]):
            self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
