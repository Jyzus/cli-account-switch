---
description: Escribir en la wiki las ideas ya maduradas, una IDEA por idea atómica
argument-hint: [título de la idea, o vacío para todas las que estén listas]
---

Escribe en la wiki las ideas que ya salieron de la maduración. Sigues siendo `refinador-ideas`:
si no has hecho `/madurar` en esta conversación, léelo antes — este comando **no** es un atajo
para saltarse esa fase.

Idea(s) a promover: $ARGUMENTS

Si no te dije ninguna, promueve las que quedaron marcadas como listas y **deja fuera las que
seguían bloqueadas por una pregunta**, diciéndome cuáles y por qué.

## Las tres carpetas, y no confundirlas

Toda idea madurada acaba en uno de estos tres estados. Pregúntame por cada una si no está claro:

- **`refinada`** — entra en este ciclo. Es la que promueves y se escribe con el flujo de abajo.
- **`propuesta_futura`** — madura y aceptada, pero fuera de este ciclo. **Se escribe igual**: nace
  su documento con `--estado propuesta_futura`. Queda registrada y visible, y no entra en
  validación, drift, índices ni Plane, así que no infla el alcance del MVP.
- **`descartada`** — decidimos que no, con su motivo, en «Descartado explícitamente».

«No es de este ciclo» no es «no». Descartar una idea buena para no ensuciar la lista la pierde, y
dejarla en `refinada` «por si acaso» infla el MVP sin que nadie lo haya decidido.

Una idea **ya escrita** se mueve de carpeta sin volver a redactarla: el texto de la idea no
cambia porque decidamos que es de otro ciclo.

```bash
planifier estado IDEA-00N propuesta_futura --aplicar
```

La excepción es `descartada`: ahí sí hay texto nuevo —el motivo, en «Descartado explícitamente»—,
así que son dos pasos, `redactar` para el motivo y `estado` para la carpeta. Descartar sin motivo
escrito es exactamente lo que hace que la volvamos a discutir en tres semanas.

## Antes de escribir

Una idea sólo se promueve si se sabe a quién le duele, qué se espera y qué queda fuera, y lo que
queda abierto es técnico y no de intención. Si alguna no llega, dilo y no la escribas: volver a
preguntar cuesta un minuto, un documento con un hueco tapado cuesta una reescritura.

Enséñame la lista de las que vas a escribir y espera mi visto bueno.

## Cómo se escribe

Una `IDEA-###` por idea atómica. Por cada idea, dos órdenes en este orden:

```bash
planifier andamio "<título de la idea>" --tipo IDEA --aplicar
planifier redactar IDEA-0NN --desde borrador.md --aplicar
```

`andamio` la cuelga sola de la página «Ideas», que a su vez cuelga de la lluvia: dentro de tres
meses se sigue viendo de dónde salió cada una, y además están todas juntas con su índice delante.

`andamio` crea el esqueleto ya relleno con la plantilla —sus secciones son las que rellenas—.
`redactar` escribe el cuerpo y no te deja tocar los metadatos: ni el ID, ni los `depende_de`, ni
sus sellos. Tú propones texto, la herramienta decide si entra.

Escribe el borrador en un archivo temporal, no en el repositorio.

## Los dos campos que todo el mundo omite

- **Origen** — de dónde salió. Si la propusiste tú y yo la acepté, tiene que poder leerse dentro
  de tres meses.
- **Descartado explícitamente** — lo que decidimos dejar fuera, con su motivo. Ahí van también tus
  propuestas rechazadas. Es lo que evita rediscutir lo mismo en tres semanas.

## Al terminar

```bash
planifier validar
```

Repórtame qué IDEAs nacieron, cuáles quedaron fuera y por qué, y qué preguntas siguen abiertas.

Las dependencias nacen **sin sellar** a propósito: un esqueleto se rellena justo después, así que
un hash calculado al crearlo nacería caduco. `planifier drift` las lista y `planifier ack` las
cierra cuando el contenido ya es real — no antes.

La lluvia de ideas **no se toca**: es la bandeja de entrada del proyecto y no se borra nunca.
