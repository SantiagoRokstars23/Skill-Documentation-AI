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
poder tener providers concretos en el futuro:

- `providers/config.py` — `ProviderConfig` (seleccion de provider, modelo, credencial), leible
  desde variables de entorno (`SPRING_DOC_LLM_PROVIDER`/`_MODEL`/`_API_KEY`) o construible de
  forma explicita. La credencial nunca aparece en su representacion por defecto.
- `providers/errors.py` — jerarquia de excepciones propia (`LLMProviderError` y subclases), para
  que ningun consumidor necesite conocer excepciones de un SDK concreto.
- `providers/registry.py` — `get_provider(config)`, seleccion de la implementacion por nombre.
- `providers/fake.py` — `FakeProvider`, unica implementacion concreta en V0.6: determinista, sin
  red, pensada para tests. **No hay ningun provider comercial real implementado todavia** (Claude,
  Gemini, OpenAI...); ver `docs/12-Roadmap.md` y `docs/13-Versionado.md` para el detalle y la
  justificacion de esa decision.

Ningun componente existente (Analyzer, Generator, Validator, CLI) depende de `providers/`; esta
infraestructura puede existir sin alterar el flujo actual (`analyze`/`generate`/`validate`).

## Proveedores potenciales (fases futuras)

- Claude (Anthropic)
- Gemini (Google)
- OpenAI
- Otros proveedores compatibles con una interfaz de generacion de texto por prompt
- Modelos locales (evaluacion futura, ver `docs/10-Seguridad.md`)

Ninguno de estos proveedores tiene una implementacion concreta en V0.1.

## Diferencia entre herramienta de desarrollo y dependencia del producto

Durante el desarrollo de este proyecto, Claude se utiliza como **herramienta de ingenieria**
(para escribir codigo, documentacion, tests, etc., ver `prompts/`). Esto es independiente de la
arquitectura del **producto**: el producto final no debe requerir Claude para funcionar
conceptualmente. La Skill (`docs/04-Skill.md`) y la interfaz `LLMProvider` estan diseñadas para
que cualquier LLM compatible pueda sustituir a Claude sin cambios en la logica central.
