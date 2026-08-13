"""Paquete de LLM Providers.

En V0.1 solo existe la interfaz conceptual (``LLMProvider``, ver ``providers/base.py``).
No hay implementaciones concretas de proveedores; estas son objeto de V0.5 (ver
docs/12-Roadmap.md y docs/06-LLM.md).
"""

from __future__ import annotations

from .base import LLMProvider

__all__ = ["LLMProvider"]
