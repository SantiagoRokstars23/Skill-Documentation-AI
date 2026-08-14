"""Tests del comando `analyze` (V0.5)."""

from __future__ import annotations

import json

from ._cli_helpers import EXAMPLE_PROJECT, run_cli


def test_analyze_valid_project_exits_zero(capsys):
    exit_code, out, _ = run_cli(capsys, ["analyze", str(EXAMPLE_PROJECT)])
    assert exit_code == 0
    assert "Controllers" in out
    assert "Endpoints" in out
    assert "DTOs" in out


def test_analyze_nonexistent_project_is_usage_error(capsys, tmp_path):
    missing = tmp_path / "does-not-exist"
    exit_code, _, err = run_cli(capsys, ["analyze", str(missing)])
    assert exit_code == 2
    assert str(missing) in err


def test_analyze_json_report_shape(capsys):
    exit_code, out, err = run_cli(capsys, ["analyze", str(EXAMPLE_PROJECT), "--json"])
    assert exit_code == 0
    assert err == ""
    report = json.loads(out)
    assert report["project"] == str(EXAMPLE_PROJECT)
    assert report["status"] == "ok"
    assert isinstance(report["endpoints"], int) and report["endpoints"] > 0
    assert isinstance(report["controllers"], int) and report["controllers"] > 0
    assert isinstance(report["dtos"], int) and report["dtos"] > 0
    assert set(report["diagnostics"]) == {"errors", "warnings", "info"}
    assert "outputs" not in report


def test_analyze_json_never_embeds_openapi_document(capsys):
    _, out, _ = run_cli(capsys, ["analyze", str(EXAMPLE_PROJECT), "--json"])
    report = json.loads(out)
    assert "document" not in report
    assert "openapi" not in report


def test_analyze_openapi_without_output_writes_document_to_stdout_and_banner_to_stderr(capsys):
    exit_code, out, err = run_cli(
        capsys, ["analyze", str(EXAMPLE_PROJECT), "--openapi", "--format", "yaml"]
    )
    assert exit_code == 0
    assert out.strip().startswith("openapi:")
    assert "Analysis" in err


def test_analyze_openapi_with_output_writes_file(capsys, tmp_path):
    output_path = tmp_path / "openapi.json"
    exit_code, out, err = run_cli(
        capsys,
        ["analyze", str(EXAMPLE_PROJECT), "--openapi", "--format", "json", "--output", str(output_path)],
    )
    assert exit_code == 0
    assert output_path.exists()
    written_text = output_path.read_text(encoding="utf-8")
    document = json.loads(written_text)
    assert document["openapi"] == "3.0.3"
    # con --output, el documento no se imprime por stdout (solo el resumen humano).
    assert written_text.strip() not in out


def test_analyze_openapi_json_requires_output(capsys):
    exit_code, _, err = run_cli(
        capsys, ["analyze", str(EXAMPLE_PROJECT), "--openapi", "--json"]
    )
    assert exit_code == 2
    assert "--output" in err


def test_analyze_openapi_json_report_includes_outputs(capsys, tmp_path):
    output_path = tmp_path / "openapi.yaml"
    exit_code, out, _ = run_cli(
        capsys,
        ["analyze", str(EXAMPLE_PROJECT), "--openapi", "--output", str(output_path), "--json"],
    )
    assert exit_code == 0
    report = json.loads(out)
    assert report["outputs"] == {"openapi": str(output_path)}
    assert "document" not in report


def test_analyze_output_without_openapi_is_usage_error(capsys, tmp_path):
    output_path = tmp_path / "openapi.yaml"
    exit_code, _, err = run_cli(
        capsys, ["analyze", str(EXAMPLE_PROJECT), "--output", str(output_path)]
    )
    assert exit_code == 2
    assert "--openapi" in err
    assert not output_path.exists()


def test_analyze_dto_count_matches_manual_traversal(capsys):
    """DTOs anidados (Address dentro de CustomerRequest) deben contarse una sola vez
    y de forma consistente con analyzer.analyze_project (ver cli/commands.py::count_dtos)."""
    from analyzer import analyze_project

    from cli.commands import count_dtos

    result = analyze_project(EXAMPLE_PROJECT)
    expected = count_dtos(result)

    exit_code, out, _ = run_cli(capsys, ["analyze", str(EXAMPLE_PROJECT), "--json"])
    assert exit_code == 0
    report = json.loads(out)
    assert report["dtos"] == expected
    assert expected > 0
