# Spec 04: Interfaz TUI y Flujo de Usuario

## 1. Módulo `cliff/tui.py`

### 1.1 Pantallas y Pasos Interactivos (`questionary`)

1. **Header:** Banner ASCII de **CLIff** generado con `rich.panel`.
2. **Paso 1: Configuración Global**
   - `bpm`: Entero (40–240, default 120).
   - Se muestra el compás actual (`4/4`, fijo en el MVP) antes de pedir los compases.
   - `total_bars`: Entero (4–64, default 8).
   - Se muestra la multiplicación `total_bars × BEATS_PER_BAR = beats totales`.
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
   - Confirm `y/n`: "¿Personalizar volumen y velocity de las pistas?" (default No).
   - Si **No**: se usan los valores por defecto (`velocity=100`, `volume=100`) en las 4 pistas.
   - Si **Sí**, por cada pista (Pad, Bass, Arpeggiator, Percusión):
     - `velocity`: Int (0–127).
     - `volume`: Int (0–100).
6. **Paso 5: Lote**
   - `variations`: Entero (1–5, default 1). Nº de variaciones (MIDIs) a generar con los mismos parámetros.
7. **Generar**
   - Se ejecuta `engine_math` + `engine_midi` una vez por variación (MIDI en memoria).

### 1.2 Previsualización de Polimetría (`rich`)

Tras completar el **Paso 2** (cuando ya se conocen `total_bars` y `pattern_beats`),
la TUI muestra una previsualización calculada con `engine_math.polymetry_summary`:

1. **Total de beats:** `total_bars × BEATS_PER_BAR` (con su equivalencia en compases).
2. **Mapa gráfico:** una barra de bloques que representa la pieza completa:
   - Los **ciclos completos** del patrón se dibujan en **cian**.
   - El **tail** final se dibuja en **amarillo**.
   - **Separación:** los bloques se separan con un espacio simple (sin corchetes).
   - **Resolución:** 1 bloque = 1 beat. Cuando `pattern_beats` o el tail tienen
     fracciones de cuarto (0.25/0.5/0.75), se usa resolución de semicorchea
     (0.25 beat = 1 bloque) para que todos los segmentos tengan longitud entera.
   - **Escalado:** si la barra supera ~60 bloques, se reduce proporcionalmente
     (manteniendo las proporciones) para caber en el ancho de la terminal.
3. **Leyenda:** "N ciclos completos + tail de M beats".

Ejemplo (8 compases en 4/4, patrón de 7 beats):

```text
32 beats totales (8 compases × 4)
███████ ███████ ███████ ███████ ████
4 ciclos completos + tail de 4 beats
```

### 1.3 Vista de Resultados (`rich.table`)

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

- **💾 Exportar**: guarda los `.mid` con el nombre `{tónica}_{escala}_{compás}_{bpm}bpm_{fechaDDMMYYYY}_{nº}.mid` (p. ej. `c_eolian_44_146bpm_05102026_3.mid`). El `nº` es el siguiente libre en la carpeta de destino (evita sobreescritura); en lote se asignan números consecutivos.
- Los tiempos y duraciones se muestran al usuario con **nombres de nota** (negra, corchea…), nunca en ticks enteros.
