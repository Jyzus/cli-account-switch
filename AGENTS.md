<!-- planifier:version=2.0.0 -->
# Switch

Esta carpeta es la **raíz de un sistema Planifier**, no un repositorio de código: aquí vive el
plan. La fuente de verdad es **Planifier Docs**; los repositorios cuelgan de aquí cuando
existan.

El método único usa IDEA, ADR, SPEC y apoyo CA, ENT, FLW, GLO. La sesión raíz coordina; los procesos delegados reciben `PLANIFIER_ROLE=trabajador`.

**Antes de trabajar, ejecuta esto una vez y lee la salida:**

```bash
planifier contexto
```

Emite el contrato completo —tipos de documento, referencias entre documentos, esquema de
metadatos, todos los comandos, las reglas duras y dónde está el manual—. Es una sola llamada; no
hace falta nada más para operar.

**No edites la documentación en Docs a mano ni navegues la wiki.** Se pregunta a la CLI:

```bash
planifier repos          # los repositorios del sistema, si ya hay alguno
planifier validar        # reglas vigentes sobre la colección
planifier drift          # qué quedó desfasado tras cambiar una decisión
```

### Vinculación y Sincronización de Workspace (Comando Único)
Para vincular, inicializar o sincronizar el workspace en cualquier servidor o máquina:

```bash
planifier workspace --docs "<slug_o_id>"  # vincula con Docs, verifica repos locales y adapta planeador
planifier workspace                      # a secas: re-sincroniza el workspace actual si ya existe
```

### Orquestador y Store de Agentes
Las instrucciones de la herramienta de la sesión se sincronizan localmente, conservando las de otras herramientas.
La sesión raíz coordina; el trabajador usa el rol explícito `PLANIFIER_ROLE=trabajador` (alias `worker`).
No se infiere el modelo de la sesión ni se fija una herramienta para todo el proyecto.
`planifier planeador <herramienta> --aplicar` conserva compatibilidad como sincronización local.

- **Cero Commits Incompletos:** Durante la ejecución con trabajadores/runners, **nunca** se realiza un commit si hay tests fallando o si el DoD no está satisfecho al 100%. El progreso parcial debe permanecer sin commitear en el árbol de trabajo (`git diff`) para que el siguiente agente pueda retomarlo sin ambigüedad.

### Redacción Técnica de SPECs (Responsabilidad del LLM) y Rol de Datier
- **Frontera Usuario vs LLM:** El usuario valida/aprueba la `IDEA-###` y el `ADR-###`. **El usuario NO escribe Gherkin ni tests**. A partir de la aprobación del ADR e Idea, el LLM (`escritor-specs`) asume la redacción autónoma del `SPEC-###` en Gherkin con criterios deterministas y observables (camino feliz, errores, límites).
- **Dónde entra Datier (CLI `planifier datier` o MCP):** Datier es la fuente de verdad del esquema de datos físico (tablas, columnas, tipos, constraints, DDL).
  - Gestión Centralizada: Configurado y resuelto en Planifier Docs por proyecto. La CLI ('planifier datier') y los agentes operan sin credenciales locales.
  - Si una feature requiere persistencia, el rol `modelador-datos` modela el esquema en Datier y Docs sincroniza `ENT-###` *antes* de que el LLM redacte el SPEC, garantizando que los criterios Gherkin usen campos y tablas reales.

### Maduración de Ideas: `/madurar [link_o_id]`
Para madurar la lluvia de ideas o un volcado en bruto (en Claude Code o Antigravity (AGY)):
1. **Comando:** `/madurar [link_o_id]` (o `planifier leer "<link_o_id>"`). Si no hay argumento, lee "Lluvia de ideas".
2. **Rol:** Adopta `refinador-ideas` en esta conversación. Parafrasea primero para confirmar entendimiento.
3. **Huecos:** Ataca los 5 huecos (¿Quién?, ¿Fallo?, ¿Escala?, ¿Qué NO hace?, ¿Existente?) y contradicciones.
4. **No toques la wiki aún:** Tres listas separadas (ideas atomizadas, preguntas abiertas, tus propuestas).
5. **Escribir en IDEA:** Con el acuerdo del usuario, escribe cada idea con `planifier andamio "<título>" --tipo IDEA --aplicar` y `planifier redactar IDEA-0NN --desde borrador.md --aplicar` (o usando `/promover`).

### Arqueología de Código: `/arqueologia [ruta]`
Para investigar, auditar y documentar progresivamente un repositorio preexistente (brownfield en JS/TS, Python o Go):
1. **Comando:** `/arqueologia [ruta]` (o `planifier arqueologia [ruta]`). Si no hay argumento, inspecciona `.`.
2. **Rol:** Adopta `arqueologo-codigo` en esta conversación.
3. **Escaneo no invasivo:** Detecta stacks (NestJS, Express, React, Next, FastAPI, Django, Gin, GORM, Prisma...), arquitectura de capas, endpoints y modelos de datos.
4. **Validación:** Presenta el inventario al usuario y acuerda los módulos clave y la estrategia.
5. **Aterrizaje en Planifier Docs:** Con el acuerdo del usuario, materializa progresivamente los documentos siguiendo la jerarquía:
   - Decisiones de arquitectura (`ADR-0NN` de stack, base de datos y capas).
   - Módulos (`MOD-0NN`) y Entidades de datos (`ENT-0NN`).
   - Capacidades (`CA-0NN`) y Especificaciones de endpoints (`SPEC-0NN`).

---
> Instrucciones unificadas para agentes (compatible con [AGENTS.md](AGENTS.md) y [CLAUDE.md](CLAUDE.md)).
