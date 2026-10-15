# AI Developer Context & Spec Sheet — CLIff

## 1. Contexto del Proyecto
**CLIff** (*Command Line Interface + Riff*) es un generador algorítmico de música MIDI por consola (CLI/TUI). Se basa en la creación de **polimetrías** (patrones de longitud asimétrica repitiéndose sobre una base estándar de 4/4) utilizando reglas matemáticas y el cálculo de residuos (*tails*).

**Descripción corta:** *A CLI-based algorithmic MIDI generator for polymetric riffs and mathematical pattern composition.*

El objetivo de CLIff es ofrecer una herramienta ligera, enfocada y estilo "hacker/productor" donde el usuario introduzca parámetros numéricos en la terminal y obtenga archivos `.mid` multipista listos para arrastrar a un DAW.

## 2. Stack Tecnológico Estricto
- **Lenguaje:** Python 3.10+
- **Interfaz de Usuario (TUI):** `rich` (para salidas visuales, paneles, tablas y colores) y `questionary` (para menús e inputs interactivos).
- **Generación MIDI:** `mido` (y sus constructores `MetaMessage`, `Message`, `MidiFile`, `MidiTrack`).
- **Empaquetado (Final):** `PyInstaller` (configurado para generar un ejecutable independiente).
- **PROHIBIDO:** Tecnologías web (JS, HTML, WebAudio), frameworks GUI de escritorio (Tkinter, PyQt, Electron). Todo el software debe ejecutarse estrictamente en la terminal.

## 3. Arquitectura Musical del MVP

### 3.1 Pistas y Asignaciones (Estándar General MIDI)
CLIff genera siempre 5 pistas (canales en notación GM 1-indexada; en `mido` se resta 1):
1. **Pad (Canal 1):** Instrumento GM 89 (Pad 2 - Warm). Mantiene el sostén armónico.
2. **Bajo (Canal 2):** Instrumento GM 33 (Finger Bass). Ejecuta la línea melódica algorítmica principal, **dos octavas por debajo** de la escala base (tónica en octava grave, p. ej. C1).
3. **Arpegiador (Canal 3):** Instrumento GM 80 (Square Lead). **Pista fantasma en el MVP** (presente pero sin notas, reservada para una feature futura).
4. **Guitarra (Canal 4):** Instrumento GM 29 (Overdriven Guitar). Duplica la línea del bajo **una octava por encima** (octava grave, p. ej. C2).
5. **Percusión (Canal 10):** Set estándar GM de percusión.

### 3.2 El Motor de Polimetría (Lógica del Residuo)
- **Métrica base:** 4/4 (Fijo en MVP).
- **Duración Total:** $X$ compases definidos por el usuario (ej. 8 compases = 32 beats).
- **Patrón Principal:** $Y$ beats definidos por el usuario (ej. 7 beats).
- **Comportamiento:** El patrón de $Y$ beats se repite consecutivamente hasta donde quepa completo dentro de los $X$ compases.
- **Tail / Residuo:** Los beats sobrantes (`total_beats % pattern_beats`) se rellenan con una versión **truncada del propio Patrón Principal** (ej. los primeros 4 beats del patrón de 7).

### 3.3 El Motor Rítmico (Duraciones y Densidad)
- El usuario selecciona qué duraciones están permitidas mediante checkboxes: Negra (1.0), Corchea con puntillo (0.75), Corchea (0.5), Semicorchea (0.25).
- **Densidad:** número de notas objetivo del patrón principal, elegida por nivel (Baja 3-4, Media 5-6, Alta 7-9), con *clamp* automático de factibilidad según la longitud del patrón y las duraciones permitidas.
- El motor genera **exactamente** el número de notas objetivo, cuya suma total es igual a la Longitud del Patrón (la última se ajusta para cuadrar exacto).
- **Precisión:** toda la aritmética de tiempos se hace en **ticks enteros** (`480` ppq), sin coma flotante en las posiciones de los eventos.

### 3.4 El Motor Melódico
- **Tónica configurable:** El usuario elige la nota central (12 notas, solo sostenidos).
- **Escalas Permitidas (2 octavas):** Mayor, Menor (Eólica), Menor Armónica, Frigio, Frigio Dominante.
- El algoritmo trata la escala como un array de índices (donde el índice 0 es la nota C grave).
- **Salto Melódico Máximo:** Parámetro del usuario (rango 1 a 5). Distancia máxima de intervalos entre notas consecutivas.
- **Límites (Bounce):** Si el índice calculado sale del rango, la dirección del movimiento se invierte automáticamente.
- **Riff:** la melodía se genera **una sola vez** y se repite en cada ciclo (el tail es su truncado).
- **Regla Estricta:** La primera nota del patrón principal (y por tanto del tail) es SIEMPRE el índice 0 (la tónica elegida).

### 3.5 Reglas Específicas de las Pistas
- **Pad (Respiración):** El usuario define cada cuántos compases se vuelve a disparar el acorde/nota. **Regla de Drone Infinito:** Si la respiración es `0`, se envía un único `Note On` en el beat 0 y un `Note Off` al final del último compás.
  - **Modo:** `Mono` (tónica) o `Acorde` (grados 1-3-5 de la escala).
  - **Registro:** `Grave` (C3) o `Agudo` (C4).
- **Percusión:**
  - Caja (Snare): Golpe estático en el **beat 3** de cada compás (por defecto). En modo *double time* (solo 4/4), golpea en los tiempos **2 y 4**.
  - Plato: Pulsos constantes en **negras** (por defecto). En *double time*, en **corcheas**. Configurable: hi-hat abierto (por defecto), hi-hat cerrado, ride, crash o china (notas GM 46/42/51/49/52).
  - Bombo (Kick): Clona exactamente los instantes de ataque (`Note On`) generados por la pista del Bajo para acentuar el polirritmo.
  - **Double time:** opción y/n que solo se ofrece en 4/4. Convierte la caja a 2 y 4 y el plato a corcheas (sensación el doble de rápida).
- **Dinámica:** *Velocity* plano (0-127) por pista y *volumen* de canal (0-100, emitido como CC7) por pista.
- **Sin claqueta (count-in) en el MVP.**

## 4. Flujo de la Interfaz TUI (Prompt Flow)
1. **Configuración Global:** BPM y Duración en Compases (mostrando el compás 4/4, fijo en el MVP, y el total de beats resultante).
2. **Estructura:** Duración del Patrón (beats), Respiración del Pad (0 = Drone), Modo del Pad (Mono/Acorde), Registro del Pad (Grave/Agudo).
3. **Reglas Algorítmicas:** Nota central (tónica), Escala, Checkboxes de duraciones permitidas, Salto melódico máximo (1-7), Densidad (Baja/Media/Alta), Plato (hi-hat abierto/cerrado, ride, crash, china), Double time (y/n, solo 4/4).
4. **Mezclador (opcional):** Velocity (0-127) y Volumen (0-100) por pista, previa confirmación y/n.
5. **Lote:** Nº de variaciones a generar (1-5).
6. **Acciones:** Generar. Tras generar, el usuario dispone de **💾 Exportar** (guardar el/los `.mid` en `/output` o carpeta elegida).

## 5. Directivas Estrictas para la IA (Guardrails)
- **Mantener la simplicidad del MVP:** No introducir progresiones de acordes, cambios de compás ni algoritmos de variación de velocity salvo petición explícita para versiones futuras.
- **Arquitectura Modular:** Separar el código en módulos limpios: `models.py` (dataclasses/enums/constantes), `engine_math.py` (cálculo de secuencias y matrices, puro), `engine_midi.py` (construcción MIDI en memoria) y `tui.py` (interfaz interactiva).
- **Estética Terminal:** Utilizar `rich` para formatear paneles de estado, barras de progreso y tablas con la estructura polirrítmica calculada.
- **Precisión Matemática:** Garantizar que los tiempos acumulados de los eventos MIDI no sufran desviaciones por redondeo (se trabaja en ticks enteros).

## 6. Próximo Trabajo (Siguiente Sesión)

- ~~Hacer que la pieza dure N veces (2 por defecto)~~ — **completado**.
- ~~Sesgo de la nota final del patrón (`generate_rhythm_pattern`)~~ — **completado**: relleno por *backtracking* aleatorizado que mantiene todas las notas (incluida la última) dentro del pool, con fallback a "última nota = resto" solo cuando el patrón no es combinable.
- ~~Duración por defecto a 4 compases~~ — **completado**.
- ~~Leyenda de acciones del resultado~~ — **completado**: eliminada, queda el `select` de acciones (💾 Exportar / ↩ Volver / ✕ Salir).
- ~~Incrementar/decrementar campos numéricos con flechas~~ — **completado**: enteros ±1; `pattern_beats` ±0.25.
- ~~Navegación atrás entre preguntas~~ — **completado**: Ctrl+C retrocede una pregunta; en el primer prompt sale del programa.
- ~~Variación del plato por loop~~ — **completado**: confirm "¿Variar el plato en cada loop? (aleatorio)" (solo si loops > 1); el primer loop usa el plato elegido y los siguientes eligen otro distinto al azar.
- ~~Densidad relativa al rango factible (`resolve_density` / `DENSITY_FRACTIONS`)~~ — **completado**: la densidad se interpreta como fracción del rango `[min_notes, max_notes]` (Baja 0.25, Media 0.5, Alta 0.8), eliminando el colapso a "todo negras" cuando la negra está en el pool.
- ~~Guarda de combinabilidad~~ — **completado**: `pattern_is_combinable` (gcd) avisa/bloquea en la TUI cuando `pattern_beats × 4` es impar (XX.25/XX.75) sin corchea con puntillo ni semicorchea en el pool.
- Guardado y carga de semillas numéricas (*Seeds*) para reproducir o compartir patrones exactos (primera entrada del roadmap en `README.md`).
- Revisar el motor de decisión de notas/steps del riff (`generate_melody_indices`): distribución uniforme del paso, dirección 50/50 y plegado espejo en bordes — evaluar sesgo hacia grados conjuntos y conciencia de la tónica.
- Aplazado: opción para **evitar tónicas consecutivas** en la recurrencia de tónica (flag booleano + guard; decidir semántica estricta vs. suave bajo el post-procesado).
- Posible feature futura: **secuenciador de ritmo** en la TUI (grid de *onsets* del riff sobre el resumen, estilo *step sequencer*). Aplazado por salirse del alcance actual de la aplicación.
- ~~Tail con notas diferentes~~ — **completado**: flag `tail_vary` (y/n tras el diagrama de bloques); el tail mantiene el ritmo truncado y la tónica inicial, pero con melodía (pitches) propia.
- ~~Fill al final del loop~~ — **completado**: flag `fill` (y/n, solo si loops > 1); roll de caja (4 semicorcheas) en el último beat de cada loop + `plato_alt` en el downbeat del siguiente (con `cymbal_vary`, eco del plato saliente; si no, plato aleatorio distinto del principal).
- ~~Intros~~ — **completado**: flag `intro` (y/n); count-in de 4 golpes de hi-hat en negras (1 compás) que desplaza la pieza. Aplazados para el futuro: drone suave y tail como intro.
---

## Control de versiones

Propón commits cuando:

- Haya cambios sustanciales en el código
- Se completen tareas/objetivos

Se usará inglés para el nombre y los mensajes los commits, con un lenguaje sencillo, breve y conciso. Si en algún momento, por los cambios llevados a cabo, es necesario explayarse, no hay problema, pero debe ser en la menor parte de los casos.

Siempre plantéalos y espera confirmación antes de llevarlos a cabo.
