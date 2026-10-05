# CLIff
## A Polymetric MIDI Generator (CLI)

> **A CLI-based algorithmic MIDI generator for polymetric riffs and mathematical pattern composition.**

**CLIff** (*Command Line Interface + Riff*) es un generador algorítmico de música por consola diseñado para productores, compositores y entusiastas del *math rock*, metal progresivo y música electrónica experimental.

La herramienta permite crear secuencias MIDI multipista basadas en **desfases métricos (polimetrías)** —como encajar patrones de 7 *beats* sobre estructuras globales en 4/4— calculando automáticamente los remates de residuo (*tails*) y exportando archivos MIDI listos para usar en cualquier DAW.

---

## 🎵 Características Principales

*   **Motor de Polimetría y Residuo:** Define la duración del patrón principal en *beats* asimétricos. CLIff repite el patrón y calcula un remate (*tail*) truncado para completar la métrica global sin descarrilar el compás.
*   **4 Pistas Autogeneradas:**
    *   **Pad:** Sostén armónico sobre la tónica. Incluye modo *Drone Infinito* (respiración = 0), modo *Mono/Acorde* y registro *Grave/Medio/Agudo*.
    *   **Bajo:** Ejecuta la línea melódica principal (el *riff*) generada por el algoritmo.
    *   **Arpegiador:** Pista reservada para una feature futura (fantasma en el MVP).
    *   **Percusión:** Base rítmica fija en 4/4 (caja y charles) con un bombo que clona dinámicamente los acentos del bajo.
*   **Densidad:** Controla el número de notas del patrón principal (Baja/Media/Alta).
*   **Selección Escalar:** Trabaja sobre la nota Do (C) en modos Mayor, Menor (Eólica), Menor Armónica, Frigio y Frigio Dominante.
*   **Exportación Multipista:** Genera archivos `.mid` de 4 pistas listos para importar en Ableton Live, FL Studio, Logic, Reaper o Bitwig.

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
2.  **Estructura del Patrón:** Define la duración del patrón (en *beats*), la respiración del Pad (`0` para *Drone Infinito*), el modo (Mono/Acorde) y el registro (Grave/Medio/Agudo) del Pad.
3.  **Reglas Algorítmicas:** Selecciona las duraciones permitidas, el salto melódico máximo y la densidad (Baja/Media/Alta).
4.  **Mezclador:** Ajusta el *velocity* y el volumen por pista.
5.  **Generación:** Genera la pieza y, desde el resumen, usa **💾 Exportar** para guardar el archivo `.mid` en `/output` (o en la carpeta que elijas).

---

## 📁 Archivos Generados

Los archivos se guardan en `/output` con el nombre de los parámetros utilizados:

*   `output/cliff_160bpm_p7.mid` $\rightarrow$ Archivo MIDI multipista (4 pistas).

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
9. Mejora de la convención de nombres de archivo.
