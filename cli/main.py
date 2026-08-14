"""Punto de entrada de la CLI ``spring-doc`` (V0.5).

Orquesta ``analyzer`` -> ``generators`` -> ``validator`` a traves de sus APIs
publicas (ver docs/03-Arquitectura.md). Esta capa no contiene logica de
analisis, generacion ni validacion propia: solo parseo de argumentos,
despacho, decision de exit code y manejo de errores de entrada/internos.
"""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

from . import commands, output
from .errors import CliUsageError


def _package_version() -> str:
    try:
        return version("skill-documentation-ai")
    except PackageNotFoundError:
        return "unknown"


def _build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--strict", action="store_true", help="Los diagnostics WARNING tambien fallan el proceso."
    )
    common.add_argument(
        "--quiet", action="store_true", help="Suprime el resumen humano cuando no hay errores."
    )
    common.add_argument(
        "--json", action="store_true", dest="json_mode", help="Reporte estructurado para automatizacion."
    )

    parser = argparse.ArgumentParser(
        prog="spring-doc",
        description=(
            "Analiza, genera y valida documentacion OpenAPI de microservicios "
            "Java/Spring Boot."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"spring-doc {_package_version()}"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser(
        "analyze", parents=[common], help="Analiza un proyecto Spring Boot."
    )
    analyze_parser.add_argument("project", help="Ruta al proyecto Spring Boot.")
    analyze_parser.add_argument(
        "--openapi", action="store_true", help="Ademas genera y valida el OpenAPI del proyecto."
    )
    analyze_parser.add_argument(
        "--format",
        choices=["json", "yaml"],
        default="yaml",
        help="Formato del OpenAPI generado (solo aplica junto con --openapi).",
    )
    analyze_parser.add_argument(
        "--output",
        default=None,
        help="Ruta de salida del OpenAPI generado (solo aplica junto con --openapi).",
    )

    generate_parser = subparsers.add_parser(
        "generate", parents=[common], help="Genera el OpenAPI de un proyecto Spring Boot."
    )
    generate_parser.add_argument("project", help="Ruta al proyecto Spring Boot.")
    generate_parser.add_argument(
        "--format", choices=["json", "yaml"], default="yaml", help="Formato del OpenAPI generado."
    )
    generate_parser.add_argument(
        "--output", default=None, help="Ruta de salida del OpenAPI generado."
    )

    validate_parser = subparsers.add_parser(
        "validate", parents=[common], help="Valida un documento OpenAPI ya construido."
    )
    validate_parser.add_argument("openapi_file", help="Ruta al archivo OpenAPI (JSON o YAML).")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "analyze":
            outcome = commands.run_analyze(
                args.project,
                openapi=args.openapi,
                fmt=args.format,
                output=args.output,
                json_mode=args.json_mode,
            )
            counts = commands.count_by_severity(outcome.diagnostics)
            status = commands.resolve_status(counts, strict=args.strict)
            output.print_analyze(
                outcome, counts=counts, status=status, quiet=args.quiet, json_mode=args.json_mode
            )
            return commands.status_to_exit_code(status)

        if args.command == "generate":
            outcome = commands.run_generate(
                args.project, fmt=args.format, output=args.output, json_mode=args.json_mode
            )
            counts = commands.count_by_severity(outcome.diagnostics)
            status = commands.resolve_status(counts, strict=args.strict)
            output.print_generate(
                outcome, counts=counts, status=status, quiet=args.quiet, json_mode=args.json_mode
            )
            return commands.status_to_exit_code(status)

        outcome = commands.run_validate(args.openapi_file)
        counts = commands.count_by_severity(outcome.diagnostics)
        status = commands.resolve_status(counts, strict=args.strict)
        output.print_validate(
            outcome, counts=counts, status=status, quiet=args.quiet, json_mode=args.json_mode
        )
        return commands.status_to_exit_code(status)

    except CliUsageError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return commands.EXIT_USAGE
    except Exception as exc:  # noqa: BLE001 - limite superior intencional: separa
        # errores de uso (CliUsageError, arriba) de bugs internos inesperados; ver
        # prompts/V0.5-CLI-&-DEVELOPER-EXPERIENCE.md seccion 4.7.
        print(f"Error interno inesperado: {exc}", file=sys.stderr)
        return commands.EXIT_INTERNAL


if __name__ == "__main__":
    sys.exit(main())
