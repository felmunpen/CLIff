# CLIff
## A Polymetric MIDI Generator (CLI)

> **A CLI-based algorithmic MIDI generator for polymetric riffs and mathematical pattern composition.**

**CLIff** (*Command Line Interface + Riff*) es un generador algorítmico de música por consola diseñado para productores, compositores y entusiastas del *math rock*, metal progresivo y música electrónica experimental. 

La herramienta permite crear secuencias MIDI multipista basadas en **desfases métricos (polimetrías)** —como encajar patrones de 7 *beats* sobre estructuras globales en 4/4— calculando automáticamente los remates de residuo (*tails*), ofreciendo una preescucha instantánea mediante SoundFonts y exportando archivos MIDI listos para usar en cualquier DAW.

---

## 🎵 Características Principales

*   **Motor de Polimetría y Residuo:** Define la duración del patrón principal en *beats* asimétricos. CLIff repite el patrón y calcula un remate (*tail*) truncado para completar la métrica global sin descarrilar el compás.
*   **4 Pistas Autogeneradas:**
    *   **Pad:** Sostén armónico sobre la tónica. Incluye modo *Drone Infinito* (respiración = 0).
    *   **Bajo / Guitarra:** Ejecuta la línea melódica principal generada por el algoritmo.
    *   **Arpegiador:** Movimiento rápido recorriendo los grados de la escala seleccionada.
    *   **Percusión:** Base rítmica fija en 4/4 (caja y charles) con un bombo que clona dinámicamente los acentos del bajo.
*   **Selección Escalar:** Trabaja sobre la nota Do (C) en modos Mayor, Menor (Eólica), Menor Armónica, Frigio y Frigio Dominante.
*   **Preescucha Inmediata:** Renderizado automático a audio (`.wav`) mediante una SoundFont integrada para evaluar las secuencias directamente desde la terminal.
*   **Exportación Multipista:** Genera archivos `.mid` de 4 canales listos para importar en Ableton Live, FL Studio, Logic, Reaper o Bitwig.

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
*   **FluidSynth** (requerido para el renderizado y preescucha de audio en tiempo real).

#### Instalación de FluidSynth:
*   **macOS:** `brew install fluidsynth`
*   **Linux (Ubuntu/Debian):** `sudo apt install fluidsynth`
*   **Windows:** Descargar el ejecutable oficial o instalar vía `winget install FluidSynth`.

### Instalación del Proyecto

```bash
# Clonar el repositorio
git clone [https://github.com/tu-usuario/cliff.git](https://github.com/tu-usuario/cliff.git)
cd cliff

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
2.  **Estructura del Patrón:** Define la duración del patrón (en *beats*) y la respiración del Pad (`0` para *Drone Infinito*).
3.  **Reglas Algorítmicas:** Selecciona las duraciones permitidas (negra, corchea, semicorchea...) y el salto melódico máximo.
4.  **Mezclador:** Ajusta el nivel de volumen y *velocity* plano para cada pista.
5.  **Generación:** Escucha la claqueta de inicio, reproduce el audio renderizado y localiza tus archivos en la carpeta `/output`.

---

## 📁 Archivos Generados

Los archivos procesados se guardan en el directorio `/output` con el nombre de los parámetros utilizados:

*   `output/cliff_160bpm_p7.mid` $\rightarrow$ Archivo MIDI multipista (4 canales).
*   `output/cliff_160bpm_p7.wav` $\rightarrow$ Audio renderizado con la SoundFont por defecto.

---

## 🗺️ Roadmap (Futuras Versiones)

*   [ ] Guardado y carga de Semillas Numéricas (*Seeds*) para reproducir o compartir patrones exactos.
*   [ ] Algoritmos de variación dinámica de *velocity* y silencios rítmicos.
*   [ ] Grados negativos por debajo de la tónica principal en el bajo.
*   [ ] Soporte para métricas compuestas y no cuaternarias (3/4, 6/8, 12/8).
*   [ ] Compilación a ejecutable independiente sin dependencias externas (`.exe` / `.app`).