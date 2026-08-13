"""Descubrimiento de archivos fuente Java dentro de un proyecto."""

from __future__ import annotations

from pathlib import Path


def discover_java_files(root: str | Path) -> list[Path]:
    """Devuelve la lista de archivos ``.java`` bajo ``root``, ordenada de forma estable.

    Si ``root`` no existe o no contiene archivos ``.java``, devuelve una lista vacia en
    vez de lanzar una excepcion: un proyecto incompleto o vacio es un caso valido para
    el Analyzer (ver docs/07-Analisis.md).
    """
    root_path = Path(root)
    if not root_path.exists():
        return []
    return sorted(root_path.rglob("*.java"))
