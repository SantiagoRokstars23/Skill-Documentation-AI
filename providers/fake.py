"""Provider Fake/Mock (V0.6): implementacion deterministica de ``LLMProvider`` sin
red, sin credenciales y sin aleatoriedad, pensada para tests -- propios y de
cualquier consumidor futuro que necesite ejercitar la infraestructura de
providers sin depender de un servicio externo (ver seccion 6 de
prompts/V0.6-LLM-PROVIDERS-&-AI-FOUNDATION.md).
"""

from __future__ import annotations

from .base import LLMProvider

DEFAULT_RESPONSE = "fake response"


class FakeProvider(LLMProvider):
    """Devuelve siempre la misma respuesta configurada, sin inspeccionar
    ``prompt`` mas alla de recibirlo. No simula errores: quien necesite probar
    manejo de errores de provider debe usar ``providers.errors`` directamente."""

    def __init__(self, response: str = DEFAULT_RESPONSE) -> None:
        self._response = response

    def generate(self, prompt: str) -> str:
        return self._response
