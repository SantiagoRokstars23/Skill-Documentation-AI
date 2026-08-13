"""Interfaz conceptual de LLM Provider.

Define el contrato que cualquier proveedor de LLM debera implementar para ser usado
por el sistema, sin acoplar el proyecto a ningun proveedor concreto. Ver
docs/06-LLM.md. No existen implementaciones concretas en V0.1 (Scope Lock, ver
prompts/V0.1-foundation.md seccion 19).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Contrato uniforme para invocar un modelo de lenguaje.

    Cualquier proveedor concreto (Claude, Gemini, OpenAI u otro compatible) debe
    heredar de esta clase e implementar ``generate``. Ningun componente por encima de
    esta interfaz debe depender de un proveedor especifico (docs/03-Arquitectura.md).
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Invoca el modelo subyacente con ``prompt`` y devuelve el texto generado."""
        raise NotImplementedError
