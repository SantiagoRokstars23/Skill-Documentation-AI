# Regla: Spring Boot

1. La evidencia que recibe esta Skill proviene de la interpretacion deterministica de anotaciones
   Spring MVC / Spring Boot realizada por el Analyzer (`@RestController`, `@RequestMapping`,
   `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@PatchMapping`,
   `@PathVariable`, `@RequestParam`, `@RequestBody`). Ver
   `skill/references/spring-boot-annotations.md`.
2. Esta Skill no reinterpreta directamente codigo fuente Java: confia en que el Analyzer ya aplico
   las convenciones de Spring Boot correctamente (p. ej. `defaultValue` en `@RequestParam` implica
   parametro opcional).
3. Si la evidencia recibida indica que un mapping fue omitido por ambiguedad (por ejemplo, un
   `@RequestMapping` sin metodo HTTP explicito, ver `docs/07-Analisis.md`), esta Skill no debe
   intentar adivinar el metodo HTTP faltante.
