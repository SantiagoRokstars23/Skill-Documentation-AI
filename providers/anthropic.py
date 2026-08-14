"""Provider real de Anthropic (V0.7), implementado unicamente con stdlib
(``urllib.request``/``urllib.error``/``json``) -- sin el SDK ``anthropic``, sin
dependencias nuevas (ver Fase 2 de
prompts/V0.7—LLM-REAL-PROVIDER-&-AI-FOUNDATION.md).

Implementa exclusivamente ``prompt -> texto`` contra el endpoint de Mensajes de
Anthropic. Sin streaming, tool calling, imagenes, archivos, conversaciones ni
memoria (fuera de alcance de V0.7).

Ninguna excepcion de ``urllib`` ni del proveedor se propaga al consumidor:
todo se traduce a ``providers.errors``.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .base import LLMProvider
from .config import ProviderConfig
from .errors import (
    InvalidModelError,
    InvalidResponseError,
    MissingCredentialError,
    ProviderRequestError,
    ProviderTimeoutError,
)

API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

# Valor seguro por defecto cuando ProviderConfig.timeout no viene configurado
# (o llega invalido/no positivo). No se pasa timeout=None a urlopen: eso
# significaria "usar el timeout global del socket", potencialmente indefinido.
DEFAULT_TIMEOUT_SECONDS = 60.0

# La API de Anthropic exige 'max_tokens' en cada request; no forma parte de la
# configuracion pedida por la directriz de V0.7, asi que se fija un valor
# razonable en vez de agregar una opcion nueva no solicitada.
DEFAULT_MAX_TOKENS = 1024


def _extract_error_message(body_bytes: bytes) -> str | None:
    """Intenta extraer 'error.message' de un cuerpo de error de Anthropic.
    Nunca lanza: si el cuerpo no es JSON o no tiene la forma esperada, devuelve
    None y el llamador usa un mensaje generico con solo el codigo HTTP."""
    try:
        data = json.loads(body_bytes.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str):
                return message
    return None


def _extract_text(data: object) -> str:
    if not isinstance(data, dict):
        raise InvalidResponseError("La respuesta de Anthropic no es un objeto JSON.")
    content = data.get("content")
    if not isinstance(content, list):
        raise InvalidResponseError(
            "La respuesta de Anthropic no tiene 'content' con el formato esperado."
        )
    texts = [
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    joined = "".join(texts)
    if not joined:
        raise InvalidResponseError("La respuesta de Anthropic no contiene texto.")
    return joined


class AnthropicProvider(LLMProvider):
    """``LLMProvider`` real contra la API de Anthropic (Messages API).

    Requiere ``config.api_key`` y ``config.model`` explicitos -- sin modelo por
    defecto (ver decision de Fase 2: un default hardcodeado quedaria
    silenciosamente desactualizado a medida que Anthropic publica modelos
    nuevos). Ambos se validan en la construccion, antes de cualquier llamada de
    red (falla rapido, mismo patron ya documentado en providers/registry.py).
    """

    def __init__(self, config: ProviderConfig) -> None:
        if not config.api_key:
            raise MissingCredentialError(
                "AnthropicProvider requiere ProviderConfig.api_key."
            )
        if not config.model:
            raise InvalidModelError(
                "AnthropicProvider requiere ProviderConfig.model (no hay modelo "
                "por defecto)."
            )
        self._api_key = config.api_key
        self._model = config.model
        self._timeout = (
            config.timeout if config.timeout and config.timeout > 0 else DEFAULT_TIMEOUT_SECONDS
        )

    def generate(self, prompt: str) -> str:
        payload = json.dumps(
            {
                "model": self._model,
                "max_tokens": DEFAULT_MAX_TOKENS,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")

        request = urllib.request.Request(
            API_URL,
            data=payload,
            method="POST",
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                raw_body = response.read()
        except TimeoutError as exc:
            # Timeout durante la lectura de la respuesta (despues de conectar):
            # urllib deja propagar un TimeoutError/socket.timeout directo, sin
            # envolverlo en URLError -- ver el except de abajo para la otra fase.
            raise ProviderTimeoutError(
                f"Anthropic no respondio dentro de {self._timeout}s."
            ) from exc
        except urllib.error.HTTPError as exc:
            body_bytes = exc.read()
            detail = _extract_error_message(body_bytes) or f"HTTP {exc.code}"
            raise ProviderRequestError(
                f"Anthropic devolvio un error (HTTP {exc.code}): {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            # Timeout durante la conexion/envio de la request: urllib.request
            # captura el OSError/TimeoutError original y lo re-lanza envuelto
            # como URLError(reason=<TimeoutError>) -- no llega como TimeoutError
            # directo, hay que revisar exc.reason explicitamente para no
            # clasificarlo como un error HTTP/de conexion generico.
            if isinstance(exc.reason, TimeoutError):
                raise ProviderTimeoutError(
                    f"Anthropic no respondio dentro de {self._timeout}s."
                ) from exc
            raise ProviderRequestError(
                f"No se pudo completar la request a Anthropic: {exc.reason}"
            ) from exc

        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise InvalidResponseError(
                "La respuesta de Anthropic no es JSON valido."
            ) from exc

        return _extract_text(data)
