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
  on it directly (e.g. `@NotNull`, `@Min`/`@Max`, `@Pattern`) — carry the concrete constraint
  values (the actual min/max, the actual pattern, the actual max length) into the documentation,
  not just the fact that "some validation exists".
- The success response and how it maps from the return type: unwrap `ResponseEntity<T>` to find
  the real body type `T`; detect collections (`List<T>`, `Set<T>`, arrays); look for
  `@ResponseStatus` (or a `ResponseEntity.status(...)` call) for an explicit status code. **If no
  status code is determinable from the code, say so — do not default to 200/OK as if it were
  evidence.**
- Every error response the operation can realistically produce — see "Tracing error responses"
  below. This is not optional detail; an endpoint documented with only its success response is
  incomplete, even if that's all a naive read of the annotations shows.
- `consumes`/`produces` at the method level (falls back to class-level values, then to "not
  specified" — never to an assumed default like `application/json` presented as fact; you may
  note it as a common convention, but label it as a convention, not as evidence).
- Method-level security annotations, in addition to (or overriding) class-level ones — see
  "Security: verify before documenting" below.
- **`tags`** (or the equivalent grouping the framework's mapping annotations expose): if the
  controller/operation doesn't declare one explicitly, use the controller's evident purpose (e.g.
  its class name without the `Controller` suffix) as a reasonable grouping label, and say that it
  was inferred rather than declared. Every endpoint should end up in some named group — an
  undocumented, ungrouped endpoint is much harder for a reader to navigate to.
- **`summary`**: always include one, for every operation, even a trivial one-liner — it's cheap
  and there's no excuse to skip it.
- **`description`**: required when the operation has real logic to explain — a request body,
  parameters beyond simple pagination, validation, or more than the generic fallback error (see
  below). Optional for a genuinely simple read/catalog endpoint (e.g. "list all X" with no
  filtering logic) — forcing a `description` there that just restates the `summary` adds no value.
  When you do write one, describe only what the code actually validates/does (parameters and
  their defaults, what triggers each error, what an empty/not-found case returns if it isn't
  treated as an error) — do not invent behavior.

### Tracing error responses

Do not stop at the success path. For every operation:

1. Look at what the method itself throws (`throw new ...`), and follow calls it makes to
   `private`/`protected` methods in the same class and to injected collaborators (services,
   repositories) that are part of the project's own source — these often contain the actual
   business-error conditions (e.g. "not found", "invalid input", "conflict").
2. Note how each thrown exception type maps to an HTTP status: either directly (a status field or
   annotation on the exception, a `ResponseStatusException`), or indirectly through a centralized/
   global exception handler (commonly `@ControllerAdvice`/`@ExceptionHandler`) that maps exception
   types to statuses. If the project has a generic handler that catches broad exceptions (e.g. any
   uncaught `RuntimeException`) and maps it to a fallback status (typically 500), document that
   fallback once and note that it applies to every operation uniformly — you don't need to
   rediscover it per endpoint.
3. Document one response entry per distinct status the operation can produce, with a description
   of the condition that causes it. When the code contains a real example message/payload for that
   error (a literal string passed to the exception, a concrete error code constant), use it as the
   example — never fabricate one. If the only evidence is the exception type and a generic message
   template, say so plainly rather than inventing a realistic-looking payload.
4. Distinguish a genuine error from a valid "nothing found" case that the code returns without
   throwing (e.g. an empty list, or an explicit `204 No Content`) — document that as its own
   response entry, not folded into the error list.
5. If, after this tracing, you still find no error path at all for an operation (rare, but
   possible for a trivial pass-through), say so explicitly instead of inventing a plausible 400/404
   — but treat that as worth double-checking, since most real operations backed by a service layer
   do have at least one failure mode.

### Security: verify before documenting

Presence of a security annotation is not the same as an enforced requirement. Before documenting
an endpoint as requiring authentication/authorization:

- Check whether the validating code path is actually active — not commented out, not a no-op, not
  bypassed by a conditional you can see in the code.
- If it is active, document it (name of the header/scheme, and the authorization expression found,
  e.g. a required role) — but do not invent a concrete OAuth2 flow or API-key transport detail the
  code doesn't specify (see "Handling ambiguity and missing evidence" below).
- If a security-looking annotation or header check exists but its validation is disabled or
  clearly not wired up, **do not document it as a requirement** — say explicitly that the
  code declares it but does not currently enforce it. Documenting an unenforced requirement as if
  it were real is worse than not documenting anything: it tells a future caller to send a header
  that accomplishes nothing, or worse, gives a false sense of protection.

**Request/response models (DTOs)**
- For each type referenced as a request body or response body, resolve its fields: name,
  declared type, whether it's a collection, whether it references another model (nested object),
  and any Bean Validation-style annotations present (`@NotNull`, `@NotBlank`, `@NotEmpty`,
  `@Size`, `@Min`, `@Max`, `@Email`, `@Pattern`, `@Positive`, etc. — record whichever are
  actually present, with their concrete values; do not assume validation that isn't annotated).
  - This applies to enums (record their constants) and to nested models (resolve them the same
    way, recursively — but track ambiguity: if a type name matches more than one class in the
    project and you can't tell which one is meant, say so instead of picking one).
- **Give every field a description, on both request and response models.** It is common for
  request fields to already carry some documentation (a Javadoc comment, an existing description
  annotation) while response fields are left bare — do not let that asymmetry carry over into your
  output. If nothing in the code documents a field's purpose, write a short description from its
  name/type/validations and mark it as inferred rather than sourced from an explicit comment or
  annotation; do not simply omit the field's description.
- **Give every field a realistic example value** when you can produce one confidently from its
  type/validations/name (e.g. a `String identification` with `@Size(min=11,max=11)` and a
  Bean Validation numeric-only pattern → an 11-digit numeric string). If you cannot produce one
  responsibly, leave it out rather than inventing an implausible value — a missing example is
  honest; a wrong-looking one is misleading.
- **Fields that represent a "catalog code"** (a status/type/category-like field whose value comes
  from a fixed or external set, not free text) need special care — figure out which of two cases
  applies before documenting it:
  - **Fixed set, defined in code** (a Java `enum`, or a small fixed array/constant list checked
    directly in the code): document the concrete allowed values directly (as an enum/allowed-values
    list) — you have full evidence for them.
  - **Set that lives outside the code** (comes from a database table, a lookup service, an external
    catalog endpoint): do **not** hardcode the values you happen to see in an example or test data
    — a hardcoded list here goes stale the moment the underlying catalog changes without anyone
    updating the documentation. Instead, describe in prose where the current valid set can be
    looked up (the query/repository/endpoint the code uses to fetch it, if you can identify it).
  - Ask yourself: "if a new valid value is added to the underlying source, would a hardcoded list
    here silently become wrong?" — if yes, it's the second case.
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
  concrete OAuth2/API-key scheme you invented). See "Security: verify before documenting" above.
- A parameter or field whose type cannot be resolved to something concrete (e.g. a generic type
  parameter, or a type from code you don't have access to).
- A "catalog code" field (see above) where you can't tell, from the available source, whether its
  values come from a fixed set or an external one — say that explicitly rather than guessing which
  case applies.

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

Tags: <group(s), declared or inferred>

Summary: <one line, in your own words, based on what the endpoint evidently does>

Description: <longer explanation, only if the operation has real logic to explain>

Parameters:
  - name (source: path|query|header, type, required/optional, constraints, description, example)

Request body: <type name, or "none">
  - field (type, required/optional, constraints, description, example)
  - ... (recurse into nested/collection fields the same way)

Responses:
  - <success status>: <body type/shape, with the same per-field detail as above, or "none">
  - <error status>: <description of the condition, plus a real example if the code provides one>
  - ... (one entry per distinct status the code can actually produce, per "Tracing error
    responses" above — never only the success response)

Security: <requirement found and confirmed active, or "none found", or "declared in code but not
currently enforced" — see "Security: verify before documenting" above>

Notes: <anything ambiguous or unresolved about this endpoint>
```

A project-level summary (list of controllers, base paths, total endpoint count, and a rollup of
anything flagged as ambiguous/unresolved) is a useful addition on top of the per-endpoint detail.
If the project defines real per-environment base URLs somewhere (application config files, a
`@OpenAPIDefinition(servers = ...)`-style declaration, deployment manifests), include them at this
project level — a set of endpoint paths is far more useful to an outside reader alongside the
actual host(s) they live on than with only `localhost` or no host information at all.

## Common mistakes to avoid

- Assuming `200 OK` / `application/json` because "that's what Spring Boot usually does" — only
  document a status code or media type you can point to in the code (or explicitly label it as an
  assumed convention, never as fact).
- **Documenting only the success response.** This is the single most common gap: an endpoint whose
  code clearly throws business exceptions but whose documentation only lists "200" is incomplete
  documentation, not a simple endpoint — go back and trace the error paths (see "Tracing error
  responses" above).
- Leaving response-model fields undocumented while request-model fields are described — document
  both sides with the same rigor.
- Hardcoding the current values of a catalog field that actually comes from an external/dynamic
  source (a database table, a lookup service) — document where to look it up instead.
- Picking one meaning for an ambiguous DTO name instead of flagging the ambiguity.
- Describing a security scheme (OAuth2 flow, API key location, etc.) that the code does not
  actually specify, just because *some* security annotation is present — and documenting a
  security requirement as active when the code shows its validation is disabled/bypassed.
- Skipping `tags`/grouping, or leaving `summary` empty — both are cheap and expected on every
  operation.
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
