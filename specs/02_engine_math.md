# Spec 02: Motor Matemático, Polimetría y Algoritmos Melódicos

## 1. Módulo `cliff/engine_math.py`

### 1.1 Generación del Patrón Rítmico (Duraciones)
**Función:** `generate_rhythm_pattern(pattern_length_beats: float, allowed_durations: list[float]) -> list[float]`

**Algoritmo:**
1. Crear una lista vacía `durations = []`.
2. Mientras `sum(durations) < pattern_length_beats`:
   - Seleccionar aleatoriamente una duración $D$ del pool `allowed_durations`.
   - Si `sum(durations) + D > pattern_length_beats`:
     - Calcular el residuo $R = \text{pattern\_length\_beats} - \text{sum}(durations)$.
     - Si $R > 0$, añadir $R$ a `durations` (ajuste dinámico para cuadrar exacto).
   - De lo contrario, añadir $D$.
3. **Salida:** Lista de duraciones cuya suma es exactamente `pattern_length_beats` (ej. `[1.0, 0.75, 0.5, 0.75]` para un patrón de 3.0 beats).

---

### 1.2 Bucle de Polimetría y Cálculo de Residuo (Tail)
**Función:** `build_polymetric_sequence(total_bars: int, pattern_rhythm: list[float]) -> list[dict]`

**Matemática:**
- $\text{total\_beats} = \text{total\_bars} \times 4.0$
- $\text{pattern\_beats} = \sum(\text{pattern\_rhythm})$
- $\text{full\_loops} = \lfloor \frac{\text{total\_beats}}{\text{pattern\_beats}} \rfloor$
- $\text{tail\_beats} = \text{total\_beats} \pmod{\text{pattern\_beats}}$

**Estructura del Resultado:**
1. Repetir `pattern_rhythm` completo $\text{full\_loops}$ veces.
2. Si $\text{tail\_beats} > 0$:
   - Recorrer `pattern_rhythm` y extraer duraciones hasta sumar exactamente $\text{tail\_beats}$.
   - Ajustar el último elemento si excede el límite del tail.

---

### 1.3 Algoritmo Melódico (Salto y Rebote)
**Función:** `generate_melody_indices(rhythm_events_count: int, max_jump: int, scale_len: int) -> list[int]`

**Reglas:**
- La nota inicial (evento 0) es **SIEMPRE el índice 0** (Tónica C).
- Cada reinicio del patrón principal o inicio del *tail* fuerza el evento a índice 0.
- Para los eventos intermedios:
  - Calcular dirección aleatoria ($\text{subir} = +1, \text{bajar} = -1$).
  - Seleccionar paso $S \in [1, \text{max\_jump}]$.
  - Nuevo índice $I_{\text{nuevo}} = I_{\text{actual}} + (\text{dirección} \times S)$.
  - **Lógica de Bounce (Límites):**
    - Si $I_{\text{nuevo}} \ge \text{scale\_len}$: $I_{\text{ajustado}} = \text{scale\_len} - 1 - (I_{\text{nuevo}} - (\text{scale\_len} - 1))$.
    - Si $I_{\text{nuevo}} < 0$: $I_{\text{ajustado}} = \vert{}I_{\text{nuevo}}\vert{}$.
- Retorna la lista de índices absolutos sobre la matriz de la escala.