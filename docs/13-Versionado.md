# 13 — Versionado

## Estrategia de versionado

El proyecto sigue [Semantic Versioning](https://semver.org/lang/es/) (`MAJOR.MINOR.PATCH`), con
una particularidad: durante la fase inicial (`0.x`), cada incremento de `MINOR` corresponde a una
fase completa del roadmap (ver `docs/12-Roadmap.md`), no a cambios menores arbitrarios.

## Significado de major/minor/patch

- **MAJOR (`X.0.0`):** cambios que rompen compatibilidad con la metadata, la Skill, o la interfaz
  de `LLMProvider` establecidas en versiones anteriores. Tambien marca hitos de madurez del
  proyecto (p. ej. V1.0 Production).
- **MINOR (`0.X.0`):** una fase completa del roadmap (p. ej. V0.2 Spring Boot Analyzer). Anade
  funcionalidad de forma retrocompatible con la metadata y estructuras publicas de versiones
  `0.x` anteriores.
- **PATCH (`0.0.X`):** correcciones de bugs o ajustes menores que no anaden funcionalidad ni
  rompen compatibilidad.

## Relacion entre versiones y funcionalidades

Cada version del roadmap tiene una directriz propia (ver `prompts/`) que define exactamente su
alcance (Scope Lock). El numero de version del paquete Python (`pyproject.toml`) debe
corresponder a la version de la directriz completada mas recientemente.

## Compatibilidad

- Mientras el proyecto se mantenga en `0.x`, las estructuras publicas (`Endpoint`, `Parameter`,
  `AnalysisResult`, la interfaz `LLMProvider`) pueden extenderse con nuevos campos opcionales sin
  romper compatibilidad, pero no deben eliminarse ni renombrarse campos existentes sin justificar
  el cambio y documentarlo (regla global 9).
- Un cambio que elimine o modifique el significado de un campo existente de la metadata requiere
  una entrada explicita en `CHANGELOG.md` y, si aplica, un incremento de versionado MAJOR una vez
  el proyecto alcance `1.0.0`.

### V0.1.0 -> V0.2.0

Todos los campos nuevos de `Endpoint`, `Parameter` y `Evidence` (V0.2) tienen valores por defecto:
el codigo que construye estas estructuras posicionalmente/por palabra clave como en V0.1 sigue
funcionando sin cambios (`analyzer/spring_boot_analyzer.py`, el motor de fallback, no se modifico).
`AnalysisResult` gano `controllers` y `diagnostics`; `warnings` se mantiene con el mismo
comportamiento observable.

**Excepcion documentada (Regla 7 de la directriz V0.2):** la forma exacta del diccionario devuelto
por `to_dict()` en `Parameter`/`Endpoint` **si** cambio (se agregaron claves nuevas:
`default_value`, `validations`, `dto` en `Parameter`; `symbol`/`type` en `Evidence`; `java_method`,
`consumes`, `produces`, `response`, `security` en `Endpoint`). Cualquier consumidor que compare el
resultado de `to_dict()` contra un diccionario exacto (en vez de leer claves especificas) vera mas
claves de las que existian en V0.1. Esto es intencional: es precisamente la funcionalidad que V0.2
debia agregar (seccion 5 de `prompts/V0.2-ADVANCED-SPRING-BOOT-ANALYZER.md`). Los dos tests de
V0.1 que hacian esa comparacion exacta (`tests/test_models.py`) se actualizaron para reflejar la
forma completa, sin reducir lo que verifican.

### V0.2.0 -> V0.3.0

**Sin cambios en `analyzer/`.** V0.3 (OpenAPI Generator) no modifico ningun archivo del paquete
`analyzer/`: ni `models.py`, ni `__init__.py`, ni los motores internos. El proceso obligatorio de
la seccion 6 de `prompts/V0.3-OPENAPI-GENERATOR.md` se aplico a cada necesidad de datos de OpenAPI
y en ningun caso se demostro necesaria una ampliacion del modelo del Analyzer (ver
`docs/03-Arquitectura.md`, decision 8). Los 84 tests de V0.2 permanecen sin modificar.

Se agrega el paquete `generators/` con implementacion real (antes placeholder) y una dependencia
de runtime nueva: `PyYAML>=6.0,<7.0` (MIT, usada exclusivamente para serializacion YAML). No se
agrego ninguna libreria de validacion ni especifica de OpenAPI (Scope Lock V0.3).

### V0.3.0 -> V0.4.0

**Sin cambios en `analyzer/` ni en `generators/`.** V0.4 (OpenAPI Quality Validator) no modifico
ningun archivo de ninguno de los dos paquetes. El proceso obligatorio de la seccion 6 de
`prompts/V0.4-OPENAPI-VALIDATOR.md` se aplico a la unica necesidad de datos identificada
(ubicacion del hallazgo dentro del documento OpenAPI) y se resolvio reutilizando
`Evidence.file`/`Evidence.type` por convencion (JSON Pointer RFC 6901), sin ampliar
`analyzer/models.py` (ver `docs/03-Arquitectura.md`, decision 9). Los 149 tests de V0.3
permanecen sin modificar.

Se agrega el paquete `validator/` (nuevo, funcional desde su creacion). Ninguna dependencia de
runtime nueva: se reutiliza `PyYAML` (ya presente desde V0.3). No se agrego ninguna libreria de
validacion OpenAPI externa (Scope Lock V0.4).

**Nota de nomenclatura:** el paquete `validators/` (plural), reservado como placeholder desde
V0.1 para un futuro "Validator", **no** es el paquete que implementa V0.4 — la directriz real
nombro el paquete nuevo `validator/` (singular). `validators/` permanece intacto, sin uso, sin
eliminarse (ver `docs/03-Arquitectura.md`).

### V0.4.0 -> V0.5.0

**Sin cambios en `analyzer/`, `generators/` ni `validator/`.** V0.5 (CLI & Developer Experience)
no modifico ningun archivo de los tres paquetes: solo los importa a traves de sus APIs publicas
(`analyze_project`, `generate`/`to_json`/`to_yaml`, `validate`/`validate_json`/`validate_yaml`).
Los 260 tests previos a V0.5 permanecen sin modificar.

Se agrega el paquete `cli/` (nuevo, funcional desde su creacion): `cli/main.py` (parser
`argparse` y despacho), `cli/commands.py` (orquestacion `analyze`/`generate`/`validate`),
`cli/output.py` (formato humano y `--json`), `cli/errors.py` (`CliUsageError`). Entry point nuevo
`spring-doc` (`[project.scripts]` en `pyproject.toml`, tambien invocable como `python -m cli`).
Ninguna dependencia de runtime nueva: `argparse` es libreria estandar (decision de Fase 2,
priorizando minima dependencia sobre `click`/`typer`).

**Reasignacion de numero de version (autorizada explicitamente):** el roadmap original asignaba
V0.5 a "LLM Providers" y V0.6 a "CLI". La directriz real de V0.5 prioriza la CLI; "LLM Providers"
se reprograma sin numero de version fijo (ver `docs/12-Roadmap.md`).

**Decision de diseno explicita de esta version:** `--format json|yaml` y `--json` no son la misma
opcion. `--format` determina el formato del artefacto OpenAPI (`generate`/`analyze --openapi`);
`--json` determina el formato del reporte de la CLI sobre la operacion (conteos y diagnostics por
severidad), nunca el documento OpenAPI embebido. Cuando `--json` se combina con generacion de
OpenAPI, `--output` es obligatorio (el reporte JSON y el documento no pueden compartir stdout).

48 tests nuevos (260 -> 308) cubriendo parser (help/version/comando desconocido/argumentos invalidos), cada comando, exit
codes, `--strict`/`--quiet`/`--json`, separacion `--format`/`--json`, `--openapi`, escritura a
archivo, integracion real contra `examples/customer-service`, determinismo, portabilidad de rutas
(`pathlib`/`tmp_path`), el limite arquitectonico de la CLI (verificado por grep sobre `cli/*.py`:
sin referencias a `ast_analyzer`, `ast_backend`, `dto_analyzer`, `spring_boot_analyzer`,
`analyzer.scanner`, `openapi_types`, `openapi_schemas`, `openapi_rules` ni `javalang`), y una
regresion encontrada en revision pre-commit (`cli/output.py::_symbol` evaluaba siempre la
codificacion de `sys.stdout` incluso cuando el banner se imprime en `stderr`; corregido para
evaluar la codificacion del stream real de destino).

### V0.5.0 -> V0.6.0

**Sin cambios en `analyzer/`, `generators/`, `validator/`.** V0.6 (LLM Providers & AI Foundation)
no modifico ningun archivo de esos tres paquetes; verificado por grep (ninguno referencia
`providers`) y por tests de aislamiento dedicados (`tests/test_providers_isolation.py`).

**Excepcion puntual en `cli/` (autorizada explicitamente, fuera del alcance original de la
directriz):** la revision pre-commit encontro un bug real preexistente desde V0.5 en
`cli/commands.py::run_validate` — leia el archivo con `path.read_text(encoding="utf-8")` sin
proteger la excepcion, a diferencia de `write_output_file` (que ya capturaba `OSError`); un
archivo no-UTF-8 o sin permisos de lectura producia un error interno no controlado (exit 3) en
vez de un error de uso (exit 2), inconsistente con el resto de la CLI. Corregido para envolver la
lectura en el mismo patron `OSError -> CliUsageError` ya usado en `write_output_file`, mas un test
de regresion. Es la unica linea modificada en `cli/`; no se toco ninguna otra funcionalidad ni
comportamiento existente. `cli/` sigue sin importar `providers` (verificado por grep y por
`tests/test_providers_isolation.py`, que no dependen de este fix puntual).

`providers/base.py` (`LLMProvider`, ver `docs/06-LLM.md`) **tampoco cambio su contrato**
(`generate(self, prompt: str) -> str`, sin cambios desde V0.1); solo se actualizo su docstring.
Se agregan cuatro modulos nuevos dentro de `providers/`:

- `providers/config.py` — `ProviderConfig` (dataclass inmutable: `provider`, `model`, `api_key`),
  con `from_env()` leyendo `SPRING_DOC_LLM_PROVIDER`/`_MODEL`/`_API_KEY`. `api_key` se excluye de
  `repr()`/`str()` (campo `repr=False`) para que nunca aparezca en logs por accidente.
- `providers/errors.py` — jerarquia propia de excepciones (`LLMProviderError` y siete subclases:
  `ProviderNotConfiguredError`, `UnknownProviderError`, `MissingCredentialError`,
  `InvalidModelError`, `ProviderTimeoutError`, `ProviderRequestError`, `InvalidResponseError`),
  para que el resto del proyecto nunca necesite conocer excepciones de un SDK concreto.
- `providers/fake.py` — `FakeProvider`, unica implementacion concreta de `LLMProvider` en V0.6:
  determinista, sin red, sin credenciales. **No se implemento ningun provider comercial real**
  (decision explicita, autorizada tras evaluar en Fase 2 un `AnthropicProvider` via `urllib`
  stdlib sin SDK; se opto por la superficie minima, ver `prompts/V0.6—LLM-PROVIDERS-&-AI-
  FOUNDATION.md` seccion 22: "la calidad de la abstraccion... es mas importante que la cantidad
  de providers implementados").
- `providers/registry.py` — `get_provider(config) -> LLMProvider`, un `dict[str, Callable]` de
  seleccion por nombre (no una clase Factory ni un sistema de plugins — patron minimo justificado
  en Fase 2). Solo `"fake"` esta registrado en V0.6.

**Ninguna dependencia nueva**, runtime ni dev: toda la infraestructura usa exclusivamente la
libreria estandar (`dataclasses`, `os`) mas lo que ya existia (`pytest`).

Se agrega tambien `skills/spring-doc/SKILL.md` (fuera de `providers/`, no es codigo Python):
conocimiento/proceso para documentar el API HTTP de un microservicio Java/Spring Boot leyendo su
codigo fuente directamente (que buscar en controllers/mappings/parametros/DTOs/respuestas/
seguridad, como tratar ambiguedad e informacion faltante, como estructurar el resultado).
**LLM-agnostico, agente-agnostico y motor-agnostico**: no depende de `spring-doc` (la CLI), no la
requiere, y no describe la arquitectura interna de este proyecto (`providers/`, `analyzer/`,
`generators/`, `validator/`, `cli/` no se mencionan). Puede mencionar `spring-doc` una vez, de
forma generica, como herramienta externa opcional, nunca como requisito — pensado para poder
copiarse solo y entregarse a cualquier LLM junto con un proyecto Java/Spring Boot.
**Correccion de alcance durante Fase 3/4:** la primera version implementada documentaba como
invocar la CLI `spring-doc` (comandos, opciones, exit codes, forma del reporte `--json`); a
pedido explicito del responsable del proyecto se reescribio por completo para eliminar esa
dependencia, junto con los tests que la verificaban (ver mas abajo). **Nota de nomenclatura:**
`skills/spring-doc/` (plural, nuevo en V0.6) no debe confundirse con `skill/` (singular, desde
V0.1): este ultimo es el componente conceptual de la arquitectura del producto
(`docs/04-Skill.md`), que asume metadata ya extraida por el Analyzer de este proyecto;
`skills/spring-doc/SKILL.md` asume que el LLM lee el codigo fuente Java directamente, sin ningun
Analyzer de por medio, y no forma parte del pipeline `Analyzer -> Skill -> LLM Provider ->
Generator -> Validator -> Auditor`. Ambos coexisten sin relacion entre si.

39 tests nuevos (308 -> 347): `ProviderConfig` (construccion, `from_env`, inmutabilidad, `api_key`
nunca en `repr`/`str`), jerarquia de errores, `FakeProvider` (determinismo, contrato), registro
(resolucion por nombre, provider desconocido, sin configurar), aislamiento (Analyzer/Generator/
Validator/CLI funcionan sin ninguna variable `SPRING_DOC_LLM_*`, y ninguno de esos paquetes
importa `providers`), validaciones sobre `skills/spring-doc/SKILL.md` (frontmatter valido, no
referencia la arquitectura interna del proyecto ni sintaxis de la CLI, no se dirige a un
agente/proveedor concreto, menciones de `spring-doc` -si las hay- quedan enmarcadas como
opcionales, ensena los principios de evidencia esperados, y es autocontenido), y la regresion de
`cli/commands.py::run_validate` sobre archivos no-UTF-8/no legibles (ver mas arriba).
