# 11 — Integracion

> Ninguna integracion externa esta implementada en V0.1. Este documento describe la unica
> integracion futura contemplada actualmente: Confluence.

## Integracion con Confluence (futura, V0.7)

El flujo de integracion conceptual es:

```text
Skill-Documentation-AI
        |
     OpenAPI
        |
Proyecto Python existente
        |
     Confluence
```

Skill-Documentation-AI produce una especificacion OpenAPI (fases futuras, ver
`docs/05-OpenAPI.md`). Esa especificacion sera consumida por un **proyecto Python existente**
(fuera de este repositorio) que ya conoce como publicar contenido en Confluence. Este proyecto no
se modifica como parte de Skill-Documentation-AI: la integracion se limita a producir una salida
OpenAPI compatible con lo que ese proyecto espera consumir.

## Fuera de alcance en V0.1

Explicitamente, V0.1 **no** implementa:

- Conexion con la API de Confluence.
- Modificacion del proyecto Python existente.
- Publicacion automatica de documentacion.

Esta integracion queda reservada para V0.7 (ver `docs/12-Roadmap.md`), una vez existan el
OpenAPI Generator (V0.3) y el Validator/Auditor (V0.4).

## Otras integraciones futuras

No se contemplan otras integraciones externas en el roadmap actual mas alla de Confluence. Nuevas
integraciones deberan documentarse aqui antes de implementarse (regla global 7).
