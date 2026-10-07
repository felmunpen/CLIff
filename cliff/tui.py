"""Interfaz TUI: formularios `questionary` y vistas `rich`."""

import os
from datetime import date
from pathlib import Path

import questionary
from prompt_toolkit.key_binding import KeyBindings
from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

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
    TonicRecurrence,
    TrackConfig,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "output"

THEME = Theme({
    "cliff.brand": "bold cyan",
    "cliff.accent": "magenta",
    "cliff.muted": "dim",
    "cliff.warn": "yellow",
    "cliff.ok": "green",
})


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


def _format_step_value(value: float, as_int: bool) -> str:
    """Formatea un valor numérico para escribirlo en el buffer del prompt."""
    if as_int:
        return str(int(round(value)))
    return str(round(value, 2))


def _step_key_bindings(lo: float, hi: float, step: float, as_int: bool):
    """Key bindings ↑/↓ para incrementar/decrementar el valor de un prompt numérico."""
    kb = KeyBindings()

    def _step(event, direction: int) -> None:
        buffer = event.current_buffer
        try:
            value = float(buffer.text.strip())
        except ValueError:
            value = lo
        value = max(lo, min(hi, value + direction * step))
        buffer.text = _format_step_value(value, as_int)
        buffer.cursor_position = len(buffer.text)

    @kb.add("up")
    def _(event):
        _step(event, +1)

    @kb.add("down")
    def _(event):
        _step(event, -1)

    return kb


def _show_header(console: Console) -> None:
    console.print()
    console.print(Panel(
        Group(
            Text("CLIff", style="bold cyan", justify="center"),
            Text("Polymetric MIDI Generator", style="italic", justify="center"),
            Text("≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈", style="magenta", justify="center"),
            Text("algorithmic riffs · in your terminal", style="dim", justify="center"),
        ),
        border_style="cyan",
        padding=(1, 2),
        width=52,
    ))
    console.print()


def _section(console: Console, title: str) -> None:
    console.print()
    console.print(Rule(f"[bold cyan]{title}[/bold cyan]", style="dim"))
    console.print()


def _show_polymetry_preview(console: Console, total_bars: int, pattern_beats: float) -> None:
    """Muestra el total de beats y un mapa de bloques (ciclos + tail) de una estructura."""
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
    console.print(f"{total_beats} beats por estructura ({total_bars} compases × {BEATS_PER_BAR})")
    console.print(bar)
    console.print(f"[dim]{legend}[/dim]")
    console.print()


def _collect_config(console: Console) -> SongConfig:
    # Paso 1: Configuración global
    _section(console, "Configuración Global")
    bpm = int(questionary.text("BPM (40-240)", default="120", validate=_int_range(40, 240),
                               key_bindings=_step_key_bindings(40, 240, 1, True)).ask())
    console.print(f"[dim]Compás: {BEATS_PER_BAR}/4 (fijo en el MVP)[/dim]")
    total_bars = int(questionary.text("Duración en compases (4-64)", default="4",
                                      validate=_int_range(4, 64),
                                      key_bindings=_step_key_bindings(4, 64, 1, True)).ask())
    console.print(f"[dim]{total_bars} compases × {BEATS_PER_BAR} "
                  f"= {total_bars * BEATS_PER_BAR} beats por estructura[/dim]")

    # Paso 2: Polimetría y Pad
    _section(console, "Estructura")
    pattern_beats = float(questionary.text(
        "Duración del patrón en beats (ej. 3, 5, 7, 9.5)",
        default="7.0", validate=_validate_pattern_beats,
        key_bindings=_step_key_bindings(0.25, 32.0, 0.25, False),
    ).ask())
    _show_polymetry_preview(console, total_bars, pattern_beats)
    repetitions = int(questionary.text(
        "Número de loops (1-8)",
        default="2", validate=_int_range(1, 8),
        key_bindings=_step_key_bindings(1, 8, 1, True),
    ).ask())
    pad_breath_bars = int(questionary.text(
        "Respiración del Pad en compases (0 = Drone Infinito, 1-8)",
        default="0", validate=_int_range(0, 8),
        key_bindings=_step_key_bindings(0, 8, 1, True),
    ).ask())
    pad_mode = PadMode(questionary.select(
        "Modo del Pad", choices=[m.value for m in PadMode],
    ).ask())
    pad_register = PadRegister(questionary.select(
        "Registro del Pad", choices=[r.value for r in PadRegister],
    ).ask())

    # Paso 3: Reglas algorítmicas
    _section(console, "Reglas Algorítmicas")
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
                                    validate=_int_range(1, 5),
                                    key_bindings=_step_key_bindings(1, 5, 1, True)).ask())
    density = DensityEnum(questionary.select(
        "Densidad", choices=[d.value for d in DensityEnum],
    ).ask())
    tonic_recurrence = TonicRecurrence(questionary.select(
        "Recurrencia de tónica", choices=[r.value for r in TonicRecurrence],
        default=TonicRecurrence.MEDIUM.value,
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
    _section(console, "Mezclador")
    if questionary.confirm("¿Personalizar volumen y velocity de las pistas?", default=False).ask():
        track_configs = {}
        for label, key in (("Pad", "pad_config"), ("Bajo", "bass_config"),
                           ("Guitarra", "guitar_config"), ("Arpegiador", "arp_config"),
                           ("Percusión", "drums_config")):
            velocity = int(questionary.text(f"{label} — velocity (0-127)", default="100",
                                            validate=_int_range(0, 127),
                                            key_bindings=_step_key_bindings(0, 127, 1, True)).ask())
            volume = int(questionary.text(f"{label} — volumen (0-100)", default="100",
                                          validate=_int_range(0, 100),
                                          key_bindings=_step_key_bindings(0, 100, 1, True)).ask())
            track_configs[key] = TrackConfig(velocity=velocity, volume=volume)
        bass_config = track_configs["bass_config"]
        pad_config = track_configs["pad_config"]
        guitar_config = track_configs["guitar_config"]
        arp_config = track_configs["arp_config"]
        drums_config = track_configs["drums_config"]
    else:
        bass_config = pad_config = guitar_config = arp_config = drums_config = TrackConfig()

    # Paso 5: Lote
    _section(console, "Lote")
    variations = int(questionary.text("Variaciones a generar (1-5)", default="1",
                                      validate=_int_range(1, 5),
                                      key_bindings=_step_key_bindings(1, 5, 1, True)).ask())

    config = SongConfig(
        bpm=bpm,
        total_bars=total_bars,
        repetitions=repetitions,
        pattern_beats=pattern_beats,
        pad_breath_bars=pad_breath_bars,
        tonic=tonic,
        scale=scale,
        allowed_durations=allowed_durations,
        max_jump=max_jump,
        density=density,
        tonic_recurrence=tonic_recurrence,
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


def _show_summary(console: Console, config: SongConfig, seq) -> None:
    structure_beats = int(seq.total_beats // seq.repetitions)
    durations = ", ".join(name for name, beats in DURATION_OPTIONS
                          if beats in config.allowed_durations)

    main = Table(box=box.ROUNDED, title="CLIff — Resumen", border_style="cyan",
                 caption="Polimetría y parámetros de la pieza")
    main.add_column("Métrica", style="bold cyan")
    main.add_column("Valor", style="white")
    main.add_row("Beats por Estructura", f"{structure_beats} "
                                         f"({structure_beats // BEATS_PER_BAR} compases en 4/4)")
    main.add_row("Loops", f"{seq.repetitions}")
    main.add_row("Duración del Patrón", f"{seq.pattern_beats} beats")
    main.add_row("Ciclos Completos (por estructura)",
                 f"{seq.full_loops} ciclos ({seq.full_loops * seq.pattern_beats} beats)")
    main.add_row("Residuo / Tail (por estructura)", f"{seq.tail_beats} beats")
    main.add_row("BPM", f"{config.bpm}")
    main.add_row("Tónica", f"{config.tonic.value}")
    main.add_row("Escala", f"{config.scale.value}")
    main.add_row("Densidad", f"{config.density.value}")
    main.add_row("Recurrencia de tónica", f"{config.tonic_recurrence.value}")
    main.add_row("Salto melódico máximo", f"{config.max_jump}")
    main.add_row("Duraciones permitidas", durations)
    main.add_row("Plato", f"{config.cymbal.value}")
    main.add_row("Double time", "Sí" if config.double_time else "No")

    mixer = Table(box=box.SIMPLE, title="Mezclador", border_style="dim")
    mixer.add_column("Pista", style="bold")
    mixer.add_column("Instrumento", style="dim")
    mixer.add_column("Velocity", justify="right")
    mixer.add_column("Volumen", justify="right")
    for label, instrument, track in (
        ("Pad", "Pad 2 (Warm)", config.pad_config),
        ("Bajo", "Finger Bass", config.bass_config),
        ("Guitarra", "Overdriven Guitar", config.guitar_config),
        ("Arpegiador", "Square Lead", config.arp_config),
        ("Percusión", "GM Drums", config.drums_config),
    ):
        mixer.add_row(label, instrument, str(track.velocity), str(track.volume))

    console.print(main)
    console.print()
    console.print(mixer)


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


def _progress(console: Console):
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    )


def _export(console: Console, config: SongConfig, midis) -> None:
    out_dir = questionary.text("Carpeta de exportación", default=str(DEFAULT_OUTPUT)).ask()
    os.makedirs(out_dir, exist_ok=True)
    prefix = _build_prefix(config)
    n = _next_number(out_dir, prefix)
    paths = []
    with _progress(console) as progress:
        task = progress.add_task("[cyan]Exportando...", total=len(midis))
        for i, midi in enumerate(midis):
            midi_path = os.path.join(out_dir, f"{prefix}_{n + i}.mid")
            midi.save(midi_path)
            paths.append(midi_path)
            progress.advance(task)
    for midi_path in paths:
        console.print(f"[green]Exportado:[/green] {midi_path}")


def _result_screen(console: Console, config: SongConfig, seq, midis) -> str:
    """Muestra el resumen y las acciones. Devuelve 'back' o 'quit'."""
    _show_summary(console, config, seq)
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
    console = Console(theme=THEME)
    _show_header(console)
    while True:
        config, variations = _collect_config(console)
        with _progress(console) as progress:
            task = progress.add_task("[cyan]Generando variaciones...", total=variations)
            sequences = []
            midis = []
            for _ in range(variations):
                seq = engine_math.generate_sequence(config)
                sequences.append(seq)
                midis.append(engine_midi.build_midi(config, seq))
                progress.advance(task)
        result = _result_screen(console, config, sequences[0], midis)
        if result == "quit":
            console.print("[cyan]¡Hasta pronto![/cyan]")
            break
        # else "back": volver a configurar
        console.print()
