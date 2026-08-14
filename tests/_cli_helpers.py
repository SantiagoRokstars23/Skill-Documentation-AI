"""Helper compartido por los tests de la CLI (V0.5). No es un modulo de test (sin
prefijo ``test_``): pytest no lo recolecta."""

from __future__ import annotations

from pathlib import Path

from cli.main import main

EXAMPLE_PROJECT = Path(__file__).resolve().parent.parent / "examples" / "customer-service"


def run_cli(capsys, argv: list[str]) -> tuple[int, str, str]:
    """Ejecuta ``cli.main.main`` en proceso y devuelve ``(exit_code, stdout, stderr)``."""
    exit_code = main(argv)
    captured = capsys.readouterr()
    return exit_code, captured.out, captured.err
