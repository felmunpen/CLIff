# CLIff
## A Polymetric MIDI Generator (CLI)

> **A CLI-based algorithmic MIDI generator for polymetric riffs and mathematical pattern composition.**

**CLIff** (*Command Line Interface + Riff*) es un generador algorítmico de música por consola diseñado para productores, compositores y entusiastas del *math rock*, metal progresivo y música electrónica experimental.

La herramienta permite crear secuencias MIDI multipista basadas en **desfases métricos (polimetrías)** —como encajar patrones de 7 *beats* sobre estructuras globales en 4/4— calculando automáticamente los remates de residuo (*tails*) y exportando archivos MIDI listos para usar en cualquier DAW.

---

## 🎵 Características Principales

*   **Motor de Polimetría y Residuo:** Define la duración del patrón principal en *beats* asimétricos. CLIff repite el patrón y calcula un remate (*tail*) truncado para completar la métrica global sin descarrilar el compás.
*   **5 Pistas Autogeneradas:**
    *   **Pad:** Sostén armónico sobre la tónica. Incluye modo *Drone Infinito* (respiración = 0), modo *Mono/Acorde* y registro *Grave/Agudo*.
    *   **Bajo:** Ejecuta la línea melódica principal (el *riff*) generada por el algoritmo.
    *   **Guitarra:** Duplica la línea del bajo una octava por encima con overdrive (GM 29).
    *   **Arpegiador:** Pista reservada para una feature futura (fantasma en el MVP).
    *   **Percusión:** Base rítmica en 4/4 con la caja en el beat 3 y plato en negras (por defecto), más un bombo que clona dinámicamente los acentos del bajo. Plato configurable (hi-hat abierto/cerrado, ride, crash o china) y opción *double time* (caja en 2 y 4 y plato en corcheas).
*   **Densidad:** Controla el número de notas del patrón principal (Baja/Media/Alta).
*   **Selección de Tonalidad y Escala:** Elige la nota central (tónica, 12 notas solo sostenidos) y el modo (Mayor, Menor (Eólica), Menor Armónica, Frigio o Frigio Dominante).
*   **Exportación Multipista:** Genera archivos `.mid` de 5 pistas listos para importar en Ableton Live, FL Studio, Logic, Reaper o Bitwig.
*   **Generación por Lotes:** Produce de 1 a 5 variaciones de los mismos parámetros en una sola pasada.

> **Nota (caso límite de densidad):** si la duración del patrón es menor que la menor duración permitida seleccionada (p. ej. patrón de `0.25` beats con solo la Negra habilitada), la combinación es infactible para el rango de densidad y la última nota se ajustará al resto exacto, pudiendo quedar fuera del pool de duraciones elegido. No se tratará por ahora.

---

## 🧩 ¿Cómo Funciona la Polimetría en CLIff?

Imagina una pieza de 8 compases en 4/4 (**32 beats totales**) y un patrón principal de **7 beats**:

```text
Estructura global (32 beats en 4/4):
[ Compás 1 | Compás 2 | Compás 3 | Compás 4 | Compás 5 | Compás 6 | Compás 7 | Compás 8 ]

Distribución del patrón de 7 beats:
[ Patrón 1 (7b) ] [ Patrón 2 (7b) ] [ Patrón 3 (7b) ] [ Patrón 4 (7b) ] [ Tail (4b) ]
```

El motor calcula que el patrón entra **4 veces completas** (7 x 4 = 28 beats) y genera automáticamente un **Tail de 4 beats** (los primeros 4 beats del patrón) para cerrar la estructura perfectamente antes del siguiente ciclo.

---

## 🛠️ Requisitos e Instalación

### Prerrequisitos
*   **Python 3.10+**

### Instalación del Proyecto

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/CLIff.git
cd CLIff

# Crear y activar el entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## 🚀 Uso

Ejecuta el programa principal para abrir la interfaz de consola interactiva:

```bash
python main.py
```

Flujo de uso en la terminal:

1.  **Ajustes Globales:** Introduce el tempo (BPM) y la cantidad de compases.
2.  **Estructura del Patrón:** Define la duración del patrón (en *beats*), la respiración del Pad (`0` para *Drone Infinito*), el modo (Mono/Acorde) y el registro (Grave/Agudo) del Pad.
3.  **Reglas Algorítmicas:** Selecciona la nota central (tónica), la escala, las duraciones permitidas, el salto melódico máximo, la densidad (Baja/Media/Alta), el plato (hi-hat abierto/cerrado, ride, crash o china) y, solo en 4/4, si quieres activar el *double time*.
4.  **Mezclador (opcional):** Decide si quieres ajustar *velocity* y volumen por pista (por defecto se usan valores neutros).
5.  **Lote:** Indica cuántas variaciones generar (1-5).
6.  **Generación:** Genera las piezas y, desde el resumen, usa **💾 Exportar** para guardar los archivos `.mid` en `/output` (o en la carpeta que elijas).

---

## 📁 Archivos Generados

Los archivos se guardan en `/output` con un nombre que combina tónica, escala, compás, BPM, fecha y un número de orden:

*   `output/c_eolian_44_146bpm_05102026_1.mid` $\rightarrow$ Archivo MIDI multipista (5 pistas).

El número final se incrementa automáticamente para no sobrescribir archivos anteriores del mismo día.

---

## 🗺️ Feature Futuras (Roadmap)

1. Guardado y carga de semillas numéricas (*Seeds*) para reproducir o compartir patrones exactos.
2. Algoritmos de variación dinámica de *velocity* y silencios rítmicos.
3. Grados negativos por debajo de la tónica principal en el bajo.
4. Soporte para métricas compuestas y no cuaternarias (3/4, 6/8, 12/8).
5. Compilación a ejecutable independiente sin dependencias externas (`.exe` / `.app`).
6. Implementación del Arpegiador (hoy pista fantasma en el MVP).
7. Tail generado como nuevo motivo (en lugar de truncado del patrón).
8. Selección de instrumento por pista.
