---
name: archify
description: Skill opcional para enriquecer la arquitectura, arqueología y flujos con diagramas interactivos validados en HTML/SVG autónomo.
version: 1
requiere: []
---

# Archify — Diagramación Arquitectónica e Interactiva

Skill opcional de enriquecimiento visual para Planifier. Úsala cuando se requiera **visualizar interactivamente** la arquitectura del sistema, dependencias entre microservicios, secuencias de llamadas API, tuberías de datos o máquinas de estado.

A diferencia de diagramas estáticos en imagen o Mermaid básico, Archify compila a **HTML autocontenido con SVG vectorial**, temas claro/oscuro, trazabilidad de caminos (*reach* y *route*) y búsqueda integrada, sin dependencias de servidores externos.

## Cuándo usar Archify en Planifier

1. **En Arqueología de Código (`/arqueologia` y Fichas `CA-###`):**
   Para mapear repositorios brownfield y generar la topología visual real entre servicios, enlazando nodos a archivos y líneas de código.
2. **En Maduración Dialéctica (`/madurar` y deliberación de `IDEA-###`):**
   Para explorar y consensuar visualmente flujos o arquitecturas complejas antes de sellar el `ADR-###`.
3. **En Especificaciones Complejas (`SPEC-###`):**
   Para ilustrar secuencias de llamadas multi-servicio o flujos de datos que asistan al trabajador (runner) durante la implementación.

## Los 5 Arquetipos Semánticos

| Tipo | Cuándo elegirlo | Artefactos Planifier relacionados |
|---|---|---|
| `architecture` | Componentes, microservicios, límites de red, repositorios y persistencia. | Fichas `CA-###`, topología del workspace. |
| `workflow` | Tuberías de procesos paso a paso, compuertas de aprobación, pipelines CI/CD. | Flujos de proceso, guías operativas. |
| `sequence` | Ciclos de petición/respuesta API, mensajes asíncronos y eventos entre servicios. | Contratos de integración en `SPEC-###`. |
| `dataflow` | Tuberías ETL/ELT, transformaciones, ingestión y linaje de datos. | Esquemas `ENT-###` y modelos de Datier. |
| `lifecycle` | Máquinas de estados finitos (FSM), transiciones de entidad y reintentos. | Ciclos de vida en `ENT-###` y `FLW-###`. |

## Protocolo de Código Real (Repository-Backed)

Al diagramar un repositorio o microservicio existente, **la fuente de verdad es el código comiteado**:

1. **Fijar identidad:** Registrar el commit (`git rev-parse HEAD`) y la URL del repositorio remoto.
2. **Cero fuga de credenciales:** Eliminar cualquier usuario, token o contraseña en URLs de git antes de volcarlas al diagrama.
3. **Mapear con evidencia:** Cada nodo o conexión debe referenciar rutas de archivo relativas (`file:///path...` o ruta relativa) y rangos de líneas observables donde ocurre la llamada o importación.
4. **Sin invenciones:** Si una llamada a base de datos no es observable en el código, no se asume.

## Flujo de Generación y Compilación

1. **Crear carpeta de artefacto:** En `.archify/<tipo>-<slug>-<timestamp>/`.
2. **Escribir candidato tipado:** Generar el archivo `candidate.json` cumpliendo con el esquema del tipo seleccionado.
3. **Compilar y validar:** Ejecutar la compuerta de validación con Node.js:
   ```bash
   node bin/archify.mjs finalize <type> candidate.json output.html --quality showcase --json
   ```
   *(Si se referencia un repositorio real, añadir `--repo-root <ruta>`)*.
4. **Resultado:** El archivo `output.html` generado es completamente autónomo y puede abrirse en cualquier navegador moderno o incrustarse como artefacto.
