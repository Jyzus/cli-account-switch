---
name: arqueologia
description: Fase de ingeniería inversa y documentación progresiva de repositorios brownfield existentes en JavaScript/TypeScript, Python o Go
argument-hint: [ruta o directorio del repositorio, por defecto '.']
---

Adopta tú el papel de **`arqueologo-codigo`**: lee `.claude/agents/arqueologo-codigo.md` (o las instrucciones de este comando/skill) y sigue su procedimiento **conmigo, en esta conversación**.

**No lo lances como subagente.** La arqueología de código requiere un diálogo interactivo con el usuario: confirmar qué carpetas y módulos son prioritarios, validar nombres de entidades y acordar las decisiones de arquitectura antes de registrarlas en Planifier Docs.

Ruta o directorio a inspeccionar: $ARGUMENTS

## Punto de partida

1. Si se especificó una ruta o directorio:
   ```bash
   planifier arqueologia "$ARGUMENTS"
   ```
2. Si no se indicó argumento o está vacío:
   ```bash
   planifier arqueologia .
   ```

## Lo primero que me devuelves

Un resumen ejecutivo de la topografía del repositorio:
* **Stack tecnológico detectado**: Lenguajes, versiones y dependencias principales (enfocado en JS/TS, Python o Go).
* **Estructura y capas**: Cómo están organizadas las carpetas (controladores, servicios, modelos, etc.).
* **Inventario de rutas y endpoints**: Mapeo preliminar de la API.
* **Modelos de datos**: Entidades detectadas en schemas ORM o structs.

Espera mi confirmación sobre si el alcance detectado es correcto o si hay subcarpetas o módulos excluidos.

## Después: Plan de aterrizaje en Planifier Docs

Presenta la propuesta de documentación en el orden metodológico de Planifier:

1. **ADR (Decisiones de arquitectura)**:
   - Stack principal de backend y frontend.
   - Persistencia, ORM y base de datos.
   - Arquitectura de capas.
2. **MOD / ENT (Dominio y datos)**:
   - Módulos transversales (`MOD-001`, `MOD-002`...).
   - Entidades principales (`ENT-001`, `ENT-002`...).
3. **CA / SPEC (Capacidades y contratos)**:
   - Capacidades de negocio que agrupan los endpoints encontrados.
   - Especificaciones técnicas para endpoints clave.

## Creación asistida de documentos

Una vez acordada la lista de documentos, créalos progresivamente utilizando los comandos oficiales de la CLI:
* `planifier andamio "<título>" --tipo <TIPO> --aplicar`
* `planifier redactar <ID> --desde borrador.md --aplicar`
* `planifier depende <ID> <ORIGEN> --aplicar`
* `planifier ack <ID>`
