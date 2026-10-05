# Spec 04: Interfaz TUI y Flujo de Usuario

## 1. Módulo `cliff/tui.py`

### 1.1 Pantallas y Pasos Interactivos (`questionary`)

1. **Header:** Banner ASCII de **CLIff** generado con `rich.panel`.
2. **Paso 1: Configuración Global**
   - `bpm`: Entero (40–240, default 120).
   - `total_bars`: Entero (4–64, default 8).
3. **Paso 2: Polimetría y Pad**
   - `pattern_beats`: Flotante/Entero (ej. 3, 5, 7, 9.5). **Validado** como múltiplo de la menor duración permitida (0.25).
   - `pad_breath_bars`: Entero (`0` = Drone Infinito, `1-8` = re-disparo).
   - `pad_mode`: Select (`Mono`, `Acorde`).
   - `pad_register`: Select (`Grave`, `Medio`, `Agudo`).
4. **Paso 3: Reglas Algorítmicas**
   - `scale`: Select (`Mayor`, `Menor (Eólica)`, `Menor Armónica`, `Frigio`, `Frigio Dominante`).
   - `allowed_durations`: Checkbox (`Negra [1.0]`, `Corchea con puntillo [0.75]`, `Corchea [0.5]`, `Semicorchea [0.25]`).
   - `max_jump`: Slider/Int (1–5).
   - `density`: Select (`Baja`, `Media`, `Alta`).
5. **Paso 4: Mezclador**
   - Por cada pista (Pad, Bass, Arpeggiator, Percusión):
     - `velocity`: Int (0–127).
     - `volume`: Int (0–100).
6. **Paso 5: Generar**
   - Al confirmar, se ejecuta `engine_math` + `engine_midi` (MIDI en memoria).

### 1.2 Vista de Resultados (`rich.table`)

Tras generar, se muestra el desglose matemático y las acciones disponibles:

```text
┌──────────────────────────────────────────────────────────┐
│ CLIff — Resumen de Polimetría Calculada                  │
├──────────────────────────────────────────────────────────┤
│ Beats Totales: 32.0 (8 compases en 4/4)                  │
│ Duración del Patrón: 7.0 beats                           │
│ Repeticiones Completas: 4 ciclos (28.0 beats)            │
│ Residuo (Tail): 4.0 beats                                │
└──────────────────────────────────────────────────────────┘

Acciones:
  💾 Exportar  (guarda el .mid en /output o carpeta elegida)
  ↩ Volver     (modificar parámetros)
```

- **💾 Exportar**: guarda el `.mid` con el nombre `cliff_<bpm>bpm_p<patrón>.mid`; carpeta por defecto `/output`, con opción de elegir otra.
- Los tiempos y duraciones se muestran al usuario con **nombres de nota** (negra, corchea…), nunca en ticks enteros.
