# AI Developer Context & Spec Sheet — CLIff

## 1. Contexto del Proyecto
**CLIff** (*Command Line Interface + Riff*) es un generador algorítmico de música MIDI por consola (CLI/TUI). Se basa en la creación de **polimetrías** (patrones de longitud asimétrica repitiéndose sobre una base estándar de 4/4) utilizando reglas matemáticas y el cálculo de residuos (*tails*).

**Descripción corta:** *A CLI-based algorithmic MIDI generator for polymetric riffs and mathematical pattern composition.*

El objetivo de CLIff es ofrecer una herramienta ligera, enfocada y estilo "hacker/productor" donde el usuario introduzca parámetros numéricos en la terminal y obtenga archivos `.mid` multipista y `.wav` (vía SoundFont integrada) listos para arrastrar a un DAW.

## 2. Stack Tecnológico Estricto
- **Lenguaje:** Python 3.10+
- **Interfaz de Usuario (TUI):** `rich` (para salidas visuales, paneles, tablas y colores) y `questionary` (para menús e inputs interactivos).
- **Generación MIDI:** `mido` (y sus constructores `MetaMessage`, `Message`, `MidiFile`, `MidiTrack`).
- **Preescucha y Render de Audio:** `pyfluidsynth` o integración vía `subprocess` con el ejecutable CLI de FluidSynth.
- **Empaquetado (Final):** `PyInstaller` (configurado para incluir archivos `.sf2` de menos de 10MB en el ejecutable final).
- **PROHIBIDO:** Tecnologías web (JS, HTML, WebAudio), frameworks GUI de escritorio (Tkinter, PyQt, Electron). Todo el software debe ejecutarse estrictamente en la terminal.

## 3. Arquitectura Musical del MVP

### 3.1 Pistas y Asignaciones (Estándar General MIDI)
CLIff generará siempre 4 pistas independientes:
1. **Pad (Canal 1):** Instrumento GM 89 (Pad 2 - Warm) o 91 (Pad 4 - Choir). Mantiene el sostén armónico.
2. **Bajo/Guitarra (Canal 2):** Instrumento GM 33 (Finger Bass) o 25 (Acoustic Steel Guitar). Ejecuta la línea melódica algorítmica principal.
3. **Arpegiador (Canal 3):** Instrumento GM 80 (Square Lead) u 81 (Saw Lead). Rellena los espacios recorriendo los grados de la escala.
4. **Percusión (Canal 10):** Set estándar GM de percusión.

### 3.2 El Motor de Polimetría (Lógica del Residuo)
- **Métrica base:** 4/4 (Fijo en MVP).
- **Duración Total:** $X$ compases definidos por el usuario (ej. 8 compases = 32 beats).
- **Patrón Principal:** $Y$ beats definidos por el usuario (ej. 7 beats).
- **Comportamiento:** El patrón de $Y$ beats se repite consecutivamente hasta donde quepa completo dentro de los $X$ compases.
- **Tail / Residuo:** Los beats sobrantes (`total_beats % pattern_beats`) se rellenan automáticamente con una versión truncada del propio Patrón Principal (ej. los primeros 4 beats del patrón de 7).

### 3.3 El Motor Rítmico (Duraciones)
- El usuario selecciona qué duraciones están permitidas mediante checkboxes: Negra (1.0), Corchea con puntillo (0.75), Corchea (0.5), Semicorchea (0.25).
- El motor seleccionará duraciones del pool de opciones permitidas hasta que **la suma total sea exactamente igual a la Longitud del Patrón** ($Y$ beats). 
- *Regla:* Si al sumar queda un residuo menor que no encaja con ninguna duración permitida, el algoritmo ajustará dinámicamente el último valor para cuadrar matemáticamente la suma.

### 3.4 El Motor Melódico
- **Tónica fija (MVP):** C (Do).
- **Escalas Permitidas (2 octavas):** Mayor, Menor (Eólica), Menor Armónica, Frigio, Frigio Dominante.
- El algoritmo tratará la escala como un array de índices (donde el índice 0 es la nota C grave).
- **Salto Melódico Máximo:** Parámetro del usuario (rango 1 a 5). Determina la distancia máxima de intervalos entre notas consecutivas.
- **Límites (Bounce):** Si el índice calculado es menor que 0 o supera el límite superior del array, la dirección del movimiento se invierte automáticamente.
- **Regla Estricta:** La primera nota del patrón principal y del *tail* debe ser SIEMPRE el índice 0 (la tónica C).

### 3.5 Reglas Específicas de las Pistas
- **Pad (Respiración):** El usuario define cada cuántos compases se vuelve a disparar el acorde/nota. **Regla de Drone Infinito:** Si el parámetro de respiración se establece en `0`, se envía un único `Note On` en el beat 0 y un `Note Off` al final del último compás de la pieza.
- **Percusión:**
  - Caja (Snare): Golpe estático en los tiempos 2 y 4 de cada compás.
  - Hi-Hat: Pulsos constantes en corcheas o negras.
  - Bombo (Kick): Clona exactamente los instantes de ataque (`Note On`) generados por la pista del Bajo/Guitarra para acentuar el polirritmo.
- **Dinámica (Velocity):** En el MVP se utiliza un *velocity* plano y constante definido por el usuario (0-127) para cada pista, así como un nivel de volumen global por canal.
- **Claqueta (Count-in):** Generar un compás previo de metrónomo/hi-hat (4 golpes) antes del inicio de la estructura musical.

## 4. Flujo de la Interfaz TUI (Prompt Flow)
1. **Configuración Global:** BPM, Duración en Compases.
2. **Estructura:** Duración del Patrón (beats), Respiración del Pad (0 = Drone).
3. **Reglas Algorítmicas:** Checkboxes de duraciones permitidas, Salto melódico máximo (1-5), Densidad.
4. **Mezclador:** Velocity base (0-127) y Volumen (0-100) por pista.
5. **Acciones:** Generar. Al terminar, guardar los archivos (`.mid` y `.wav`) en `/output` y reproducir automáticamente la preescucha.

## 5. Directivas Estrictas para la IA (Guardrails)
- **Mantener la simplicidad del MVP:** No introducir progresiones de acordes, cambios de compás ni algoritmos de variación de velocity salvo petición explícita para versiones futuras.
- **Arquitectura Modular:** Separar el código en módulos limpios: `tui.py` (interfaz interactiva), `engine_math.py` (cálculo de secuencias y matrices) y `engine_midi.py` (construcción y exportación MIDI con `mido`).
- **Estética Terminal:** Utilizar `rich` para formatear paneles de estado, barras de progreso y tablas con la estructura polirrítmica calculada.
- **Precisión Matemática:** Garantizar que los tiempos acumulados de los eventos MIDI no sufran desviaciones por redondeo en operaciones de punto flotante.

---

## Control de versiones

Propón commits cuando:

- Haya cambios sustanciales en el código
- Se completen tareas/objetivos

Se usará inglés para el nombre y los mensajes los commits, con un lenguaje sencillo, breve y conciso. Si en algún momento, por los cambios llevados a cabo, es necesario explayarse, no hay problema, pero debe ser en la menor parte de los casos.

Siempre plantéalos y espera confirmación antes de llevarlos a cabo.