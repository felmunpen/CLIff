# TO DO

---
### Arpegiador

> Rama: `feature/arpeggiator` (desde `develop`).
> Estado: borrador inicial. Ir completando poco a poco conforme se resuelven las dudas.

#### Mapa propuesto

1. **Rama y base de trabajo** — Crear `feature/arpeggiator` desde `develop`, que ya integra la TUI de `feature/tui-flow`.
2. **Material armónico** — Definir el acorde a arpegiar empezando por la triada de tónica (grados I–III–V).
3. **Orden del arpegio** — Empezar con ascendente (I→III→V) y descendente (V→III→I).
4. **Pulsación / ritmo del arpegio** — Generar con negras, blancas y blancas con puntillo hasta completar el loop.
5. **Timbre / canal** — Elegir un programa GM suave y sostenido (celesta, órgano u otro).
6. **Feature futura** — Anotar el double time del arpegio para valorarlo más adelante.

#### Dudas / cuestiones abiertas

- Cómo evoluciona el acorde a lo largo de los loops (¿siempre la triada de tónica o varía?).
- Registro de octavas del arpegio (rango de notas).
- Cómo encaja el arpegio con el tail (¿arpegios en el tail o solo en ciclos completos?).
- Relación con la pulsación del riff/patrón principal (contraste: ritmo más relajado).
- Interacción con `double_time` global y con el `intro`.
- ---