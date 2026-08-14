"""Tests de aislamiento (V0.6, secc. 9/14): Analyzer/Generator/Validator/CLI deben
seguir funcionando sin ninguna configuracion de LLM, y ninguno de esos paquetes
debe importar providers/ (el desacoplamiento es en ambas direcciones)."""

from __future__ import annotations

from pathlib import Path

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
