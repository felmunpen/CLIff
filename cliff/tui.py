"""Interfaz TUI: formularios `questionary` y vistas `rich`."""

import os
from datetime import date
from pathlib import Path

import questionary
from questionary import Style
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.keys import Keys
from rich import box
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
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

TONIC_VALUES = [t.value for t in TonicEnum]

THEME = Theme({
    "cliff.brand": "bold #33ff33",
    "cliff.accent": "#33ff33",
    "cliff.info": "#5fd7d7",
    "cliff.value": "#d8ffd8",
    "cliff.muted": "dim",
    "cliff.warn": "#ffbf00",
    "cliff.ok": "#33ff33",
})

QUESTIONARY_STYLE = Style([
    ("qmark", "fg:#33ff33 bold"),
    ("question", "fg:#33ff33 bold"),
    ("answer", "fg:#33ff33"),
    ("pointer", "fg:#33ff33 bold"),
    ("highlighted", "fg:#33ff33 bold"),
    ("selected", "fg:#33ff33 bold"),
    ("instruction", "fg:#6a6a6a"),
    ("text", "fg:#d8ffd8"),
])

QMARK = "■"


class _Quit(Exception):
    """Señal interna: el usuario pidió salir del programa."""


def _bind_quit(question):
    """Añade Ctrl+G para salir en cualquier pregunta (excepción `_Quit`)."""
    quit_kb = KeyBindings()

    @quit_kb.add(Keys.ControlG)
    def _(event):
        event.app.exit(exception=_Quit())

    question.application.key_bindings = merge_key_bindings(
        [quit_kb, question.application.key_bindings]
    )
    return question


def _q_text(*args, **kwargs):
    kwargs.setdefault("style", QUESTIONARY_STYLE)
    kwargs.setdefault("qmark", QMARK)
    return _bind_quit(questionary.text(*args, **kwargs))


def _q_confirm(*args, **kwargs):
    kwargs.setdefault("style", QUESTIONARY_STYLE)
    kwargs.setdefault("qmark", QMARK)
    return _bind_quit(questionary.confirm(*args, **kwargs))


def _q_select(*args, **kwargs):
    kwargs.setdefault("style", QUESTIONARY_STYLE)
    kwargs.setdefault("qmark", QMARK)
    return _bind_quit(questionary.select(*args, **kwargs))


def _q_checkbox(*args, **kwargs):
    kwargs.setdefault("style", QUESTIONARY_STYLE)
    kwargs.setdefault("qmark", QMARK)
    return _bind_quit(questionary.checkbox(*args, **kwargs))


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


def _normalize_tonic(text: str) -> str:
    return text.strip().upper().replace("♯", "#").replace("♭", "#")


def _validate_tonic(text: str):
    if _normalize_tonic(text) in TONIC_VALUES:
        return True
    return f"Debe ser una de: {', '.join(TONIC_VALUES)}."


def _parse_tonic(text: str) -> TonicEnum:
    return TonicEnum(_normalize_tonic(text))


def _tonic_key_bindings():
    """Key bindings ↑/↓ para subir/bajar el pitch de la tónica (cíclico)."""
    kb = KeyBindings()

    def _step(event, direction: int) -> None:
        buffer = event.current_buffer
        try:
            idx = TONIC_VALUES.index(_normalize_tonic(buffer.text))
        except ValueError:
            idx = 0
        idx = max(0, min(len(TONIC_VALUES) - 1, idx + direction))
        buffer.text = TONIC_VALUES[idx]
        buffer.cursor_position = len(buffer.text)

    @kb.add("up")
    def _(event):
        _step(event, +1)

    @kb.add("down")
    def _(event):
        _step(event, -1)

    return kb


class _Back(Exception):
    """Señal interna: el usuario pidió retroceder a la pregunta anterior."""


def _ask(question):
    """Pregunta con `questionary`; Ctrl+C (KeyboardInterrupt) retrocede una pregunta."""
    try:
        return question.unsafe_ask()
    except KeyboardInterrupt:
        raise _Back from None


def _run_steps(steps):
    """Ejecuta pasos con navegación atrás. Devuelve True si se retrocedió del primero."""
    i = 0
    while 0 <= i < len(steps):
        try:
            steps[i]()
        except _Back:
            i -= 1
            continue
        i += 1
    return i < 0


def _run_sections(console: Console, sections):
    """Ejecuta secciones (título + pasos) con navegación atrás, limpiando por sección."""
    flat = []
    sec_of = []
    for si, (_, steps) in enumerate(sections):
        for step in steps:
            flat.append(step)
            sec_of.append(si)

    i = 0
    last_sec = -1
    while 0 <= i < len(flat):
        sec = sec_of[i]
        if sec != last_sec:
            _clear_screen(console)
            _show_header_compact(console)
            _section(console, sections[sec][0], sec + 1, len(sections))
            last_sec = sec
        try:
            flat[i]()
        except _Back:
            i -= 1
            continue
        i += 1
    return i < 0


def _show_header(console: Console) -> None:
    console.print()
    console.print(Text("CLIff", style="cliff.brand"))
    console.print(Text("Polymetric MIDI Generator", style="italic"))
    console.print(Text("≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈", style="cliff.accent"))
    console.print(Text("algorithmic riffs · in your terminal", style="dim"))
    console.print(Text("Ctrl+C = retroceder · Ctrl+G = salir", style="dim"))
    console.print()


def _show_header_compact(console: Console) -> None:
    """Encabezado reducido que persiste arriba en cada pantalla de sección."""
    console.print(Text("CLIff", style="cliff.brand"))
    console.print(Text("algorithmic riffs · in your terminal", style="dim"))
    console.print(Text("Ctrl+C = retroceder · Ctrl+G = salir", style="dim"))
    console.print()


def _clear_screen(console: Console) -> None:
    """Limpia la terminal (solo si es TTY) para empezar una pantalla desde arriba."""
    if console.is_terminal:
        console.clear()


def _section(console: Console, title: str, index: int, total: int) -> None:
    heading = f"{title} [{index}/{total}]"
    console.print(Text(heading, style="cliff.brand"))
    console.print(Text("─" * len(heading), style="dim"))
    console.print()


def _header_gate(console: Console) -> None:
    """Header: Enter = continuar; Ctrl+C / Ctrl+G = salir."""
    question = questionary.press_any_key_to_continue(
        "Enter = continuar · Ctrl+C / Ctrl+G = salir", style=QUESTIONARY_STYLE)
    try:
        _bind_quit(question).unsafe_ask()
    except KeyboardInterrupt:
        raise _Quit from None


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
    console.print("[cliff.brand]Previsualización de polimetría[/cliff.brand]")
    console.print(f"[cliff.value]{total_beats} beats por estructura "
                  f"({total_bars} compases × {BEATS_PER_BAR})[/cliff.value]")
    console.print(bar)
    console.print(f"[dim]{legend}[/dim]")
    console.print()


def _collect_config(console: Console):
    """Recoge la configuración pregunta a pregunta, con navegación atrás (Ctrl+C)."""
    a: dict = {}
    duration_choices = [
        questionary.Choice(f"{name} [{value}]", value=value)
        for name, value in DURATION_OPTIONS
    ]

    def s_bpm():
        a["bpm"] = int(_ask(_q_text("BPM (40-240)", default="120",
                                            validate=_int_range(40, 240),
                                            key_bindings=_step_key_bindings(40, 240, 1, True))))
        console.print(f"[dim]Compás: {BEATS_PER_BAR}/4 (fijo en el MVP)[/dim]")

    def s_total_bars():
        a["total_bars"] = int(_ask(_q_text("Duración en compases (4-64)", default="4",
                                                   validate=_int_range(4, 64),
                                                   key_bindings=_step_key_bindings(4, 64, 1, True))))
        console.print(f"[dim]{a['total_bars']} compases × {BEATS_PER_BAR} "
                      f"= {a['total_bars'] * BEATS_PER_BAR} beats por estructura[/dim]")

    def s_pattern_beats():
        a["pattern_beats"] = float(_ask(_q_text(
            "Duración del patrón en beats (ej. 3, 5, 7, 9.5)",
            default="7.0", validate=_validate_pattern_beats,
            key_bindings=_step_key_bindings(0.25, 32.0, 0.25, False),
        )))

    def s_tail_vary():
        a["tail_vary"] = _ask(_q_confirm(
            "¿Variar la melodía del tail? (mismos tiempos, otros pitches)", default=True,
        ))
        _show_polymetry_preview(console, a["total_bars"], a["pattern_beats"])

    def s_repetitions():
        a["repetitions"] = int(_ask(_q_text(
            "Número de loops (1-8)", default="2", validate=_int_range(1, 8),
            key_bindings=_step_key_bindings(1, 8, 1, True),
        )))

    def s_intro():
        a["intro"] = _ask(_q_confirm(
            "¿Intro de 4 golpes de hi-hat?", default=False,
        ))

    def s_pad_breath():
        a["pad_breath_bars"] = int(_ask(_q_text(
            "Respiración del Pad en compases (0 = Drone Infinito, 1-8)",
            default="0", validate=_int_range(0, 8),
            key_bindings=_step_key_bindings(0, 8, 1, True),
        )))

    def s_pad_mode():
        a["pad_mode"] = PadMode(_ask(_q_select(
            "Modo del Pad", choices=[m.value for m in PadMode],
        )))

    def s_pad_register():
        a["pad_register"] = PadRegister(_ask(_q_select(
            "Registro del Pad", choices=[r.value for r in PadRegister],
        )))

    def s_tonic():
        a["tonic"] = _parse_tonic(_ask(_q_text(
            "Nota central (tónica) (↑↓ cambia el pitch)",
            default=TonicEnum.C.value,
            validate=_validate_tonic,
            key_bindings=_tonic_key_bindings(),
        )))

    def s_scale():
        a["scale"] = ScaleEnum(_ask(_q_select(
            "Escala", choices=[s.value for s in ScaleEnum],
        )))

    def s_durations():
        while True:
            selected = _ask(_q_checkbox(
                "Duraciones permitidas", choices=duration_choices,
            ))
            if not selected:
                console.print("[cliff.warn]Selecciona al menos una duración.[/cliff.warn]")
                continue
            if not engine_math.pattern_is_combinable(a["pattern_beats"], selected):
                console.print(
                    "[cliff.warn]Esa combinación no puede rellenar exactamente el patrón de "
                    f"{a['pattern_beats']} beats. Añade corchea con puntillo (0.75) o "
                    "semicorchea (0.25), o pulsa Ctrl+C para cambiar la duración del patrón.[/cliff.warn]"
                )
                continue
            a["allowed_durations"] = selected
            return

    def s_max_jump():
        a["max_jump"] = int(_ask(_q_text("Salto melódico máximo (1-7)", default="3",
                                                 validate=_int_range(1, 7),
                                                 key_bindings=_step_key_bindings(1, 7, 1, True))))

    def s_density():
        a["density"] = DensityEnum(_ask(_q_select(
            "Densidad de notas", choices=[d.value for d in DensityEnum],
        )))

    def s_tonic_recurrence():
        a["tonic_recurrence"] = TonicRecurrence(_ask(_q_select(
            "Recurrencia de tónica", choices=[r.value for r in TonicRecurrence],
            default=TonicRecurrence.MEDIUM.value,
        )))

    def s_double_time():
        # Double time solo tiene sentido en 4/4 (caja en 2 y 4). Guardado para
        # cuando el compás sea configurable.
        double_time = False
        if BEATS_PER_BAR == 4:
            double_time = _ask(_q_confirm(
                "¿Double time? (platos a corcheas y caja en 2 y 4)", default=False,
            ))
        a["double_time"] = double_time

    def s_cymbal():
        a["cymbal"] = CymbalEnum(_ask(_q_select(
            "Plato", choices=[c.value for c in CymbalEnum],
        )))

    def s_cymbal_vary():
        vary = False
        if a["repetitions"] > 1:
            vary = _ask(_q_confirm(
                "¿Variar el plato en cada loop? (aleatorio)", default=True,
            ))
        a["cymbal_vary"] = vary

    def s_fill():
        fill = False
        if a["repetitions"] > 1:
            fill = _ask(_q_confirm(
                "¿Fill entre loops? (roll de caja + plato_alt)", default=False,
            ))
        a["fill"] = fill

    mixer_keys = (("Pad", "pad_config"), ("Bajo", "bass_config"),
                  ("Guitarra", "guitar_config"), ("Arpegiador", "arp_config"),
                  ("Percusión", "drums_config"))

    def s_mixer():
        if not _ask(_q_confirm("¿Personalizar volumen y velocity de las pistas?", default=False)):
            a["mixer"] = None
            return

        values: dict = {}

        def make_velocity(label, key):
            def step():
                values[f"{key}_velocity"] = int(_ask(_q_text(
                    f"{label} — velocity (0-127)", default="100",
                    validate=_int_range(0, 127),
                    key_bindings=_step_key_bindings(0, 127, 1, True),
                )))
            return step

        def make_volume(label, key):
            def step():
                values[f"{key}_volume"] = int(_ask(_q_text(
                    f"{label} — volumen (0-100)", default="100",
                    validate=_int_range(0, 100),
                    key_bindings=_step_key_bindings(0, 100, 1, True),
                )))
            return step

        mixer_steps = []
        for label, key in mixer_keys:
            mixer_steps.append(make_velocity(label, key))
            mixer_steps.append(make_volume(label, key))

        if _run_steps(mixer_steps):
            raise _Back

        a["mixer"] = {key: TrackConfig(velocity=values[f"{key}_velocity"],
                                       volume=values[f"{key}_volume"])
                      for _, key in mixer_keys}

    def s_variations():
        a["variations"] = int(_ask(_q_text("Variaciones a generar (1-5)", default="1",
                                                   validate=_int_range(1, 5),
                                                   key_bindings=_step_key_bindings(1, 5, 1, True))))

    sections = [
        ("Configuración Global", [s_bpm, s_total_bars]),
        ("Estructura", [s_pattern_beats, s_tail_vary, s_repetitions, s_intro,
                        s_pad_breath, s_pad_mode, s_pad_register]),
        ("Reglas Algorítmicas", [s_tonic, s_scale, s_durations, s_max_jump, s_density,
                                 s_tonic_recurrence, s_double_time, s_cymbal, s_cymbal_vary, s_fill]),
        ("Mezclador", [s_mixer]),
        ("Lote", [s_variations]),
    ]

    if _run_sections(console, sections):
        return None

    if a.get("mixer"):
        bass_config = a["mixer"]["bass_config"]
        pad_config = a["mixer"]["pad_config"]
        guitar_config = a["mixer"]["guitar_config"]
        arp_config = a["mixer"]["arp_config"]
        drums_config = a["mixer"]["drums_config"]
    else:
        bass_config = pad_config = guitar_config = arp_config = drums_config = TrackConfig()

    config = SongConfig(
        bpm=a["bpm"],
        total_bars=a["total_bars"],
        repetitions=a["repetitions"],
        pattern_beats=a["pattern_beats"],
        pad_breath_bars=a["pad_breath_bars"],
        tonic=a["tonic"],
        scale=a["scale"],
        allowed_durations=a["allowed_durations"],
        max_jump=a["max_jump"],
        density=a["density"],
        tonic_recurrence=a["tonic_recurrence"],
        pad_mode=a["pad_mode"],
        pad_register=a["pad_register"],
        bass_config=bass_config,
        pad_config=pad_config,
        arp_config=arp_config,
        guitar_config=guitar_config,
        drums_config=drums_config,
        double_time=a["double_time"],
        cymbal=a["cymbal"],
        cymbal_vary=a["cymbal_vary"],
        tail_vary=a["tail_vary"],
        fill=a["fill"],
        intro=a["intro"],
    )
    return config, a["variations"]


def _show_summary(console: Console, config: SongConfig, seq) -> None:
    console.print()
    structure_beats = int(seq.total_beats // seq.repetitions)
    durations = ", ".join(name for name, beats in DURATION_OPTIONS
                          if beats in config.allowed_durations)

    main = Table(box=box.SIMPLE, title="CLIff — Resumen", title_justify="left",
                 caption="Polimetría y parámetros de la pieza", caption_justify="left")
    main.add_column("Métrica", style="cliff.brand")
    main.add_column("Valor", style="cliff.value")
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
    main.add_row("Densidad de notas", f"{config.density.value}")
    main.add_row("Recurrencia de tónica", f"{config.tonic_recurrence.value}")
    main.add_row("Salto melódico máximo", f"{config.max_jump}")
    main.add_row("Duraciones permitidas", durations)
    cymbal_label = (
        f"{config.cymbal.value} (varía por loop)" if config.cymbal_vary else config.cymbal.value
    )
    main.add_row("Plato", cymbal_label)
    main.add_row("Double time", "Sí" if config.double_time else "No")
    main.add_row("Tail", "Variación melódica" if config.tail_vary else "Truncado")
    main.add_row("Fill entre loops", "Sí" if config.fill else "No")
    main.add_row("Intro", "4 golpes hi-hat" if config.intro else "No")

    mixer = Table(box=box.SIMPLE, title="Mezclador", title_justify="left", border_style="dim")
    mixer.add_column("Pista", style="bold")
    mixer.add_column("Instrumento", style="dim")
    mixer.add_column("Velocity", justify="right", style="cliff.value")
    mixer.add_column("Volumen", justify="right", style="cliff.value")
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
    out_dir = _q_text("Carpeta de exportación", default=str(DEFAULT_OUTPUT)).ask()
    os.makedirs(out_dir, exist_ok=True)
    prefix = _build_prefix(config)
    n = _next_number(out_dir, prefix)
    paths = []
    with _progress(console) as progress:
        task = progress.add_task("[cliff.info]Exportando...", total=len(midis))
        for i, midi in enumerate(midis):
            midi_path = os.path.join(out_dir, f"{prefix}_{n + i}.mid")
            midi.save(midi_path)
            paths.append(midi_path)
            progress.advance(task)
    for midi_path in paths:
        console.print(f"[cliff.ok]Exportado:[/cliff.ok] {midi_path}")


def _result_screen(console: Console, config: SongConfig, seq, midis) -> str:
    """Muestra el resumen y las acciones. Devuelve 'back' o 'quit'."""
    _clear_screen(console)
    _show_summary(console, config, seq)
    if len(midis) > 1:
        console.print(f"[dim]Se generaron {len(midis)} variaciones.[/dim]")
    while True:
        action = _q_select(
            "Acción",
            choices=["Exportar", "Volver", "Salir"],
        ).ask()
        if action == "Exportar":
            _export(console, config, midis)
        elif action == "Volver":
            return "back"
        else:  # Salir
            return "quit"


def run() -> None:
    """Punto de entrada de la TUI."""
    console = Console(theme=THEME)
    try:
        _show_header(console)
        _header_gate(console)
        while True:
            collected = _collect_config(console)
            if collected is None:
                console.print("[cliff.info]¡Hasta pronto![/cliff.info]")
                break
            config, variations = collected
            with _progress(console) as progress:
                task = progress.add_task("[cliff.info]Generando variaciones...", total=variations)
                sequences = []
                midis = []
                for _ in range(variations):
                    seq = engine_math.generate_sequence(config)
                    sequences.append(seq)
                    midis.append(engine_midi.build_midi(config, seq))
                    progress.advance(task)
            result = _result_screen(console, config, sequences[0], midis)
            if result == "quit":
                console.print("[cliff.info]¡Hasta pronto![/cliff.info]")
                break
            # else "back": volver a configurar
            console.print()
    except _Quit:
        console.print("[cliff.info]¡Hasta pronto![/cliff.info]")
