"""Tests de la jerarquia de excepciones de providers/ (V0.6)."""

from __future__ import annotations

from providers import (
    InvalidModelError,
    InvalidResponseError,
    LLMProviderError,
    MissingCredentialError,
    ProviderNotConfiguredError,
    ProviderRequestError,
    ProviderTimeoutError,
    UnknownProviderError,
)

ALL_ERROR_CLASSES = [
    ProviderNotConfiguredError,
    UnknownProviderError,
    MissingCredentialError,
    InvalidModelError,
    ProviderTimeoutError,
    ProviderRequestError,
    InvalidResponseError,
]


def test_all_provider_errors_are_llm_provider_errors():
    for error_class in ALL_ERROR_CLASSES:
        assert issubclass(error_class, LLMProviderError)


def test_llm_provider_error_is_a_plain_exception():
    assert issubclass(LLMProviderError, Exception)


def test_catching_base_class_catches_any_concrete_error():
    for error_class in ALL_ERROR_CLASSES:
        try:
            raise error_class("boom")
        except LLMProviderError as exc:
            assert isinstance(exc, error_class)
        else:
            raise AssertionError(f"{error_class} did not propagate as LLMProviderError")


def test_error_classes_are_distinct():
    assert len(set(ALL_ERROR_CLASSES)) == len(ALL_ERROR_CLASSES)
