---
name: madurar
description: Fase de maduración — convertir la lluvia de ideas o un documento de ideas en ideas atómicas con refinador-ideas, sin escribir nada todavía
argument-hint: [link o ID del documento en Planifier Docs, o vacío para 'Lluvia de ideas']
---

Adopta tú el papel de **`refinador-ideas`**: lee `.claude/agents/refinador-ideas.md` (o las instrucciones de este comando/skill si estás en otra herramienta) y sigue su procedimiento **conmigo, en esta conversación**.

**No lo lances como subagente.** Su procedimiento es una conversación de ida y vuelta —parafrasear y esperar confirmación, preguntar por los huecos y esperar respuesta— y un subagente se lanza, trabaja solo y devuelve un informe. Aquí el trabajo *es* la conversación.

Documento o link a madurar: $ARGUMENTS

## Punto de partida

Si se proporcionó un link, ID o título como argumento:
```bash
planifier leer "$ARGUMENTS"
```

Si no se indicó ningún argumento (o está vacío):
```bash
planifier leer "Lluvia de ideas"
```

Es el único documento que traes entero, y sólo una vez. Si te dicto las ideas aquí directamente en el chat, ése es el punto de partida y no hace falta leer nada.

## Lo primero que me devuelves

Lo que entendiste, con tus palabras, antes de estructurar nada. Es la validación más barata que existe: si entendiste mal, todo lo que venga después está mal. Espera mi confirmación.

## Después

Ataca los 5 huecos de planificación, que es tu aportación principal:
1. **Quién** — un rol o actor concreto («el usuario» no es un actor).
2. **Qué pasa cuando falla** — casi siempre sin responder y donde está el trabajo real.
3. **Cuántos y con qué frecuencia** — la escala cambia las decisiones por completo.
4. **Qué NO hace** — cerrar el alcance vale más que ampliarlo.
5. **Qué existe ya** — puede que el problema esté resuelto en otro sitio.

Señala las contradicciones entre ideas: ahora cuestan una conversación, en desarrollo cuestan una semana.

Puedes proponer lo que veas que falta para el MVP, **en una lista aparte y marcado como tuyo**, cada propuesta con su porqué. La respuesta por defecto a una propuesta tuya es *descartada con motivo*.

## Lo que NO haces en este turno

**No escribes ni un documento todavía.** Ni `andamio`, ni `redactar`, ni nada que toque la colección de documentos.

Convertir cada viñeta de la lluvia en un `IDEA-###` sería transcribir, no madurar: saldrían documentos con formato oficial y los mismos huecos que ya tenían. Un hueco marcado vale más que un hueco tapado — el tapado se descubre implementando.

Tampoco elijas tecnologías ni las sugieras de pasada. En cuanto nombras una tecnología, la conversación deja de ser sobre el problema.

## Cómo termina la conversación

Con **tres listas separadas** y la wiki intacta:

1. Las ideas que traje yo, atomizadas — una idea por entrada; si al describirla necesitas «además», son dos.
2. Las preguntas sin responder (los huecos abiertos).
3. Tus propuestas, con su porqué.

Y me dices cuáles están listas para promover y cuáles siguen bloqueadas por una pregunta. Una idea está lista cuando alguien podría tomar una decisión a partir de ella: se sabe a quién le duele, qué se espera y qué queda fuera, y lo que queda abierto es técnico, no de intención.

## Cómo se escriben las ideas consensuadas

Cuando contestemos las preguntas y te dé el visto bueno, escribe cada idea atómica aprobada usando:
```bash
planifier andamio "<título de la idea>" --tipo IDEA --aplicar
planifier redactar IDEA-0NN --desde borrador.md --aplicar
```
O ejecuta `/promover`.
