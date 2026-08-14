"""Tests del comando `generate` (V0.5)."""

from __future__ import annotations

import json

import yaml

from ._cli_helpers import EXAMPLE_PROJECT, run_cli


def test_generate_default_format_is_yaml_to_stdout(capsys):
    exit_code, out, err = run_cli(capsys, ["generate", str(EXAMPLE_PROJECT)])
    assert exit_code == 0
    parsed = yaml.safe_load(out)
    assert parsed["openapi"] == "3.0.3"
    assert "generated" in err.lower() or "OpenAPI" in err


def test_generate_format_json_to_stdout(capsys):
    exit_code, out, _ = run_cli(capsys, ["generate", str(EXAMPLE_PROJECT), "--format", "json"])
    assert exit_code == 0
    parsed = json.loads(out)
    assert parsed["openapi"] == "3.0.3"


def test_generate_output_writes_yaml_file(capsys, tmp_path):
    output_path = tmp_path / "sub" / "openapi.yaml"
    exit_code, out, _ = run_cli(
        capsys, ["generate", str(EXAMPLE_PROJECT), "--format", "yaml", "--output", str(output_path)]
    )
    assert exit_code == 0
    assert output_path.exists()
    parsed = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert parsed["openapi"] == "3.0.3"
    assert parsed["info"]["title"]


def test_generate_output_writes_json_file(capsys, tmp_path):
    output_path = tmp_path / "openapi.json"
    exit_code, _, _ = run_cli(
        capsys, ["generate", str(EXAMPLE_PROJECT), "--format", "json", "--output", str(output_path)]
    )
    assert exit_code == 0
    parsed = json.loads(output_path.read_text(encoding="utf-8"))
    assert parsed["openapi"] == "3.0.3"


def test_generate_nonexistent_project_is_usage_error(capsys, tmp_path):
    missing = tmp_path / "nope"
    exit_code, _, err = run_cli(capsys, ["generate", str(missing)])
    assert exit_code == 2
    assert str(missing) in err


def test_generate_json_report_requires_output(capsys):
    exit_code, _, err = run_cli(capsys, ["generate", str(EXAMPLE_PROJECT), "--json"])
    assert exit_code == 2
    assert "--output" in err


def test_generate_json_report_shape(capsys, tmp_path):
    output_path = tmp_path / "openapi.yaml"
    exit_code, out, err = run_cli(
        capsys, ["generate", str(EXAMPLE_PROJECT), "--output", str(output_path), "--json"]
    )
    assert exit_code == 0
    assert err == ""
    report = json.loads(out)
    assert report["project"] == str(EXAMPLE_PROJECT)
    assert report["status"] == "ok"
    assert report["outputs"] == {"openapi": str(output_path)}
    assert set(report["diagnostics"]) == {"errors", "warnings", "info"}
    assert "document" not in report
    assert "openapi" not in report  # el documento nunca viaja embebido en el reporte


def test_generate_output_creates_missing_parent_directories(capsys, tmp_path):
    nested_output = tmp_path / "does" / "not" / "exist" / "openapi.yaml"
    exit_code, _, _ = run_cli(
        capsys, ["generate", str(EXAMPLE_PROJECT), "--output", str(nested_output)]
    )
    assert exit_code == 0
    assert nested_output.exists()


def test_generate_invalid_output_path_is_usage_error(capsys, tmp_path):
    # tmp_path es un directorio existente: no se puede escribir un archivo encima.
    exit_code, _, err = run_cli(
        capsys, ["generate", str(EXAMPLE_PROJECT), "--output", str(tmp_path)]
    )
    assert exit_code == 2
    assert "Error" in err
