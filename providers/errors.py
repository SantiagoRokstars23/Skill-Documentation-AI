"""Jerarquia de excepciones propia de ``providers/`` (V0.6).

Los proveedores concretos deben traducir cualquier excepcion de su mecanismo de
comunicacion (HTTP, SDK, etc.) a una de estas clases, para que el resto del
proyecto pueda manejar errores de LLM sin conocer los detalles internos de un
proveedor especifico. Ver docs/06-LLM.md.

Ningun mensaje de estas excepciones debe incluir el valor de una credencial.
"""

from __future__ import annotations


class LLMProviderError(Exception):
    """Base de todas las excepciones de ``providers/``."""


class ProviderNotConfiguredError(LLMProviderError):
    """No se proporciono ninguna configuracion de provider (``ProviderConfig``)."""


class UnknownProviderError(LLMProviderError):
    """``ProviderConfig.provider`` no corresponde a ningun provider registrado."""


class MissingCredentialError(LLMProviderError):
    """El provider requiere una credencial (p. ej. ``api_key``) y no se proporciono."""


class InvalidModelError(LLMProviderError):
    """El modelo indicado no es valido para el provider seleccionado."""


class ProviderTimeoutError(LLMProviderError):
    """El provider no respondio dentro del tiempo esperado."""


class ProviderRequestError(LLMProviderError):
    """El provider respondio con un error (p. ej. HTTP 4xx/5xx)."""


class InvalidResponseError(LLMProviderError):
    """La respuesta del provider no tiene el formato esperado."""
