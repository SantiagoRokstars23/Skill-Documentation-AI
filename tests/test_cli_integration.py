"""Tests de integracion de la CLI (V0.5): pipeline completo contra
examples/customer-service, determinismo, y el limite arquitectonico de la
seccion 4.9 de la directriz (la CLI solo importa las APIs publicas de
analyzer/generators/validator, nunca sus modulos internos)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from ._cli_helpers import EXAMPLE_PROJECT, run_cli

CLI_SOURCE_FILES = sorted((Path(__file__).resolve().parent.parent / "cli").glob("*.py"))

FORBIDDEN_IMPORTS = (
    "ast_analyzer",
    "ast_backend",
    "dto_analyzer",
    "spring_boot_analyzer",
    "analyzer.scanner",
    "openapi_types",
    "openapi_schemas",
    "openapi_rules",
    "javalang",
)


def test_cli_modules_do_not_import_internal_engines():
    for source_file in CLI_SOURCE_FILES:
        text = source_file.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_IMPORTS:
            assert forbidden not in text, f"{source_file.name} referencia '{forbidden}'"


def test_full_pipeline_analyze_generate_validate(capsys, tmp_path):
    output_path = tmp_path / "openapi.yaml"

    exit_code, out, err = run_cli(
        capsys,
        ["analyze", str(EXAMPLE_PROJECT), "--openapi", "--output", str(output_path), "--json"],
    )
    assert exit_code == 0
    analyze_report = json.loads(out)
    assert analyze_report["outputs"]["openapi"] == str(output_path)
    assert output_path.exists()

    exit_code, out, _ = run_cli(capsys, ["validate", str(output_path), "--json"])
    validate_report = json.loads(out)
    assert exit_code in (0, 1)
    assert validate_report["diagnostics"]["errors"] == 0


def test_generate_then_validate_matches_direct_library_calls(capsys, tmp_path):
    """La CLI no debe producir un documento distinto al que producen las
    APIs publicas directamente (no hay logica de generacion propia en la CLI)."""
    from analyzer import analyze_project
    from generators import generate, to_yaml

    output_path = tmp_path / "openapi.yaml"
    exit_code, _, _ = run_cli(
        capsys, ["generate", str(EXAMPLE_PROJECT), "--format", "yaml", "--output", str(output_path)]
    )
    assert exit_code == 0

    result = analyze_project(EXAMPLE_PROJECT)
    expected_document, _ = generate(result)

    written_document = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert written_document == expected_document
    assert to_yaml(expected_document) == output_path.read_text(encoding="utf-8")


def test_analyze_json_report_is_deterministic_across_runs(capsys):
    _, first_out, _ = run_cli(capsys, ["analyze", str(EXAMPLE_PROJECT), "--json"])
    _, second_out, _ = run_cli(capsys, ["analyze", str(EXAMPLE_PROJECT), "--json"])
    assert first_out == second_out


def test_generate_document_is_deterministic_across_runs(capsys):
    _, first_out, _ = run_cli(capsys, ["generate", str(EXAMPLE_PROJECT), "--format", "json"])
    _, second_out, _ = run_cli(capsys, ["generate", str(EXAMPLE_PROJECT), "--format", "json"])
    assert first_out == second_out


def test_relative_and_absolute_project_paths_yield_same_result(capsys, monkeypatch):
    """Verifica manejo de rutas de forma portable (pathlib) en vez de asumir un
    formato de ruta especifico de un sistema operativo."""
    repo_root = Path(__file__).resolve().parent.parent
    monkeypatch.chdir(repo_root)

    _, out_relative, _ = run_cli(
        capsys, ["analyze", "examples/customer-service", "--json"]
    )
    _, out_absolute, _ = run_cli(
        capsys, ["analyze", str(EXAMPLE_PROJECT), "--json"]
    )

    relative_report = json.loads(out_relative)
    absolute_report = json.loads(out_absolute)
    for key in ("endpoints", "controllers", "dtos", "diagnostics", "status"):
        assert relative_report[key] == absolute_report[key]


def test_output_path_with_nested_subdirectory_is_portable(capsys, tmp_path):
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    output_path = nested / "openapi.yaml"
    exit_code, _, _ = run_cli(
        capsys, ["generate", str(EXAMPLE_PROJECT), "--output", str(output_path)]
    )
    assert exit_code == 0
    assert output_path.exists()
