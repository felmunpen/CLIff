"""Interfaz TUI: formularios `questionary` y vistas `rich`."""

import os
from datetime import date
from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import engine_midi, engine_math
from .models import (
    BEATS_PER_BAR,
    DURATION_OPTIONS,
    SCALE_SLUGS,
    TICKS_PER_BEAT,
    TONIC_SLUGS,
    CymbalEnum,
    DensityEnum,
    PadMode,
    PadRegister,
    ScaleEnum,
    SongConfig,
    TonicEnum,
    TrackConfig,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
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


def _show_polymetry_preview(console: Console, total_bars: int, pattern_beats: float) -> None:
    """Muestra el total de beats y un mapa de bloques (ciclos + tail)."""
    total_beats = total_bars * BEATS_PER_BAR
    full_loops, tail_ticks = engine_math.polymetry_summary(total_bars, pattern_beats)
    tail_beats = tail_ticks / TICKS_PER_BEAT

    # Resolución: 1 bloque = 1 beat; con fracciones de cuarto, 1 bloque = semicorchea.
    fractional = (pattern_beats % 1 != 0) or (tail_beats % 1 != 0)
    cells_per_beat = 4 if fractional else 1
    pattern_cells = round(pattern_beats * cells_per_beat)
    tail_cells = round(tail_beats * cells_per_beat)

    # Escalado: si la barra supera ~60 caracteres, se reduce proporcionalmente.
    n_blocks = full_loops + (1 if tail_cells else 0)
    width = full_loops * pattern_cells + tail_cells + (n_blocks - 1)
    max_width = 60
    if width > max_width:
        scale = width / max_width
        pattern_cells = max(1, round(pattern_cells / scale))
        tail_cells = max(1, round(tail_cells / scale)) if tail_cells else 0

    segments = []
    if full_loops:
        segments.append("[cyan]" + " ".join(["█" * pattern_cells] * full_loops) + "[/cyan]")
    if tail_cells:
        segments.append("[yellow]" + "█" * tail_cells + "[/yellow]")
    bar = " ".join(segments)

    tail_str = str(int(tail_beats)) if tail_beats.is_integer() else str(tail_beats)
    legend = (
        f"{full_loops} ciclos completos + tail de {tail_str} beats"
        if tail_beats
        else f"{full_loops} ciclos completos (sin residuo)"
    )

    console.print()
    console.print("[bold]Previsualización de polimetría[/bold]")
    console.print(f"{total_beats} beats totales ({total_bars} compases × {BEATS_PER_BAR})")
    console.print(bar)
    console.print(f"[dim]{legend}[/dim]")
    console.print()


def _collect_config(console: Console) -> SongConfig:
    # Paso 1: Configuración global
    bpm = int(questionary.text("BPM (40-240)", default="120", validate=_int_range(40, 240)).ask())
    console.print(f"[dim]Compás: {BEATS_PER_BAR}/4 (fijo en el MVP)[/dim]")
    total_bars = int(questionary.text("Duración en compases (4-64)", default="8",
                                      validate=_int_range(4, 64)).ask())
    console.print(f"[dim]{total_bars} compases × {BEATS_PER_BAR} = {total_bars * BEATS_PER_BAR} beats totales[/dim]")

    # Paso 2: Polimetría y Pad
    pattern_beats = float(questionary.text(
        "Duración del patrón en beats (ej. 3, 5, 7, 9.5)",
        default="7.0", validate=_validate_pattern_beats,
    ).ask())
    _show_polymetry_preview(console, total_bars, pattern_beats)
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
    tonic = TonicEnum(questionary.select(
        "Nota central (tónica)", choices=[t.value for t in TonicEnum],
    ).ask())
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
    # Double time solo tiene sentido en 4/4 (caja en 2 y 4). Guardado para
    # cuando el compás sea configurable.
    double_time = False
    if BEATS_PER_BAR == 4:
        double_time = questionary.confirm(
            "¿Double time? (platos a corcheas y caja en 2 y 4)", default=False,
        ).ask()
    cymbal = CymbalEnum(questionary.select(
        "Plato", choices=[c.value for c in CymbalEnum],
    ).ask())

    # Paso 4: Mezclador
    if questionary.confirm("¿Personalizar volumen y velocity de las pistas?", default=False).ask():
        track_configs = {}
        for label, key in (("Pad", "pad_config"), ("Bajo", "bass_config"),
                           ("Guitarra", "guitar_config"), ("Arpegiador", "arp_config"),
                           ("Percusión", "drums_config")):
            velocity = int(questionary.text(f"{label} — velocity (0-127)", default="100",
                                            validate=_int_range(0, 127)).ask())
            volume = int(questionary.text(f"{label} — volumen (0-100)", default="100",
                                          validate=_int_range(0, 100)).ask())
            track_configs[key] = TrackConfig(velocity=velocity, volume=volume)
        bass_config = track_configs["bass_config"]
        pad_config = track_configs["pad_config"]
        guitar_config = track_configs["guitar_config"]
        arp_config = track_configs["arp_config"]
        drums_config = track_configs["drums_config"]
    else:
        bass_config = pad_config = guitar_config = arp_config = drums_config = TrackConfig()

    # Paso 5: Lote
    variations = int(questionary.text("Variaciones a generar (1-5)", default="1",
                                      validate=_int_range(1, 5)).ask())

    config = SongConfig(
        bpm=bpm,
        total_bars=total_bars,
        pattern_beats=pattern_beats,
        pad_breath_bars=pad_breath_bars,
        tonic=tonic,
        scale=scale,
        allowed_durations=allowed_durations,
        max_jump=max_jump,
        density=density,
        pad_mode=pad_mode,
        pad_register=pad_register,
        bass_config=bass_config,
        pad_config=pad_config,
        arp_config=arp_config,
        guitar_config=guitar_config,
        drums_config=drums_config,
        double_time=double_time,
        cymbal=cymbal,
    )
    return config, variations


def _show_summary(console: Console, seq) -> None:
    table = Table(title="CLIff — Resumen de Polimetría Calculada", border_style="cyan")
    table.add_column("Métrica", style="bold")
    table.add_column("Valor")
    table.add_row("Beats Totales", f"{seq.total_beats} ({int(seq.total_beats / 4)} compases en 4/4)")
    table.add_row("Duración del Patrón", f"{seq.pattern_beats} beats")
    table.add_row("Repeticiones Completas", f"{seq.full_loops} ciclos ({seq.full_loops * seq.pattern_beats} beats)")
    table.add_row("Residuo (Tail)", f"{seq.tail_beats} beats")
    console.print(table)


def _build_prefix(config: SongConfig) -> str:
    """Construye el prefijo del nombre de archivo (sin número)."""
    date_str = date.today().strftime("%d%m%Y")
    compas = f"{BEATS_PER_BAR}4"
    return f"{TONIC_SLUGS[config.tonic]}_{SCALE_SLUGS[config.scale]}_{compas}_{config.bpm}bpm_{date_str}"


def _next_number(folder: str, prefix: str) -> int:
    """Devuelve el siguiente número de archivo libre para `prefix` en `folder`."""
    marker = prefix + "_"
    max_n = 0
    for name in os.listdir(folder):
        if name.startswith(marker) and name.endswith(".mid"):
            num_part = name[len(marker):-len(".mid")]
            if num_part.isdigit():
                max_n = max(max_n, int(num_part))
    return max_n + 1


def _export(console: Console, config: SongConfig, midis) -> None:
    out_dir = questionary.text("Carpeta de exportación", default=str(DEFAULT_OUTPUT)).ask()
    os.makedirs(out_dir, exist_ok=True)
    prefix = _build_prefix(config)
    n = _next_number(out_dir, prefix)
    for i, midi in enumerate(midis):
        midi_path = os.path.join(out_dir, f"{prefix}_{n + i}.mid")
        midi.save(midi_path)
        console.print(f"[green]Exportado:[/green] {midi_path}")


def _result_screen(console: Console, config: SongConfig, seq, midis) -> str:
    """Muestra el resumen y las acciones. Devuelve 'back' o 'quit'."""
    _show_summary(console, seq)
    if len(midis) > 1:
        console.print(f"[dim]Se generaron {len(midis)} variaciones.[/dim]")
    while True:
        action = questionary.select(
            "Acción",
            choices=["💾 Exportar", "↩ Volver", "✕ Salir"],
        ).ask()
        if action == "💾 Exportar":
            _export(console, config, midis)
        elif action == "↩ Volver":
            return "back"
        else:  # ✕ Salir
            return "quit"


def run() -> None:
    """Punto de entrada de la TUI."""
    console = Console()
    _show_header(console)
    while True:
        config, variations = _collect_config(console)
        sequences = [engine_math.generate_sequence(config) for _ in range(variations)]
        midis = [engine_midi.build_midi(config, seq) for seq in sequences]
        result = _result_screen(console, config, sequences[0], midis)
        if result == "quit":
            console.print("[cyan]¡Hasta pronto![/cyan]")
            break
        # else "back": volver a configurar
        console.print()
