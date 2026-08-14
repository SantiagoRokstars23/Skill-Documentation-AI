"""Tests de providers.registry.get_provider (V0.6)."""

from __future__ import annotations

import pytest

from providers import (
    FakeProvider,
    ProviderConfig,
    ProviderNotConfiguredError,
    UnknownProviderError,
    get_provider,
)


def test_get_provider_resolves_fake():
    provider = get_provider(ProviderConfig(provider="fake"))
    assert isinstance(provider, FakeProvider)


def test_get_provider_unknown_name_raises():
    with pytest.raises(UnknownProviderError):
        get_provider(ProviderConfig(provider="does-not-exist"))


def test_get_provider_empty_provider_raises_not_configured():
    with pytest.raises(ProviderNotConfiguredError):
        get_provider(ProviderConfig(provider=""))


def test_get_provider_fake_does_not_require_credentials():
    # 'fake' no necesita api_key; no debe lanzar MissingCredentialError.
    provider = get_provider(ProviderConfig(provider="fake", api_key=None))
    assert provider.generate("x") == "fake response"


def test_unknown_provider_error_message_lists_available_providers():
    with pytest.raises(UnknownProviderError, match="fake"):
        get_provider(ProviderConfig(provider="does-not-exist"))
