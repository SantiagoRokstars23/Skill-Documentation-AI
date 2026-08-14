---
name: spring-doc
description: Teach any LLM how to analyze Java/Spring Boot source code directly and produce accurate, evidence-based API documentation (endpoints, parameters, request/response models, security). Use when asked to document, describe, or explain the HTTP API of a Spring Boot microservice from its source code. Works standalone from just the project's source — requires no particular tool, agent, or LLM provider.
---

# Documenting a Java/Spring Boot microservice's API

This skill teaches how to read Java/Spring Boot source code and produce API documentation that is
accurate to what the code actually does — not what it probably does. It is written for **any**
LLM, used by **any** agent or directly, with **no** required tooling: given only this file and a
Spring Boot project's source code, you should be able to carry out a professional documentation
pass on that service's HTTP API.

This is a knowledge/process skill, not a tool manual. It does not depend on, require, or describe
any particular software project, library, or command-line tool.

## Core principles

1. **Evidence over assumption.** Every statement in the documentation must be traceable to
   something actually present in the source code — an annotation, a type, a literal value, a
   control-flow path. If you cannot point to the code that justifies a claim, do not make it.
2. **Never invent.** Do not invent endpoints, parameters, request/response models, HTTP status
   codes, security schemes, or behavior that the code does not support. This applies even when a
   guess would be "usually correct" for a typical Spring Boot service — a plausible default is
   still an invention if the code doesn't say so.
3. **Preserve uncertainty; do not silently resolve it.** When something cannot be determined
   reliably (an ambiguous type name, a mapping without a resolvable HTTP method, a response type
   that depends on runtime logic), say so explicitly in the output — e.g. "status code not
   specified in code" — rather than picking a plausible value and presenting it as fact.
4. **Distinguish fact from inference.** If you do reasonably infer something not stated
   explicitly (e.g., a field named `email` with an `@Email`-style annotation is almost certainly
   an email address), it is acceptable to include that as documentation prose, but it should read
   as description of the field's evident purpose, not as an invented constraint or behavior that
   isn't actually enforced in code.
5. **Consistency.** Given equivalent evidence, document it the same way every time — same
   structure, same handling of optional vs. required, same treatment of missing information —
   regardless of which endpoint or which service you're looking at.

## What to look for in the source code

Work directly from the `.java` source files. For each class that looks like an HTTP controller
(commonly annotated `@RestController` or `@Controller`, but also recognize a class that has
Spring MVC mapping annotations on its methods even if the class-level annotation is unusual or
inherited), extract:

**Class-level context**
- Any base path from a class-level `@RequestMapping`.
- Class-level security annotations (e.g. `@PreAuthorize`, `@Secured`) that apply to every method
  unless overridden.
- Class-level `consumes`/`produces` defaults.

**Per endpoint (per HTTP-mapped method)**
- HTTP method and path: from `@GetMapping`/`@PostMapping`/`@PutMapping`/`@DeleteMapping`/
  `@PatchMapping`, or from `@RequestMapping(method = ...)`. If a mapping has no method you can
  resolve with confidence (e.g. `@RequestMapping` with several methods, or none specified),
  **do not guess one** — record it as an endpoint with an unresolved/ambiguous method instead of
  silently picking the most likely one.
- Parameters and their source: `@PathVariable` (path), `@RequestParam` (query — check `required`
  and `defaultValue`; a parameter with a `defaultValue` is effectively optional even if
  `required` isn't set explicitly), `@RequestHeader` (header), `@RequestBody` (request body,
  usually a DTO type).
- For each parameter: name, declared type, whether it is required, and any validation annotations
  on it directly (e.g. `@NotNull`, `@Min`/`@Max`, `@Pattern`).
- Return type and how it maps to a response: unwrap `ResponseEntity<T>` to find the real body
  type `T`; detect collections (`List<T>`, `Set<T>`, arrays); look for `@ResponseStatus` for an
  explicit status code. **If no status code is determinable from the code, say so — do not
  default to 200/OK as if it were evidence.**
- `consumes`/`produces` at the method level (falls back to class-level values, then to "not
  specified" — never to an assumed default like `application/json` presented as fact; you may
  note it as a common convention, but label it as a convention, not as evidence).
- Method-level security annotations, in addition to (or overriding) class-level ones.

**Request/response models (DTOs)**
- For each type referenced as a request body or response body, resolve its fields: name,
  declared type, whether it's a collection, whether it references another model (nested object),
  and any Bean Validation-style annotations present (`@NotNull`, `@NotBlank`, `@NotEmpty`,
  `@Size`, `@Min`, `@Max`, `@Email`, `@Pattern`, `@Positive`, etc. — record whichever are
  actually present; do not assume validation that isn't annotated).
  - This applies to enums (record their constants) and to nested models (resolve them the same
    way, recursively — but track ambiguity: if a type name matches more than one class in the
    project and you can't tell which one is meant, say so instead of picking one).
- If a DTO type cannot be found anywhere in the provided source (e.g., it comes from an external
  dependency you don't have visibility into), document that its structure is unknown rather than
  guessing its shape from its name.

## Handling ambiguity and missing evidence

Whenever you hit one of these situations, make it visible in the documentation instead of
resolving it silently:

- A mapping without a resolvable HTTP method.
- A DTO type name that matches more than one class definition, with no way to tell which is
  meant.
- A response whose status code, body type, or both cannot be determined from the code.
- Security annotations present but with no way to know the concrete authentication/authorization
  scheme they map to (a role name in `@PreAuthorize` is not enough to construct a full security
  scheme — document it as "endpoint requires authorization: `<expression found>`", not as a
  concrete OAuth2/API-key scheme you invented).
- A parameter or field whose type cannot be resolved to something concrete (e.g. a generic type
  parameter, or a type from code you don't have access to).

A short, explicit note ("not specified in code", "ambiguous: could be X or Y", "type not
resolvable from available source") is always preferable to silence or to a confident-sounding
guess.

## Recommended process

1. **Discover controllers.** Find classes with Spring MVC mapping annotations (class-level or
   method-level).
2. **Enumerate endpoints.** For each controller, walk its methods and extract every HTTP-mapped
   method as one endpoint, per "What to look for" above.
3. **Resolve models.** For every type referenced as a request or response body, locate its
   definition in the project and extract its shape (recursing into nested types, tracking cycles
   so you don't loop forever on self-referential models).
4. **Cross-check consistency.** If the same model or the same base path is used by multiple
   endpoints, document it consistently across all of them.
5. **Write the documentation**, structured per endpoint (see below), explicitly flagging every
   gap found in steps 1–3 instead of smoothing them over.
6. **Review your own output against the source once more** before presenting it: for every claim,
   confirm you can point to the specific annotation, type, or literal that supports it.

## Suggested output structure (adapt as needed)

A useful shape per endpoint — not a mandated format, just a solid default:

```
### METHOD /path

Summary: <one line, in your own words, based on what the endpoint evidently does>

Parameters:
  - name (source: path|query|header, type, required/optional, constraints if any)

Request body: <type name and shape, or "none">

Responses:
  - <status code if known, otherwise "not specified in code">: <body type/shape, or "none">

Security: <annotation/expression found, or "none found">

Notes: <anything ambiguous or unresolved about this endpoint>
```

A project-level summary (list of controllers, base paths, total endpoint count, and a rollup of
anything flagged as ambiguous/unresolved) is a useful addition on top of the per-endpoint detail.

## Common mistakes to avoid

- Assuming `200 OK` / `application/json` because "that's what Spring Boot usually does" — only
  document a status code or media type you can point to in the code (or explicitly label it as an
  assumed convention, never as fact).
- Picking one meaning for an ambiguous DTO name instead of flagging the ambiguity.
- Describing a security scheme (OAuth2 flow, API key location, etc.) that the code does not
  actually specify, just because *some* security annotation is present.
- Treating an inherited/overridden mapping you can't fully trace as if it were absent, instead of
  noting that inheritance made it unresolvable.
- Silently dropping an endpoint you couldn't fully resolve instead of listing it with its gaps
  noted.

## Relationship to tooling

This skill is deliberately tool-, agent-, and LLM-provider-agnostic. It describes a way of
reading code and reasoning about it, not an API of any particular program. You can follow it by
reading source files yourself, with no other tooling at all.

If your environment happens to provide a deterministic static-analysis tool for Spring Boot
projects (for example, this repository also contains one, called `spring-doc`, exposed as a
command-line tool), you may use it to pre-extract structural facts (endpoints, parameters, DTO
shapes) and treat that output as additional evidence to ground your reading of the code — but
using it is entirely optional, never a requirement of this skill, and this skill does not depend
on its internal design, its command syntax, or its output format in any way. Everything this
skill asks you to do can be done by reading `.java` source files directly.
