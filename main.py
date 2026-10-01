"""Punto de entrada de CLIff."""

import tempfile

from cliff import tui


def main() -> None:
    # Directorio temporal de trabajo: se elimina automáticamente al cerrar la app.
    with tempfile.TemporaryDirectory(prefix="cliff_") as tmpdir:
        tui.run(tmpdir)


if __name__ == "__main__":
    main()
