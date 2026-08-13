"""Aisla la dependencia de terceros ``javalang`` del resto del Analyzer.

Decision arquitectonica V0.2 (ver docs/03-Arquitectura.md y docs/07-Analisis.md):
V0.2 introduce ``javalang`` como motor de parsing principal (AST semantico), con el
motor de V0.1 (``analyzer/spring_boot_analyzer.py``, regex + balanceo de brackets) como
fallback por archivo cuando ``javalang`` no puede parsear un archivo (sintaxis no
soportada o codigo malformado). Ningun otro modulo del Analyzer debe importar
``javalang`` directamente para invocarlo o capturar sus excepciones: deben usar
``parse_file`` y las utilidades de este modulo, de forma que un futuro cambio de motor
AST (ver evaluacion Regex vs AST en el reporte de Fase 2) quede contenido aqui.

``analyzer/ast_analyzer.py`` y ``analyzer/dto_analyzer.py`` si importan tipos de arbol
de ``javalang.tree`` directamente para recorrerlo (isinstance/atributos): encapsular
por completo la forma del AST detras de una capa propia de nodos supondria una
abstraccion no justificada para el alcance de V0.2 (regla global 12 de V0.1, seccion 7
de la directriz V0.2). El limite que se mantiene es: la invocacion del parser, la
traduccion de sus excepciones, y las utilidades genericas de extraccion de valores
(tipos, argumentos de anotacion, literales) viven unicamente aqui.
"""

from __future__ import annotations

from pathlib import Path

import javalang
import javalang.tree

_COLLECTION_TYPE_NAMES = frozenset({"List", "Set", "Collection", "Iterable", "Optional"})


class AstParseError(Exception):
    """Un archivo no pudo leerse o parsearse como AST Java.

    Cubre tanto errores de lectura/codificacion como errores de sintaxis o lexer de
    ``javalang``. Quien reciba esta excepcion debe recurrir al motor de fallback
    (``analyzer/spring_boot_analyzer.py``) para ese archivo, nunca inventar un
    resultado.
    """


def parse_file(path: str | Path) -> tuple[javalang.tree.CompilationUnit, str]:
    """Lee y parsea un archivo ``.java``. Devuelve ``(unidad_de_compilacion, texto)``.

    Lanza ``AstParseError`` ante cualquier fallo de lectura o de parsing; nunca
    propaga excepciones de ``javalang`` directamente, para que el resto del Analyzer
    no dependa de su superficie de excepciones.
    """
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise AstParseError(f"no se pudo leer el archivo: {exc}") from exc
    try:
        unit = javalang.parse.parse(text)
    except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError) as exc:
        raise AstParseError(f"error de sintaxis Java: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - defensivo: javalang no mantiene una
        # superficie de excepciones exhaustivamente documentada (sin releases desde
        # 2020, ver reporte de Fase 2); cualquier fallo de parsing debe degradar al
        # fallback en vez de interrumpir analyze_project.
        raise AstParseError(f"fallo inesperado de javalang: {exc}") from exc
    return unit, text


def simple_name(name: str | None) -> str | None:
    """Devuelve el ultimo segmento de un nombre de anotacion/tipo.

    ``javalang`` conserva el nombre tal como aparece en el codigo fuente: si esta
    fully-qualified (``org.springframework...RestController``) lo devuelve completo.
    Comparar solo por el segmento final resuelve la limitacion de V0.1 de no reconocer
    anotaciones fully-qualified (ver docs/07-Analisis.md).
    """
    if name is None:
        return None
    return name.rsplit(".", 1)[-1]


def annotation_args(node) -> dict[str, object]:
    """Normaliza ``node.element`` (o ``node.annotation.element``) de una anotacion a un
    dict de nombre de atributo -> nodo de valor.

    El ``element`` de ``javalang`` cambia de forma segun como se escribio la
    anotacion: ``None`` (anotacion sin argumentos), un unico nodo de valor
    (``@GetMapping("/x")``, atributo posicional ``value``), o una lista de
    ``ElementValuePair`` (``@RequestParam(required = false)``). Esta funcion unifica
    los tres casos.
    """
    element = getattr(node, "element", None)
    if element is None:
        return {}
    if isinstance(element, list):
        return {pair.name: pair.value for pair in element}
    return {"value": element}


def literal_text(value_node) -> str | None:
    """Convierte un nodo de valor de anotacion a texto legible, sin interpretar su
    significado (evidencia, no inferencia).

    Devuelve ``None`` cuando el nodo no es un caso reconocido (evitar inventar un
    texto para una forma no soportada de ``javalang``).
    """
    if value_node is None:
        return None
    if isinstance(value_node, javalang.tree.Literal):
        return str(value_node.value).strip('"')
    if isinstance(value_node, javalang.tree.MemberReference):
        qualifier = f"{value_node.qualifier}." if value_node.qualifier else ""
        return f"{qualifier}{value_node.member}"
    if isinstance(value_node, javalang.tree.ElementArrayValue):
        parts = [literal_text(v) for v in value_node.values]
        return ", ".join(p for p in parts if p is not None)
    return None


def _walk_reference_chain(type_node):
    """Sigue la cadena ``sub_type`` de un tipo calificado (p. ej. ``java.util.List``,
    que ``javalang`` representa como ``ReferenceType(name="java", sub_type=ReferenceType(
    name="util", sub_type=ReferenceType(name="List", arguments=[...])))``).

    Devuelve ``(nombres_en_orden, nodo_final)``; ``nodo_final`` es el segmento que
    lleva los ``arguments``/``dimensions`` reales del tipo completo.
    """
    names = []
    node = type_node
    leaf = type_node
    while node is not None:
        names.append(node.name)
        leaf = node
        node = getattr(node, "sub_type", None)
    return names, leaf


def leaf_name(type_node) -> str | None:
    """Nombre simple (ultimo segmento) de un tipo, resolviendo nombres calificados
    (``java.util.List`` -> ``"List"``, ``Address`` -> ``"Address"``)."""
    if type_node is None:
        return None
    _, leaf = _walk_reference_chain(type_node)
    return getattr(leaf, "name", None)


def type_to_text(type_node) -> str:
    """Reconstruye el texto de un tipo Java (``ReferenceType``/``BasicType`` de
    ``javalang``) preservando el nombre calificado, genericos y arrays, p. ej.
    ``"List<CustomerResponse>"`` o ``"java.util.List<String>"``.

    Devuelve ``"void"`` para un tipo de retorno ausente (metodo sin valor de retorno).
    Para argumentos de tipo no resueltos (wildcards ``?``/``? extends X``) devuelve
    ``"?"`` en vez de suponer un tipo concreto.
    """
    if type_node is None:
        return "void"
    name = getattr(type_node, "name", None)
    if name is None:
        return "?"
    names, leaf = _walk_reference_chain(type_node)
    dotted_name = ".".join(names)
    dimensions = "[]" * len(
        getattr(leaf, "dimensions", None) or getattr(type_node, "dimensions", None) or []
    )
    arguments = getattr(leaf, "arguments", None)
    if arguments:
        arg_texts = []
        for argument in arguments:
            inner = getattr(argument, "type", None)
            arg_texts.append(type_to_text(inner) if inner is not None else "?")
        return f"{dotted_name}<{', '.join(arg_texts)}>{dimensions}"
    return f"{dotted_name}{dimensions}"


def unwrap_single_argument(type_node):
    """Si ``type_node`` es un generico de un unico argumento de un tipo "contenedor"
    conocido (``List``/``Set``/``Collection``/``Iterable``/``Optional``, calificado o
    no), devuelve ``(True, tipo_interno)``. En caso contrario, ``(False, type_node)``.

    Solo se desenvuelven estos nombres especificos: para genericos con mas de un
    argumento (p. ej. ``Map<String, Object>``) o nombres no reconocidos, no se intenta
    adivinar cual argumento es "el relevante" (ver regla de evidencia, seccion 2 de la
    directriz V0.2) y se devuelve el tipo tal cual.
    """
    if type_node is None:
        return False, type_node
    _, leaf = _walk_reference_chain(type_node)
    name = getattr(leaf, "name", None)
    arguments = getattr(leaf, "arguments", None)
    if name in _COLLECTION_TYPE_NAMES and arguments and len(arguments) == 1:
        inner = getattr(arguments[0], "type", None)
        if inner is not None:
            return True, inner
    return False, type_node


def line_of(node) -> int | None:
    """Extrae el numero de linea de un nodo de ``javalang``, cuando esta disponible."""
    position = getattr(node, "position", None)
    return position.line if position else None
