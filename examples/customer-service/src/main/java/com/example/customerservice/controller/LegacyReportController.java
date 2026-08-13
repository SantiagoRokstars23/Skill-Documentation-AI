package com.example.customerservice.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

// Archivo incluido deliberadamente con un metodo malformado (parentesis sin cerrar)
// para demostrar el motor de fallback de V0.2: el motor AST (javalang) no puede
// parsear este archivo completo, por lo que analyze_project recurre al motor de V0.1
// (regex + balanceo de brackets), que recupera el endpoint valido y omite el metodo
// malformado sin interrumpir el analisis del resto del proyecto. Ver docs/07-Analisis.md.
@RestController
public class LegacyReportController {

    @GetMapping("/reports/summary")
    public ResponseEntity<String> summary() {
        return ResponseEntity.ok("summary");
    }

    public String malformed(String unterminated {
        return "unreachable";
    }
}
