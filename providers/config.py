"""Configuracion de LLM Providers (V0.6).

``ProviderConfig`` es la unica forma de configurar un provider: por variables de
entorno (``from_env``) o por construccion explicita (util para tests y para
cualquier consumidor que prefiera inyeccion directa). Ninguna de las dos vias
asume un valor por defecto para la credencial: si no se proporciona, queda en
``None`` (ver providers/registry.py y providers/errors.py::MissingCredentialError
para como se reporta la ausencia).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

ENV_PREFIX = "SPRING_DOC_LLM_"


@dataclass(frozen=True)
class ProviderConfig:
    """Configuracion minima para seleccionar y construir un ``LLMProvider``.

    ``api_key`` se excluye deliberadamente de la representacion por defecto
    (``repr``/``str``) para que nunca aparezca en logs o mensajes de error por
    accidente (ver seccion 7 de prompts/V0.6-LLM-PROVIDERS-&-AI-FOUNDATION.md).
    """

    provider: str
    model: str | None = None
    api_key: str | None = field(default=None, repr=False)
    timeout: float | None = None
    """Timeout en segundos, opcional. ``None`` significa "no configurado": el
    provider concreto decide su propio valor seguro por defecto (ver
    providers/anthropic.py::DEFAULT_TIMEOUT_SECONDS). ``ProviderConfig`` no
    valida el valor (ni que sea positivo, ni que sea numerico si viene de
    ``from_env``) -- transporta datos, la validacion vive en el provider."""

    @classmethod
    def from_env(cls, *, prefix: str = ENV_PREFIX) -> ProviderConfig:
        """Construye la configuracion a partir de variables de entorno:
        ``{prefix}PROVIDER``, ``{prefix}MODEL``, ``{prefix}API_KEY``,
        ``{prefix}TIMEOUT`` (opcional).

        ``{prefix}PROVIDER`` es obligatoria (sin ella no hay provider que
        seleccionar); su ausencia se reporta como cadena vacia, y es
        responsabilidad de quien resuelva el provider (``providers.registry``)
        decidir que hacer con una configuracion incompleta -- ``ProviderConfig``
        en si mismo no valida ni lanza excepciones, solo transporta datos.
        ``{prefix}TIMEOUT`` se intenta convertir a ``float``; si esta ausente o
        no es un numero valido, ``timeout`` queda en ``None`` (nunca lanza).
        """
        raw_timeout = os.environ.get(f"{prefix}TIMEOUT")
        try:
            timeout = float(raw_timeout) if raw_timeout else None
        except ValueError:
            timeout = None
        return cls(
            provider=os.environ.get(f"{prefix}PROVIDER", ""),
            model=os.environ.get(f"{prefix}MODEL") or None,
            api_key=os.environ.get(f"{prefix}API_KEY") or None,
            timeout=timeout,
        )
