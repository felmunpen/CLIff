"""Renderizado de audio (FluidSynth vía subprocess) y reproducción."""

import subprocess
import sys


def render_midi_to_wav(midi_path: str, sf2_path: str, output_wav_path: str) -> bool:
    """Renderiza un `.mid` a `.wav` usando el binario de FluidSynth."""
    cmd = [
        "fluidsynth", "-ni", sf2_path, midi_path,
        "-F", output_wav_path, "-r", "44100",
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0


def play_audio(wav_path: str) -> None:
    """Reproduce un `.wav` con el reproductor por defecto del sistema (best-effort)."""
    if sys.platform == "darwin":                 # macOS
        cmd = ["afplay", wav_path]
    elif sys.platform.startswith("win"):         # Windows
        cmd = ["powershell", "-c",
               f'(New-Object Media.SoundPlayer "{wav_path}").PlaySync()']
    else:                                        # Linux
        cmd = ["aplay", wav_path]                # fallback: paplay

    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        # best-effort: sin reproductor de audio disponible, no se rompe nada
        pass
