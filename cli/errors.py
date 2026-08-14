"""Excepciones propias de la CLI (V0.5).

Distinguen errores de entrada del usuario de errores internos inesperados (ver
prompts/V0.5-CLI-&-DEVELOPER-EXPERIENCE.md, seccion 4.7). ``cli/main.py`` es el
unico lugar que traduce estas excepciones a un exit code.
"""

from __future__ import annotations


class CliUsageError(Exception):
    """Error de uso de la CLI: ruta inexistente, combinacion de opciones invalida,
    ruta de salida no escribible. Se traduce siempre a exit code 2, sin traceback."""
