"""Interfaz TUI: formularios `questionary` y vistas `rich`."""

import os
from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import engine_audio, engine_midi, engine_math
from .models import (
    DURATION_OPTIONS,
    DensityEnum,
    PadMode,
    PadRegister,
    ScaleEnum,
    SongConfig,
    TrackConfig,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SF2 = PROJECT_ROOT / "assets" / "default.sf2"
DEFAULT_OUTPUT = PROJECT_ROOT / "output"


def _int_range(lo: int, hi: int):
    def validate(text: str):
        try:
            value = int(text)
        except ValueError:
            return "Debe ser un número entero."
        if not (lo <= value <= hi):
            return f"Debe estar entre {lo} y {hi}."
        return True
    return validate


def _validate_pattern_beats(text: str):
    try:
        value = float(text)
    except ValueError:
        return "Debe ser un número."
    if value <= 0:
        return "Debe ser mayor que 0."
    if abs(value * 4 - round(value * 4)) > 1e-6:
        return "Debe ser múltiplo de 0.25 (semicorchea)."
    return True


def _show_header(console: Console) -> None:
    console.print()
    console.print(Panel.fit(
        "[bold cyan]CLIff[/bold cyan] — [italic]Polymetric MIDI Generator[/italic]",
        border_style="cyan",
    ))
    console.print()


def _collect_config(console: Console) -> SongConfig:
    # Paso 1: Configuración global
    bpm = int(questionary.text("BPM (40-240)", default="120", validate=_int_range(40, 240)).ask())
    total_bars = int(questionary.text("Duración en compases (4-64)", default="8",
                                      validate=_int_range(4, 64)).ask())

    # Paso 2: Polimetría y Pad
    pattern_beats = float(questionary.text(
        "Duración del patrón en beats (ej. 3, 5, 7, 9.5)",
        default="7.0", validate=_validate_pattern_beats,
    ).ask())
    pad_breath_bars = int(questionary.text(
        "Respiración del Pad en compases (0 = Drone Infinito, 1-8)",
        default="0", validate=_int_range(0, 8),
    ).ask())
    pad_mode = PadMode(questionary.select(
        "Modo del Pad", choices=[m.value for m in PadMode],
    ).ask())
    pad_register = PadRegister(questionary.select(
        "Registro del Pad", choices=[r.value for r in PadRegister],
    ).ask())

    # Paso 3: Reglas algorítmicas
    scale = ScaleEnum(questionary.select(
        "Escala", choices=[s.value for s in ScaleEnum],
    ).ask())
    duration_choices = [
        questionary.Choice(f"{name} [{value}]", value=value)
        for name, value in DURATION_OPTIONS
    ]
    allowed_durations = questionary.checkbox(
        "Duraciones permitidas", choices=duration_choices,
    ).ask()
    while not allowed_durations:
        console.print("[yellow]Selecciona al menos una duración.[/yellow]")
        allowed_durations = questionary.checkbox(
            "Duraciones permitidas", choices=duration_choices,
        ).ask()
    max_jump = int(questionary.text("Salto melódico máximo (1-5)", default="3",
                                    validate=_int_range(1, 5)).ask())
    density = DensityEnum(questionary.select(
        "Densidad", choices=[d.value for d in DensityEnum],
    ).ask())

    # Paso 4: Mezclador
    track_configs = {}
    for label, key in (("Pad", "pad_config"), ("Bajo", "bass_config"),
                       ("Arpegiador", "arp_config"), ("Percusión", "drums_config")):
        velocity = int(questionary.text(f"{label} — velocity (0-127)", default="100",
                                        validate=_int_range(0, 127)).ask())
        volume = int(questionary.text(f"{label} — volumen (0-100)", default="100",
                                      validate=_int_range(0, 100)).ask())
        track_configs[key] = TrackConfig(velocity=velocity, volume=volume)

    return SongConfig(
        bpm=bpm,
        total_bars=total_bars,
        pattern_beats=pattern_beats,
        pad_breath_bars=pad_breath_bars,
        scale=scale,
        allowed_durations=allowed_durations,
        max_jump=max_jump,
        density=density,
        pad_mode=pad_mode,
        pad_register=pad_register,
        bass_config=track_configs["bass_config"],
        pad_config=track_configs["pad_config"],
        arp_config=track_configs["arp_config"],
        drums_config=track_configs["drums_config"],
    )


def _show_summary(console: Console, seq) -> None:
    table = Table(title="CLIff — Resumen de Polimetría Calculada", border_style="cyan")
    table.add_column("Métrica", style="bold")
    table.add_column("Valor")
    table.add_row("Beats Totales", f"{seq.total_beats} ({int(seq.total_beats / 4)} compases en 4/4)")
    table.add_row("Duración del Patrón", f"{seq.pattern_beats} beats")
    table.add_row("Repeticiones Completas", f"{seq.full_loops} ciclos ({seq.full_loops * seq.pattern_beats} beats)")
    table.add_row("Residuo (Tail)", f"{seq.tail_beats} beats")
    console.print(table)


def _pattern_str(pattern_beats: float) -> str:
    return str(int(pattern_beats)) if pattern_beats.is_integer() else str(pattern_beats)


def _ensure_wav(midi, tmpdir: str, console: Console):
    """Renderiza (y cachea) el WAV de preescucha en el directorio temporal."""
    wav_tmp = os.path.join(tmpdir, "current.wav")
    if os.path.exists(wav_tmp):
        return wav_tmp
    if not DEFAULT_SF2.exists():
        console.print(f"[yellow]No se encontró {DEFAULT_SF2}; no se puede preescuchar.[/yellow]")
        return None
    midi_tmp = os.path.join(tmpdir, "current.mid")
    midi.save(midi_tmp)
    if not engine_audio.render_midi_to_wav(midi_tmp, str(DEFAULT_SF2), wav_tmp):
        console.print("[red]Error al renderizar el audio (¿FluidSynth instalado?).[/red]")
        return None
    return wav_tmp


def _export(console: Console, config: SongConfig, midi) -> None:
    out_dir = questionary.text("Carpeta de exportación", default=str(DEFAULT_OUTPUT)).ask()
    os.makedirs(out_dir, exist_ok=True)
    base = f"cliff_{config.bpm}bpm_p{_pattern_str(config.pattern_beats)}"
    midi_path = os.path.join(out_dir, base + ".mid")
    wav_path = os.path.join(out_dir, base + ".wav")
    midi.save(midi_path)
    console.print(f"[green]Exportado:[/green] {midi_path}")
    if DEFAULT_SF2.exists():
        if engine_audio.render_midi_to_wav(midi_path, str(DEFAULT_SF2), wav_path):
            console.print(f"[green]Exportado:[/green] {wav_path}")
        else:
            console.print("[yellow]No se pudo renderizar el WAV (¿FluidSynth instalado?).[/yellow]")
    else:
        console.print(f"[yellow]No se encontró {DEFAULT_SF2}; WAV no renderizado.[/yellow]")


def _result_screen(console: Console, config: SongConfig, seq, midi, tmpdir: str) -> str:
    """Muestra el resumen y las acciones. Devuelve 'back' o 'quit'."""
    _show_summary(console, seq)
    while True:
        action = questionary.select(
            "Acción",
            choices=["▶ Play", "💾 Exportar", "↩ Volver", "✕ Salir"],
        ).ask()
        if action == "▶ Play":
            wav = _ensure_wav(midi, tmpdir, console)
            if wav:
                engine_audio.play_audio(wav)
        elif action == "💾 Exportar":
            _export(console, config, midi)
        elif action == "↩ Volver":
            return "back"
        else:  # ✕ Salir
            return "quit"


def run(tmpdir: str) -> None:
    """Punto de entrada de la TUI. `tmpdir` es el directorio temporal de trabajo."""
    console = Console()
    _show_header(console)
    while True:
        config = _collect_config(console)
        sequence = engine_math.generate_sequence(config)
        midi = engine_midi.build_midi(config, sequence)
        result = _result_screen(console, config, sequence, midi, tmpdir)
        if result == "quit":
            console.print("[cyan]¡Hasta pronto![/cyan]")
            break
        # else "back": volver a configurar
        console.print()
