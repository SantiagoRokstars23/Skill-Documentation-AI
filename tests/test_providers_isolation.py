"""Tests de aislamiento (V0.6 secc. 9/14, reafirmado en V0.7 secc. 11):
Analyzer/Generator/Validator/CLI/Skill deben seguir funcionando sin ninguna
configuracion de LLM (ni siquiera con un provider real como AnthropicProvider
disponible en providers/), y ninguno de esos paquetes debe importar
providers/ -- el desacoplamiento es en ambas direcciones. Tambien verifica que
importar providers/ o construir su configuracion nunca dispara una llamada de
red por si solo."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from ._cli_helpers import EXAMPLE_PROJECT, run_cli

REPO_ROOT = Path(__file__).resolve().parent.parent
DOWNSTREAM_PACKAGES = ["analyzer", "generators", "validator", "cli"]


def test_no_downstream_package_imports_providers():
    for package_name in DOWNSTREAM_PACKAGES:
        for source_file in sorted((REPO_ROOT / package_name).glob("*.py")):
            text = source_file.read_text(encoding="utf-8")
            assert "providers" not in text, (
                f"{package_name}/{source_file.name} referencia 'providers' "
                "-- Analyzer/Generator/Validator/CLI no deben depender de LLM."
            )


def test_skill_files_do_not_import_providers():
    skill_dirs = [REPO_ROOT / "skill", REPO_ROOT / "skills"]
    for skill_dir in skill_dirs:
        for source_file in sorted(skill_dir.rglob("*.md")):
            text = source_file.read_text(encoding="utf-8")
            assert "providers/" not in text and "providers." not in text, (
                f"{source_file.relative_to(REPO_ROOT)} referencia 'providers' "
                "-- la Skill no debe depender de la infraestructura de LLM Providers."
            )


def test_importing_providers_never_calls_urlopen():
    with patch("urllib.request.urlopen") as mock_urlopen:
        import importlib

        import providers

        importlib.reload(providers)
        from providers import AnthropicProvider, FakeProvider, ProviderConfig  # noqa: F401

        mock_urlopen.assert_not_called()


def test_analyzer_works_without_any_llm_env_configured(monkeypatch):
    monkeypatch.delenv("SPRING_DOC_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("SPRING_DOC_LLM_MODEL", raising=False)
    monkeypatch.delenv("SPRING_DOC_LLM_API_KEY", raising=False)

    from analyzer import analyze_project

    result = analyze_project(EXAMPLE_PROJECT)
    assert len(result.endpoints) > 0


def test_generator_and_validator_work_without_any_llm_env_configured(monkeypatch):
    monkeypatch.delenv("SPRING_DOC_LLM_PROVIDER", raising=False)

    from analyzer import analyze_project
    from generators import generate
    from validator import validate

    result = analyze_project(EXAMPLE_PROJECT)
    document, _ = generate(result)
    diagnostics = validate(document)
    assert isinstance(diagnostics, list)


def test_cli_works_without_any_llm_env_configured(capsys, monkeypatch):
    monkeypatch.delenv("SPRING_DOC_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("SPRING_DOC_LLM_MODEL", raising=False)
    monkeypatch.delenv("SPRING_DOC_LLM_API_KEY", raising=False)

    exit_code, out, _ = run_cli(capsys, ["analyze", str(EXAMPLE_PROJECT), "--json"])
    assert exit_code == 0
    assert out != ""
