# Spec 01: Arquitectura General y Estructura del Proyecto

## 1. Estructura de Directorios

```text
CLIff/                      # repositorio / marca
├── AGENTS.md
├── README.md
├── requirements.txt
├── main.py
├── specs/
│   ├── 01_architecture.md
│   ├── 02_engine_math.md
│   ├── 03_engine_midi.md
│   ├── 04_tui.md
│   └── 05_data_models.md
├── cliff/                  # paquete Python (imports: from cliff import ...)
│   ├── __init__.py
│   ├── models.py           # Dataclasses, Enums y constantes
│   ├── engine_math.py      # Lógica matemática, polimetría y melodía (puro)
│   ├── engine_midi.py      # Construcción de pistas MIDI en memoria
│   ├── engine_audio.py     # Render WAV (FluidSynth) y reproducción
│   └── tui.py              # Formularios Questionary y vistas Rich
├── assets/
│   └── default.sf2         # SoundFont ligera por defecto (<10MB)
└── output/                 # Carpeta de exportación por defecto (.mid y .wav)
```

> La marca es **CLIff**; el paquete Python se importa como **cliff** (minúsculas).

## 2. Flujo de Datos

```text
[ Usuario ] ──(inputs)──> [ tui.py ]
                              │
                       (SongConfig)
                              ▼
                     [ engine_math.py ] ──(SequenceData)──┐
                                                          │
                                                          ▼
                     [ engine_midi.py ] ──(MidiFile en memoria)
                                                          │
                                                          ├─ Exportar ──> output/*.mid
                                                          ▼
                     [ engine_audio.py ] ──(FluidSynth)
                                                          │
                                                          ├─ ▶ Play ──> reproducción
                                                          └─ Exportar ──> output/*.wav
```

Flujo de acciones del usuario (ver `specs/04`):

1. **Generar**: `tui.py` → `engine_math.py` (cálculo) → `engine_midi.py` (MIDI en memoria).
2. **▶ Play**: `engine_audio.py` renderiza el `.wav` (perezoso) y lo reproduce.
3. **💾 Exportar**: guarda `.mid` y `.wav` en `/output` (o carpeta elegida).

## 3. Principios de Diseño
- **Inmutabilidad de Configuración:** `SongConfig` se construye en `tui.py` y se pasa como objeto de lectura a los motores.
- **Cero Efectos Secundarios en Math:** `engine_math.py` es puramente determinista, no depende de librerías MIDI ni de I/O, y trabaja con **ticks enteros** (sin aritmética en coma flotante para los tiempos).
- **Desacoplamiento de Audio:** `engine_midi.py` solo construye el `.mid` en memoria. `engine_audio.py` renderiza a `.wav` (perezoso) y reproduce. Nada se escribe a disco hasta que el usuario exporta.
