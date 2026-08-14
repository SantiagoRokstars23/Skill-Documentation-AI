"""Interfaz conceptual de LLM Provider.

Define el contrato que cualquier proveedor de LLM debera implementar para ser usado
por el sistema, sin acoplar el proyecto a ningun proveedor concreto. Ver
docs/06-LLM.md. Sin cambios desde V0.1: V0.6 anade infraestructura alrededor de
esta interfaz (``providers/config.py``, ``providers/errors.py``,
``providers/registry.py``) y una implementacion Fake/Mock (``providers/fake.py``),
pero no modifica el contrato de ``LLMProvider`` en si. No existe todavia ningun
provider comercial concreto (ver docs/12-Roadmap.md).
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
