"""Tests del comando `validate` (V0.5)."""

from __future__ import annotations

import json

from generators import generate, to_json, to_yaml

from analyzer import analyze_project

from ._cli_helpers import EXAMPLE_PROJECT, run_cli


def _write_example_openapi(tmp_path, *, fmt: str):
    result = analyze_project(EXAMPLE_PROJECT)
    document, _ = generate(result)
    text = to_json(document) if fmt == "json" else to_yaml(document)
    path = tmp_path / f"openapi.{fmt}"
    path.write_text(text, encoding="utf-8")
    return path


def test_validate_valid_yaml_file(capsys, tmp_path):
    path = _write_example_openapi(tmp_path, fmt="yaml")
    exit_code, out, _ = run_cli(capsys, ["validate", str(path)])
    assert exit_code in (0, 1)  # el documento tiene WARNING/INFO esperados, no ERROR
    assert "Errors: 0" in out


def test_validate_valid_json_file(capsys, tmp_path):
    path = _write_example_openapi(tmp_path, fmt="json")
    exit_code, out, _ = run_cli(capsys, ["validate", str(path)])
    assert exit_code in (0, 1)
    assert "Errors: 0" in out


def test_validate_nonexistent_file_is_usage_error(capsys, tmp_path):
    missing = tmp_path / "missing.yaml"
    exit_code, _, err = run_cli(capsys, ["validate", str(missing)])
    assert exit_code == 2
    assert str(missing) in err


def test_validate_invalid_yaml_content_is_diagnostic_not_usage_error(capsys, tmp_path):
    path = tmp_path / "broken.yaml"
    path.write_text("not: [valid: yaml: at: all", encoding="utf-8")
    exit_code, out, _ = run_cli(capsys, ["validate", str(path), "--json"])
    assert exit_code == 1  # error de validacion (contenido), no de uso de la CLI
    report = json.loads(out)
    assert report["status"] == "error"
    assert report["diagnostics"]["errors"] >= 1


def test_validate_document_not_an_object_is_diagnostic(capsys, tmp_path):
    path = tmp_path / "not-object.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    exit_code, out, _ = run_cli(capsys, ["validate", str(path), "--json"])
    assert exit_code == 1
    report = json.loads(out)
    assert report["diagnostics"]["errors"] >= 1


def test_validate_json_report_shape(capsys, tmp_path):
    path = _write_example_openapi(tmp_path, fmt="yaml")
    exit_code, out, err = run_cli(capsys, ["validate", str(path), "--json"])
    assert err == ""
    report = json.loads(out)
    assert report["file"] == str(path)
    assert report["status"] in ("ok", "error")
    assert set(report["diagnostics"]) == {"errors", "warnings", "info"}
    assert "outputs" not in report


def test_validate_unknown_extension_falls_back_to_yaml_parser(capsys, tmp_path):
    path = _write_example_openapi(tmp_path, fmt="yaml")
    renamed = path.with_suffix(".openapi")
    renamed.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    exit_code, out, _ = run_cli(capsys, ["validate", str(renamed)])
    assert exit_code in (0, 1)
    assert "Errors: 0" in out


def test_validate_file_not_valid_utf8_is_usage_error_not_internal_error(capsys, tmp_path):
    """Regresion: un archivo no-UTF-8 (o sin permisos de lectura) debia producir un
    error interno no controlado (exit 3) en vez de un error de uso (exit 2),
    porque run_validate no protegia path.read_text() como si lo hace
    write_output_file() con OSError. Ver cli/commands.py::run_validate."""
    path = tmp_path / "not-utf8.yaml"
    path.write_bytes(b"\xff\xfe\x00\x01invalid-utf8-bytes")
    exit_code, _, err = run_cli(capsys, ["validate", str(path)])
    assert exit_code == 2
    assert "Error" in err
