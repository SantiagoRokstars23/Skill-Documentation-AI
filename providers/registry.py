"""Seleccion de provider por nombre (V0.6).

Mecanismo minimo: un diccionario de nombre -> constructor. Deliberadamente no es
una clase Factory ni un sistema de plugins (ver Fase 2 de
prompts/V0.6-LLM-PROVIDERS-&-AI-FOUNDATION.md, seccion 3: no asumir un patron sin
justificarlo). Anadir un provider nuevo consiste en registrar una entrada aqui.
"""

from __future__ import annotations

from collections.abc import Callable

from .base import LLMProvider
from .config import ProviderConfig
from .errors import ProviderNotConfiguredError, UnknownProviderError
from .fake import FakeProvider

_REGISTRY: dict[str, Callable[[ProviderConfig], LLMProvider]] = {
    "fake": lambda config: FakeProvider(),
}


def get_provider(config: ProviderConfig) -> LLMProvider:
    """Resuelve ``config`` a una instancia de ``LLMProvider``.

    Lanza ``ProviderNotConfiguredError`` si no se indico ningun provider, o
    ``UnknownProviderError`` si el nombre indicado no esta registrado. Cualquier
    otro requisito del provider concreto (credencial, modelo valido) lo valida su
    propio constructor, no este modulo.
    """
    if not config.provider:
        raise ProviderNotConfiguredError(
            "No se configuro ningun provider (ProviderConfig.provider esta vacio)."
        )
    try:
        factory = _REGISTRY[config.provider]
    except KeyError:
        raise UnknownProviderError(
            f"Provider desconocido: '{config.provider}'. Providers disponibles: "
            f"{sorted(_REGISTRY)}."
        ) from None
    return factory(config)
