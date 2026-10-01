# Spec 01: Arquitectura General y Estructura del Proyecto

## 1. Estructura de Directorios

```text
cliff/
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
├── cliff/
│   ├── __init__.py
│   ├── models.py          # Dataclasses, Enums y validadores
│   ├── engine_math.py     # Lógica matemática, polimetría y melodía
│   ├── engine_midi.py     # Construcción de pistas MIDI y exportación
│   ├── engine_audio.py    # Integración con FluidSynth para renderizado WAV
│   └── tui.py             # Formularios Questionary y vistas Rich
├── assets/
│   └── default.sf2        # SoundFont ligera por defecto (<10MB)
└── output/                # Archivos generados (.mid y .wav)
```

## 2. Flujo de Datos

```text
[ Usuario ] ──(Inputs)──> [ tui.py ]
                              │
                      (SongConfig Dataclass)
                              │
                              ▼
                     [ engine_math.py ] ──(SequenceData)──┐
                                                          │
                              ┌───────────────────────────┘
                              ▼
                     [ engine_midi.py ] ──(MidiFile)───> [ output/*.mid ]
                              │
                              ▼
                     [ engine_audio.py ] ──(FluidSynth)─> [ output/*.wav ]
                              │
                              ▼
                   [ Reproducción TUI ]
```

## 3. Principios de Diseño
- **Inmutabilidad de Configuración:** `SongConfig` se construye en `tui.py` y se pasa como objeto de lectura a los motores.
- **Cero Efectos Secundarios en Math:** `engine_math.py` es puramente determinista y no depende de librerías MIDI ni de entrada/salida (I/O).
- **Desacoplamiento de Audio:** `engine_midi.py` solo crea y guarda el archivo `.mid`. `engine_audio.py` toma ese `.mid` y lo convierte a `.wav`.

---