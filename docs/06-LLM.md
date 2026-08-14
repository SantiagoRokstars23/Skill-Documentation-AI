# 06 — LLM Provider

## Concepto de LLM Provider

Un **LLM Provider** es una abstraccion que expone una interfaz uniforme para invocar un modelo de
lenguaje, independientemente del proveedor concreto que lo implemente (Claude, Gemini, OpenAI, u
otro proveedor compatible, incluyendo futuros modelos locales).

## Desacoplamiento

El sistema **no** debe acoplarse arquitectonicamente a ningun LLM especifico. Ningun componente
por encima del LLM Provider (Skill, Generator, Validator, Auditor, CLI) debe importar o depender
directamente de un SDK de un proveedor concreto. Toda interaccion con un LLM pasa por la interfaz
definida en `providers/base.py`.

Esto permite que el proyecto evolucione para soportar distintos proveedores sin modificar la
logica central (Analyzer, Skill, Generator, Validator, Auditor).

## Responsabilidades del LLM Provider

- Recibir un prompt/contexto ya construido (a partir de la Skill y la evidencia del Analyzer).
- Invocar el modelo de lenguaje subyacente.
- Devolver el contenido generado en un formato consistente, independiente del proveedor.
- Encapsular detalles especificos del proveedor (autenticacion, formato de API, limites) fuera
  del resto del sistema.

## Interfaz conceptual (V0.1)

V0.1 define unicamente la interfaz abstracta, sin implementaciones concretas:

```python
class LLMProvider(ABC):
    def generate(self, prompt: str) -> str:
        """Invoca el modelo subyacente y devuelve el contenido generado."""
```

Ver `providers/base.py` para la definicion real. Cualquier implementacion concreta (Claude,
Gemini, OpenAI, etc.) debera heredar de esta interfaz.

## Infraestructura de providers (V0.6)

V0.6 agrega, alrededor de la interfaz de arriba (sin modificarla), la infraestructura minima para
poder tener providers concretos:

- `providers/config.py` — `ProviderConfig` (seleccion de provider, modelo, credencial, timeout
  desde V0.7), leible desde variables de entorno (`SPRING_DOC_LLM_PROVIDER`/`_MODEL`/`_API_KEY`/
  `_TIMEOUT`) o construible de forma explicita. La credencial nunca aparece en su representacion
  por defecto.
- `providers/errors.py` — jerarquia de excepciones propia (`LLMProviderError` y subclases), para
  que ningun consumidor necesite conocer excepciones de un SDK concreto ni de `urllib`.
- `providers/registry.py` — `get_provider(config)`, seleccion de la implementacion por nombre
  (`"fake"` → `FakeProvider`, `"anthropic"` → `AnthropicProvider` desde V0.7).
- `providers/fake.py` — `FakeProvider`: determinista, sin red, pensada para tests.

Ningun componente existente (Analyzer, Generator, Validator, CLI, Skill) depende de `providers/`;
esta infraestructura puede existir sin alterar el flujo actual (`analyze`/`generate`/`validate`),
y sin ninguna variable `SPRING_DOC_LLM_*` configurada.

## Provider real: Anthropic (V0.7)

`providers/anthropic.py::AnthropicProvider` es el primer (y, a la fecha, unico) provider LLM
comercial real del proyecto. Implementa `LLMProvider.generate(prompt: str) -> str` exactamente
igual que `FakeProvider`, contra el endpoint de Mensajes de Anthropic
(`POST https://api.anthropic.com/v1/messages`), unicamente con `urllib.request`/`urllib.error`/
`json` de la libreria estandar — **sin el SDK `anthropic`**, sin ninguna dependencia nueva.

**Configuracion** (via `ProviderConfig`, construccion explicita o `ProviderConfig.from_env()`):

| Variable de entorno | Campo | Obligatorio | Notas |
|---|---|---|---|
| `SPRING_DOC_LLM_PROVIDER` | `provider` | si (`"anthropic"`) | selecciona el provider en `get_provider()` |
| `SPRING_DOC_LLM_MODEL` | `model` | si | sin valor por defecto (ver "Limitaciones" abajo) |
| `SPRING_DOC_LLM_API_KEY` | `api_key` | si | nunca se hardcodea, nunca aparece en logs/`repr`/excepciones |
| `SPRING_DOC_LLM_TIMEOUT` | `timeout` | no | segundos; si falta o no es numerico, se usa el default seguro del provider (60s) |

`api_key`/`model` ausentes se detectan en la construccion (`get_provider(...)`), antes de
cualquier llamada de red: `MissingCredentialError`/`InvalidModelError`.

**Seguridad:** la API key solo puede venir de `ProviderConfig` (nunca hardcodeada en el
repositorio); no aparece en `repr()`/`str()` de `ProviderConfig` ni de `AnthropicProvider`, ni en
ningun mensaje de excepcion (verificado por tests dedicados). Los tests del proyecto usan
exclusivamente credenciales ficticias y nunca realizan una llamada de red real.

**Manejo de errores:** ninguna excepcion de `urllib` (`TimeoutError`, `HTTPError`, `URLError`) ni
del formato de respuesta de Anthropic llega al consumidor sin traducir — todo se convierte a
`providers.errors` (`ProviderTimeoutError`, `ProviderRequestError`, `InvalidResponseError`). Ver
`docs/13-Versionado.md` seccion "V0.6.0 -> V0.7.0" para la tabla completa de traduccion.

**Diferencia con `FakeProvider`:** `FakeProvider` es 100% determinista, sin red, sin credenciales,
pensado para tests (siempre devuelve la misma respuesta configurada). `AnthropicProvider` hace una
llamada HTTP real cuando se le proporcionan credenciales validas, con una respuesta que depende
del modelo invocado (no determinista) — por eso los tests de `AnthropicProvider` mockean
`urllib.request.urlopen` en vez de invocar la red real.

**Limitaciones conocidas:**
- Sin modelo por defecto: `AnthropicProvider` exige `model` explicito (decision de diseno, no una
  limitacion tecnica — ver `docs/03-Arquitectura.md` decision 12).
- Solo `prompt -> texto`: sin streaming, tool calling, imagenes, archivos, conversaciones
  multi-turno ni memoria (fuera de alcance de V0.7).
- `max_tokens` fijo (1024) en cada request, no configurable todavia.

**Ausencia de integracion con la CLI:** V0.7 no agrega ningun comando (`spring-doc ai`/`chat`/
`ask`/`document` no existen) ni cambia el comportamiento de `analyze`/`generate`/`validate`.
`AnthropicProvider` existe en `providers/` pero **ningun consumidor real lo usa todavia** — esa
integracion (que capacidad de IA concreta consume el LLM, y como) es responsabilidad de V0.8.

## Proveedores potenciales (fases futuras)

- ~~Claude (Anthropic)~~ — implementado en V0.7 (`AnthropicProvider`), ver arriba.
- Gemini (Google)
- OpenAI
- Otros proveedores compatibles con una interfaz de generacion de texto por prompt
- Modelos locales (evaluacion futura, ver `docs/10-Seguridad.md`)

Ninguno de los proveedores restantes tiene una implementacion concreta todavia.

## Diferencia entre herramienta de desarrollo y dependencia del producto

Durante el desarrollo de este proyecto, Claude se utiliza como **herramienta de ingenieria**
(para escribir codigo, documentacion, tests, etc., ver `prompts/`). Esto es independiente de la
arquitectura del **producto**: el producto final no debe requerir Claude para funcionar
conceptualmente. La Skill (`docs/04-Skill.md`) y la interfaz `LLMProvider` estan diseñadas para
que cualquier LLM compatible pueda sustituir a Claude sin cambios en la logica central.
