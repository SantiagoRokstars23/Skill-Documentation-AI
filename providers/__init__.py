"""Paquete de LLM Providers.

Desde V0.1: la interfaz conceptual (``LLMProvider``, ver ``providers/base.py``).
Desde V0.6: infraestructura de providers (configuracion, errores, seleccion por
nombre) y una implementacion Fake/Mock determinista para tests (``FakeProvider``).
No hay ningun provider comercial real implementado (ver docs/12-Roadmap.md y
docs/06-LLM.md); no es necesario para que ningun otro componente del proyecto
(Analyzer/Generator/Validator/CLI) funcione.
"""

from __future__ import annotations

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
