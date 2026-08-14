"""Paquete de LLM Providers.

Desde V0.1: la interfaz conceptual (``LLMProvider``, ver ``providers/base.py``).
Desde V0.6: infraestructura de providers (configuracion, errores, seleccion por
nombre) y una implementacion Fake/Mock determinista para tests (``FakeProvider``).
Desde V0.7: primer provider comercial real, ``AnthropicProvider``
(``providers/anthropic.py``), implementado unicamente con stdlib (sin el SDK
``anthropic``, ver docs/06-LLM.md). Ningun otro componente del proyecto
(Analyzer/Generator/Validator/CLI/Skill) depende de ``providers/`` ni de que
haya credenciales configuradas.
"""

from __future__ import annotations

from .anthropic import AnthropicProvider
from .base import LLMProvider
from .config import ProviderConfig
from .errors import (
    InvalidModelError,
    InvalidResponseError,
    LLMProviderError,
    MissingCredentialError,
    ProviderNotConfiguredError,
    ProviderRequestError,
    ProviderTimeoutError,
    UnknownProviderError,
)
from .fake import FakeProvider
from .registry import get_provider

__all__ = [
    "AnthropicProvider",
    "FakeProvider",
    "InvalidModelError",
    "InvalidResponseError",
    "LLMProvider",
    "LLMProviderError",
    "MissingCredentialError",
    "ProviderConfig",
    "ProviderNotConfiguredError",
    "ProviderRequestError",
    "ProviderTimeoutError",
    "UnknownProviderError",
    "get_provider",
]
