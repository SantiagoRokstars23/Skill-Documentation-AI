"""Analizador estatico de anotaciones Spring MVC / Spring Boot.

Extrae Endpoint/Parameter a partir del texto fuente de archivos .java, sin ejecutar
codigo ni requerir un entorno Java. Ver docs/07-Analisis.md para el diseno y las
limitaciones conocidas de este enfoque basado en expresiones regulares y balance de
brackets/parentesis (en lugar de un AST completo de Java).
"""

from __future__ import annotations

import re
from pathlib import Path

from .models import Endpoint, Evidence, Parameter, ParameterSource

_MAPPING_ANNOTATIONS = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "DeleteMapping": "DELETE",
    "PatchMapping": "PATCH",
}
_VALID_HTTP_METHODS = frozenset(_MAPPING_ANNOTATIONS.values())

_ANNOTATION_RE = re.compile(r"@(\w+)")
_CLASS_RE = re.compile(r"\bclass\s+(\w+)")
_METHOD_SIG_RE = re.compile(
    r"(?:public|private|protected)\s+(?:static\s+)?(?:[\w$.\[\]<>,?\s]+?)\s+(\w+)\s*\("
)
_STRING_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def analyze_file(path: str | Path) -> tuple[list[Endpoint], list[str]]:
    """Analiza un unico archivo .java. Nunca lanza excepcion por contenido invalido:
    devuelve una lista vacia de endpoints y un warning describiendo el problema."""
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [], [f"{file_path}: no se pudo leer el archivo ({exc}); se omite."]
    return _scan_file(text, str(file_path))


# ---------------------------------------------------------------------------
# Escaneo de nivel de archivo / clase
# ---------------------------------------------------------------------------


def _scan_file(text: str, file_label: str) -> tuple[list[Endpoint], list[str]]:
    endpoints: list[Endpoint] = []
    warnings: list[str] = []
    n = len(text)
    i = 0
    pending: list[tuple[str, str]] = []

    while i < n:
        i = _skip_ws_and_comments(text, i)
        if i >= n:
            break
        c = text[i]

        if c in ('"', "'"):
            i = _skip_literal(text, i)
            continue

        if c == "@":
            parsed = _parse_annotation(text, i)
            if parsed is None:
                i += 1
                continue
            name, args, end = parsed
            pending.append((name, args))
            i = end
            continue

        match = _CLASS_RE.match(text, i)
        if match:
            class_name = match.group(1)
            brace_idx = text.find("{", match.end())
            if brace_idx == -1:
                pending = []
                i = match.end()
                continue
            close_idx = _find_matching(text, brace_idx, "{", "}")
            if close_idx == -1:
                pending = []
                i = brace_idx + 1
                continue

            annotation_names = {name for name, _ in pending}
            if "RestController" in annotation_names:
                base_path = ""
                for name, args in pending:
                    if name == "RequestMapping":
                        base_path = _extract_path(args) or ""
                body = text[brace_idx + 1 : close_idx]
                class_endpoints, class_warnings = _scan_methods(
                    body, brace_idx + 1, text, class_name, base_path, file_label
                )
                endpoints.extend(class_endpoints)
                warnings.extend(class_warnings)

            pending = []
            i = close_idx + 1
            continue

        if c in ";{}":
            pending = []
            i += 1
            continue

        i += 1

    return endpoints, warnings


def _scan_methods(
    body: str,
    body_offset: int,
    full_text: str,
    controller_name: str,
    base_path: str,
    file_label: str,
) -> tuple[list[Endpoint], list[str]]:
    endpoints: list[Endpoint] = []
    warnings: list[str] = []
    n = len(body)
    i = 0
    pending: list[tuple[str, str]] = []

    while i < n:
        i = _skip_ws_and_comments(body, i)
        if i >= n:
            break
        c = body[i]

        if c in ('"', "'"):
            i = _skip_literal(body, i)
            continue

        if c == "@":
            parsed = _parse_annotation(body, i)
            if parsed is None:
                i += 1
                continue
            name, args, end = parsed
            pending.append((name, args))
            i = end
            continue

        match = _METHOD_SIG_RE.match(body, i)
        if match:
            method_name = match.group(1)
            paren_idx = match.end() - 1
            close_paren_idx = _find_matching(body, paren_idx, "(", ")")
            if close_paren_idx == -1:
                pending = []
                i = match.end()
                continue

            http_method, path_from_annotation, mapping_found = _resolve_mapping(pending)
            if mapping_found:
                if http_method is None:
                    warnings.append(
                        f"{file_label}: metodo '{method_name}' en '{controller_name}' "
                        "tiene un mapping sin metodo HTTP explicito; se omite."
                    )
                else:
                    params_text = body[paren_idx + 1 : close_paren_idx]
                    parameters = _parse_parameters(params_text)
                    line_no = full_text.count("\n", 0, body_offset + match.start()) + 1
                    endpoints.append(
                        Endpoint(
                            controller=controller_name,
                            endpoint=_join_paths(base_path, path_from_annotation or ""),
                            method=http_method,
                            parameters=tuple(parameters),
                            evidence=Evidence(file=file_label, line=line_no),
                        )
                    )

            pending = []
            i = close_paren_idx + 1
            continue

        if c in ";{}":
            pending = []
            i += 1
            continue

        i += 1

    return endpoints, warnings


def _resolve_mapping(
    pending: list[tuple[str, str]]
) -> tuple[str | None, str | None, bool]:
    http_method: str | None = None
    path: str | None = None
    found = False
    for name, args in pending:
        if name in _MAPPING_ANNOTATIONS:
            found = True
            http_method = _MAPPING_ANNOTATIONS[name]
            extracted_path = _extract_path(args)
            if extracted_path is not None:
                path = extracted_path
        elif name == "RequestMapping":
            found = True
            extracted_path = _extract_path(args)
            if extracted_path is not None:
                path = extracted_path
            explicit_method = _extract_http_method(args)
            if explicit_method is not None:
                http_method = explicit_method
    return http_method, path, found


# ---------------------------------------------------------------------------
# Parametros
# ---------------------------------------------------------------------------


def _parse_parameters(params_text: str) -> list[Parameter]:
    parameters: list[Parameter] = []
    for raw in _split_top_level(params_text, ","):
        parameter = _parse_parameter(raw)
        if parameter is not None:
            parameters.append(parameter)
    return parameters


def _parse_parameter(raw: str) -> Parameter | None:
    raw = raw.strip()
    if not raw:
        return None

    annotations: list[tuple[str, str]] = []
    i = 0
    n = len(raw)
    while i < n:
        i = _skip_ws_and_comments(raw, i)
        if i >= n or raw[i] != "@":
            break
        parsed = _parse_annotation(raw, i)
        if parsed is None:
            break
        name, args, end = parsed
        annotations.append((name, args))
        i = end

    rest = raw[i:].strip()
    tokens = [t for t in rest.split() if t != "final"]
    if len(tokens) < 2:
        return None

    param_name = tokens[-1]
    param_type = " ".join(tokens[:-1])
    ann_map = {name: args for name, args in annotations}

    if "PathVariable" in ann_map:
        args = ann_map["PathVariable"]
        explicit_name = _extract_name_attr(args)
        return Parameter(
            name=explicit_name or param_name,
            type=param_type,
            source=ParameterSource.PATH,
            required=not _has_required_false(args),
        )

    if "RequestParam" in ann_map:
        args = ann_map["RequestParam"]
        explicit_name = _extract_name_attr(args)
        has_default = bool(re.search(r"\bdefaultValue\s*=", args))
        return Parameter(
            name=explicit_name or param_name,
            type=param_type,
            source=ParameterSource.QUERY,
            required=not (_has_required_false(args) or has_default),
        )

    if "RequestBody" in ann_map:
        args = ann_map["RequestBody"]
        return Parameter(
            name=param_name,
            type=param_type,
            source=ParameterSource.BODY,
            required=not _has_required_false(args),
        )

    return None


def _has_required_false(args: str) -> bool:
    return bool(re.search(r"\brequired\s*=\s*false\b", args))


def _extract_name_attr(args: str) -> str | None:
    args = args.strip()
    if not args:
        return None
    if args.startswith('"'):
        match = _STRING_RE.match(args)
        return match.group(1) if match else None
    match = re.search(r'\b(?:value|name)\s*=\s*"((?:[^"\\]|\\.)*)"', args)
    return match.group(1) if match else None


def _extract_path(args: str) -> str | None:
    args = args.strip()
    if not args:
        return None
    if args.startswith('"'):
        match = _STRING_RE.match(args)
        return match.group(1) if match else None
    match = re.search(r'\b(?:value|path)\s*=\s*"((?:[^"\\]|\\.)*)"', args)
    return match.group(1) if match else None


def _extract_http_method(args: str) -> str | None:
    matches = re.findall(r"\bRequestMethod\.(\w+)", args)
    if len(matches) != 1:
        return None
    method = matches[0].upper()
    return method if method in _VALID_HTTP_METHODS else None


def _join_paths(base: str, path: str) -> str:
    base = base.strip()
    path = path.strip()
    if not base:
        combined = path if path.startswith("/") else f"/{path}" if path else "/"
    else:
        combined = f"{base.rstrip('/')}/{path.lstrip('/')}" if path else base
    if not combined.startswith("/"):
        combined = f"/{combined}"
    if len(combined) > 1 and combined.endswith("/"):
        combined = combined.rstrip("/")
    return combined or "/"


def _split_top_level(text: str, sep: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth_paren = 0
    depth_angle = 0
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in ('"', "'"):
            j = _skip_literal(text, i)
            current.append(text[i:j])
            i = j
            continue
        if c == "(":
            depth_paren += 1
        elif c == ")":
            depth_paren -= 1
        elif c == "<":
            depth_angle += 1
        elif c == ">" and depth_angle > 0:
            depth_angle -= 1
        if c == sep and depth_paren == 0 and depth_angle == 0:
            parts.append("".join(current))
            current = []
            i += 1
            continue
        current.append(c)
        i += 1
    last = "".join(current)
    if last.strip():
        parts.append(last)
    return parts


# ---------------------------------------------------------------------------
# Utilidades de bajo nivel: literales, comentarios y balance de brackets
# ---------------------------------------------------------------------------


def _parse_annotation(text: str, at: int) -> tuple[str, str, int] | None:
    match = _ANNOTATION_RE.match(text, at)
    if not match:
        return None
    name = match.group(1)
    j = _skip_ws_and_comments(text, match.end())
    if j < len(text) and text[j] == "(":
        close = _find_matching(text, j, "(", ")")
        if close == -1:
            return name, "", len(text)
        return name, text[j + 1 : close], close + 1
    return name, "", match.end()


def _skip_ws_and_comments(text: str, i: int) -> int:
    n = len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif text.startswith("//", i):
            nl = text.find("\n", i)
            i = n if nl == -1 else nl + 1
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
        else:
            break
    return i


def _skip_literal(text: str, i: int) -> int:
    n = len(text)
    quote = text[i]
    j = i + 1
    while j < n:
        if text[j] == "\\":
            j += 2
            continue
        if text[j] == quote:
            return j + 1
        j += 1
    return n


def _find_matching(text: str, open_index: int, open_char: str, close_char: str) -> int:
    n = len(text)
    depth = 0
    i = open_index
    while i < n:
        c = text[i]
        if text.startswith("//", i):
            nl = text.find("\n", i)
            i = n if nl == -1 else nl + 1
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        if c in ('"', "'"):
            i = _skip_literal(text, i)
            continue
        if c == open_char:
            depth += 1
        elif c == close_char:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1
