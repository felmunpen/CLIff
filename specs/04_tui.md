# Spec 04: Interfaz TUI y Flujo de Usuario

## 1. Módulo `cliff/tui.py`

### 1.1 Pantallas y Pasos Interactivos (`questionary`)

1. **Header:** Banner ASCII de **CLIff** generado con `rich.panel`.
2. **Paso 1: Configuración Global**
   - `bpm`: Número entero (Rango: 40 - 240, Default: 120).
   - `total_bars`: Número entero (Rango: 4 - 64, Default: 8).
3. **Paso 2: Polimetría**
   - `pattern_beats`: Flotante/Entero (Ej: 3, 5, 7, 9.5).
   - `pad_breath_bars`: Entero (`0` = Drone Infinito, `1-8` = Re-disparo).
4. **Paso 3: Reglas Algorítmicas**
   - `scale`: Select (`Mayor`, `Menor Eólica`, `Menor Armónica`, `Frigio`, `Frigio Dominante`).
   - `allowed_durations`: Checkbox (`Negra [1.0]`, `Corchea Puntillo [0.75]`, `Corchea [0.5]`, `Semicorchea [0.25]`).
   - `max_jump`: Slider/Int (1 a 5).
5. **Paso 4: Mezclador**
   - Velocities planos por pista (0 - 127).

---

### 1.2 Vista de Resultados (`rich.table`)

Al terminar el cálculo, se presenta un panel con el desglose matemático:

```text
┌──────────────────────────────────────────────────────────┐
│ CLIff — Resumen de Polimetría Calculada                  │
├──────────────────────────────────────────────────────────┤
│ Beats Totales: 32.0 (8 compases en 4/4)                  │
│ Duración del Patrón: 7.0 beats                           │
│ Repeticiones Completas: 4 ciclos (28.0 beats)            │
│ Residuo (Tail): 4.0 beats                                │
└──────────────────────────────────────────────────────────┘
```