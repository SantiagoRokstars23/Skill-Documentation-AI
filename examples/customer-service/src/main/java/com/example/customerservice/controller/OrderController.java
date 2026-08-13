package com.example.customerservice.controller;

import com.example.customerservice.dto.OrderResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class OrderController {

    @RequestMapping(value = "/orders/{orderId}", method = RequestMethod.GET)
    public ResponseEntity<OrderResponse> getOrder(@PathVariable String orderId) {
        return ResponseEntity.ok(null);
    }

    // Mapping sin metodo HTTP explicito: el Analyzer debe omitirlo y emitir un
    // warning en vez de asumir un metodo (ver docs/07-Analisis.md).
    @RequestMapping("/orders/{orderId}/summary")
    public ResponseEntity<String> getOrderSummary(@PathVariable String orderId) {
        return ResponseEntity.ok("summary");
    }
}
