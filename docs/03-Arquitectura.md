# 03 — Arquitectura

## Vision general

La arquitectura es conceptual y por capas: cada componente tiene una responsabilidad unica y se
comunica con el siguiente mediante estructuras de datos bien definidas, no mediante acoplamiento
directo de implementacion.

```text
Skill-Documentation-AI
|
+-- Analyzer
|
+-- Skill
|
+-- LLM Provider
|
+-- OpenAPI Generator
|
+-- Validator
|
+-- Auditor
|
+-- CLI
|
+-- Integraciones futuras
```

Relacion conceptual entre componentes:

```text
                    Skill-Documentation-AI
                             |
              +--------------+--------------+
              |                             |
           Analyzer                       Skill
              |                             |
              +--------------+--------------+
                             v
                       LLM Provider
                             |
               +-------------+-------------+
               v             v             v
            Claude        Gemini        OpenAI
               |             |             |
               +-------------+-------------+
                             v
                    OpenAPI Generator
                             v
                         Validator
                             v
                          Auditor
                             v
                      OpenAPI YAML/JSON
```

**Importante:** esta arquitectura es conceptual para todo el proyecto. V0.1 implementa
unicamente el **Analyzer** de forma funcional y deja el resto de componentes delimitados y
documentados, pero no implementados (ver estado por componente mas abajo).

## Componentes

### Analyzer (implementado en V0.1)

- **Responsabilidad:** analizar codigo fuente Java/Spring Boot y producir evidencia y metadata
  estructurada sobre la API (controllers, endpoints, metodos HTTP, parametros).
- **Entrada:** ruta a un proyecto Java/Spring Boot.
- **Salida:** estructuras `Endpoint` / `Parameter` serializables (ver `docs/07-Analisis.md`).
- **Dependencias:** ninguna hacia otros componentes del sistema. Es la base del pipeline.
- Detalle en `docs/07-Analisis.md`.

### Skill (estructura definida en V0.1)

- **Responsabilidad:** encapsular el conocimiento sobre como documentar APIs correctamente:
  reglas, principios, formato OpenAPI, manejo de incertidumbre.
- **Entrada:** evidencia/metadata producida por el Analyzer.
- **Salida:** instrucciones/comportamiento esperado para el LLM Provider.
- **Dependencias:** consume la salida del Analyzer; no depende de ningun LLM concreto.
- Detalle en `docs/04-Skill.md`.

### LLM Provider (interfaz definida en V0.1)

- **Responsabilidad:** exponer una interfaz uniforme para invocar un LLM, independientemente del
  proveedor concreto (Claude, Gemini, OpenAI, u otros compatibles).
- **Entrada:** prompt/contexto construido a partir de la Skill y la evidencia.
- **Salida:** contenido generado por el LLM (texto/estructura, interpretado por el Generator).
- **Dependencias:** ninguna dependencia arquitectonica de componentes superiores hacia un
  proveedor especifico. Ver `docs/06-LLM.md`.
- **Estado en V0.1:** solo la interfaz conceptual (`providers/base.py`). Sin implementaciones
  concretas (fuera de alcance, ver Scope Lock).

### OpenAPI Generator (no implementado en V0.1)

- **Responsabilidad futura:** transformar la salida del LLM Provider (guiada por la Skill) en una
  especificacion OpenAPI valida.
- Reservado para V0.3. Ver `docs/05-OpenAPI.md`.

### Validator (no implementado en V0.1)

- **Responsabilidad futura:** validar la especificacion OpenAPI generada (estructural y
  semanticamente) y clasificar hallazgos en errores/warnings/info.
- Reservado para V0.4. Ver `docs/08-Validacion.md`.
- V0.1 crea unicamente el paquete `validators/` como placeholder documentado.

### Auditor (no implementado en V0.1)

- **Responsabilidad futura:** evaluar trazabilidad, evidencia y confianza (confidence) de la
  documentacion generada.
- Reservado para V0.4. Ver `docs/09-Auditoria.md`.

### CLI (no implementado en V0.1)

- **Responsabilidad futura:** exponer el pipeline completo como herramienta de linea de comandos.
- Reservado para V0.6. En V0.1 el Analyzer se utiliza directamente como libreria Python (ver
  `README.md`).

### Integraciones futuras (no implementadas en V0.1)

- Integracion con Confluence y con el proyecto Python existente. Reservado para V0.7. Ver
  `docs/11-Integracion.md`.

## Flujo de informacion (V0.1)

```text
Codigo fuente Java/Spring Boot
        |
        v
   analyzer.scanner        (descubre archivos .java)
        |
        v
analyzer.spring_boot_analyzer  (extrae Endpoint/Parameter)
        |
        v
   analyzer.models.AnalysisResult   (metadata estructurada, serializable)
```

El resultado del Analyzer es la unica salida funcional de V0.1 y esta disenado para ser consumido
por el futuro OpenAPI Generator sin necesidad de romper compatibilidad (ver `docs/07-Analisis.md`
y `docs/13-Versionado.md`).

## Limites entre componentes

- El Analyzer **no** conoce la Skill, el LLM Provider, ni OpenAPI. Solo produce metadata.
- La Skill **no** depende de un LLM concreto ni contiene instrucciones exclusivas de Claude.
- El LLM Provider es una interfaz; ningun componente superior debe importar un SDK de un
  proveedor especifico directamente.
- `validators/` y `generators/` existen como paquetes reservados, sin logica de negocio en V0.1.

## Decisiones arquitectonicas relevantes

1. **Analisis deterministico basado en expresiones regulares y conteo de balance de
   brackets/parentesis**, en lugar de un parser Java completo (p. ej. via un compilador o una
   libreria de terceros de parseo AST). Justificacion: evita una dependencia adicional pesada
   para V0.1, es suficiente para detectar anotaciones Spring MVC de forma fiable, y mantiene el
   principio de minimizar dependencias (regla global 2). Limitacion conocida documentada en
   `docs/07-Analisis.md`; una libreria de parseo formal podria evaluarse en una version futura si
   la complejidad del codigo real lo justifica.
2. **Sin CLI en V0.1**: el Analyzer se consume como libreria Python. Evita adelantar el roadmap
   (V0.6 CLI) y mantiene el alcance minimo necesario para validar el Analyzer con tests y con el
   ejemplo incluido.
3. **`providers/` solo define la interfaz** (clase base abstracta), sin implementaciones
   concretas, para evitar acoplamiento a un LLM especifico y cumplir el Scope Lock.
4. **`validators/` y `generators/` se crean vacios/placeholder** porque la estructura de proyecto
   (seccion 8 de la directriz) los requiere, pero su logica pertenece a V0.3/V0.4.
