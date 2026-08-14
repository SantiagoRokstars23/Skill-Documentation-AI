"""Tests del parser de la CLI (V0.5): help, version, comandos y argumentos
invalidos. No dependen de texto decorativo, solo de exit codes y presencia de
subcadenas estables (nombres de comandos/opciones)."""

from __future__ import annotations

import pytest

from cli.main import main


def test_help_top_level_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "analyze" in out
    assert "generate" in out
    assert "validate" in out


def test_help_subcommand_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["generate", "--help"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "--format" in out
    assert "--output" in out


def test_version_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "spring-doc" in out


def test_no_command_exits_nonzero_usage_error():
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code == 2


def test_unknown_command_exits_with_usage_error():
    with pytest.raises(SystemExit) as exc_info:
        main(["frobnicate"])
    assert exc_info.value.code == 2


def test_unknown_format_value_exits_with_usage_error():
    with pytest.raises(SystemExit) as exc_info:
        main(["generate", "some-project", "--format", "xml"])
    assert exc_info.value.code == 2


def test_missing_required_positional_exits_with_usage_error():
    with pytest.raises(SystemExit) as exc_info:
        main(["analyze"])
    assert exc_info.value.code == 2
