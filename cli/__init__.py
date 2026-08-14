"""CLI ``spring-doc`` (V0.5): capa delgada de orquestacion de linea de comandos
sobre ``analyzer``/``generators``/``validator``.

Ver docs/03-Arquitectura.md y prompts/V0.5-CLI-&-DEVELOPER-EXPERIENCE.md. Este
paquete no reimplementa analisis, generacion ni validacion: solo parseo de
argumentos, despacho a las APIs publicas de los otros paquetes, y presentacion
del resultado (humano o ``--json``).
"""

from __future__ import annotations

from .main import main

__all__ = ["main"]
