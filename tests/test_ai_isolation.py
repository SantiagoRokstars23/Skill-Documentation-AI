"""Tests de aislamiento de la capa ai/ (V0.8, secciones 2 y 30):

- analyzer/generators/validator/cli no dependen de ai/.
- ai/ no importa internals del Analyzer (ast_analyzer/ast_backend/dto_analyzer/
  spring_boot_analyzer/scanner) ni conoce AnthropicProvider/urllib/SDK de
  ningun proveedor -- solo la abstraccion providers.LLMProvider.
- skill/ y skills/ tampoco dependen de ai/.

Se inspeccionan los imports reales via ``ast`` (no busqueda de substrings en
todo el archivo): los docstrings de ai/ mencionan a proposito nombres como
"AnthropicProvider"/"ast_analyzer" en prosa para explicar que NO se usan, y
una busqueda de texto plano los marcaria como falsos positivos.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOWNSTREAM_PACKAGES = ["analyzer", "generators", "validator", "cli"]
AI_FILES = sorted((REPO_ROOT / "ai").glob("*.py"))

FORBIDDEN_ANALYZER_INTERNAL_MODULES = {
    "ast_analyzer",
    "ast_backend",
    "dto_analyzer",
    "spring_boot_analyzer",
    "scanner",
}

FORBIDDEN_PROVIDER_SPECIFIC_MODULES = {
    "anthropic",
    "urllib",
    "urllib.request",
    "urllib.error",
}

FORBIDDEN_PROVIDER_SPECIFIC_NAMES = {"AnthropicProvider"}


def _imported_module_roots(source_file: Path) -> set[str]:
    """Nombres de modulo realmente importados (``import x``/``from x import
    y``), no texto libre del archivo."""
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _imported_names(source_file: Path) -> set[str]:
    """Nombres concretos importados via ``from modulo import Nombre``."""
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.name)
    return names


def test_no_downstream_package_imports_ai_module():
    for package_name in DOWNSTREAM_PACKAGES:
        for source_file in sorted((REPO_ROOT / package_name).glob("*.py")):
            modules = _imported_module_roots(source_file)
            assert not any(m == "ai" or m.startswith("ai.") for m in modules), (
                f"{package_name}/{source_file.name} importa 'ai' -- "
                "Analyzer/Generator/Validator/CLI no deben depender de la capa AI."
            )


def test_skill_files_do_not_reference_ai_layer():
    for skill_dir in (REPO_ROOT / "skill", REPO_ROOT / "skills"):
        for source_file in sorted(skill_dir.rglob("*.md")):
            text = source_file.read_text(encoding="utf-8")
            assert "ai/" not in text and "ai.models" not in text and "ai.context" not in text, (
                f"{source_file.relative_to(REPO_ROOT)} referencia la capa ai/ -- "
                "la Skill debe seguir siendo independiente del motor."
            )


def test_ai_does_not_import_analyzer_internals():
    for source_file in AI_FILES:
        modules = _imported_module_roots(source_file)
        offending = {
            m
            for m in modules
            if m.split(".")[-1] in FORBIDDEN_ANALYZER_INTERNAL_MODULES
        }
        assert not offending, (
            f"ai/{source_file.name} importa {sorted(offending)} -- ai/ solo debe "
            "usar la API publica de analyzer."
        )


def test_ai_does_not_import_provider_specifics():
    for source_file in AI_FILES:
        modules = _imported_module_roots(source_file)
        offending_modules = {
            m for m in modules if m.split(".")[0] in FORBIDDEN_PROVIDER_SPECIFIC_MODULES
        }
        assert not offending_modules, (
            f"ai/{source_file.name} importa {sorted(offending_modules)} -- ai/ solo "
            "debe conocer la abstraccion providers.LLMProvider."
        )

        names = _imported_names(source_file)
        offending_names = names & FORBIDDEN_PROVIDER_SPECIFIC_NAMES
        assert not offending_names, (
            f"ai/{source_file.name} importa {sorted(offending_names)} -- ai/ solo "
            "debe conocer la abstraccion providers.LLMProvider."
        )


def test_ai_does_not_import_cli():
    for source_file in AI_FILES:
        modules = _imported_module_roots(source_file)
        assert not any(m == "cli" or m.startswith("cli.") for m in modules), (
            f"ai/{source_file.name} importa 'cli' -- ai/ no debe conocer la CLI."
        )
