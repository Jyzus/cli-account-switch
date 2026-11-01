---
description: Fase de decisión — convertir las ideas refinadas en ADR, debatiéndolos antes de cerrarlos
argument-hint: [la decisión a tomar, o vacío para partir de las ideas refinadas]
---

Adopta tú el papel de **`guardian-adr`**: lee `.claude/agents/guardian-adr.md` y sigue su
procedimiento **conmigo, en esta conversación**.

**No lo lances como subagente.** Su límite duro es que no decide por mí: presenta opciones con
sus costes y espera mi elección. Un subagente se lanza, trabaja solo y vuelve con la decisión ya
tomada — que es justo lo que este agente tiene prohibido hacer.

Decisión a tomar: $ARGUMENTS

## Punto de partida

Si no te dije ninguna, parte de las ideas que están en `refinada`:

```bash
planifier indexar --salida /tmp/vistas/     # «Índice — Ideas» trae ID, estado y de qué trata
planifier pack IDEA-00N                     # el contenido de una idea concreta
```

Las que estén en `propuesta_futura` **no se tocan**: están fuera de este ciclo por decisión mía,
y sacar un ADR de una de ellas es meter alcance por la puerta de atrás.

## Antes de escribir nada

Enséñame qué decisiones ves y **en qué orden las tomarías**, con un motivo. No es lo mismo el
orden en que aparecieron las ideas que el orden en que conviene decidir: hay decisiones que
condicionan a otras, y tomarlas al revés obliga a rehacer.

Y aplica el filtro de tu definición: si no puedes articular las fuerzas en tensión, ahí no hay
decisión que tomar — hay una `IDEA` que refinar. Dímelo y devuélvela a `/madurar`, no rellenes un
ADR para que quede algo escrito.

## Un ADR nace en `borrador`, y eso es lo que permite discutirlo

La regla de que un ADR jamás se edita protege una decisión **acordada**. Un borrador no lo es
todavía, y por eso los estados existen:

| Estado | Qué significa | ¿Se puede editar? |
|---|---|---|
| `borrador` | Escrito, no acordado. Estamos discutiéndolo | **Sí**, cuantas veces haga falta |
| `aprobado` | Lo acordamos. Vigente | **No.** A partir de aquí, cambiar de opinión es un ADR nuevo |
| `implementado` | Existe en código | No |

Escribe el ADR y déjalo en `borrador`:

```bash
planifier andamio "<asunto o decisión a tomar>" --tipo ADR --depende-de IDEA-00N --aplicar
planifier redactar ADR-0NN --desde borrador.md --estado borrador --aplicar
```

Formula el **asunto a decidir** (ej. `Framework backend`, `Almacén de sesiones`), **nunca la opción preliminar** (no `Usar NestJS`): si en la discusión gana otra opción, no habrá que renombrar el documento, bastará con marcar la ganadora en el cuadro.

**`--depende-de` no es opcional**: sin él la orden se rechaza, y con razón. Un ADR que no declara
la `IDEA` de la que sale (o el ADR aprobado del que deriva) queda desconectado de la cadena y, como no tiene ningún hash que
comparar, **nunca recibirá un aviso de drift**: si esa idea cambia, nadie te lo dirá. Si el ADR deriva de otro ADR (micro-decisión nacida de su `## Queda por resolver`), **el ADR padre debe estar `aprobado`** (`ADR_PADRE_NO_APROBADO`) y la jerarquía no puede superar 2 niveles. Además el
ADR se apoya en ese enlace para poder ser corto — el porqué completo vive en el origen, y quien lea
llega por ahí.

Si el ADR nace de dos ideas, sepáralas por coma. Y si descubres que se te escapó uno sin origen
—`planifier validar` lo reporta como `SIN_ORIGEN`—, se arregla sin reescribir el cuerpo:

```bash
planifier depende ADR-0NN --de IDEA-00N --aplicar
```

`andamio` cuelga el documento solo de la página «Decisiones de arquitectura», creándola si hace
falta.

Usa `plantillas/adr.md` entera, y **corta el contexto en dos frases**: el porqué está en las
`IDEA` de las que cuelga el ADR, y yo puedo abrirlas igual que tú. El cuadro de **opciones y sus
consecuencias** no es relleno: es lo que me permite discutir contigo sin reconstruir por mi cuenta
lo que ya descartaste.

## Mientras esté en borrador

Te voy a pedir que traigas un ADR para debatirlo, que cambies el argumento, o que cambies la
decisión entera. Todo eso es una redacción más:

```bash
planifier redactar ADR-0NN --desde borrador.md --aplicar
```

Si al discutirlo cambia la opción elegida, **reescribe también las opciones consideradas**: el
ADR tiene que explicar por qué ganó la que ganó, no quedarse con el razonamiento de la anterior.

Cuando yo te diga que lo damos por bueno, y sólo entonces:

```bash
planifier estado ADR-0NN aprobado --aplicar
planifier ack ADR-0NN --nota "decisión acordada; IDEA-00N sigue siendo su origen"
```

Ese `ack` es el que cierra el sello contra la `IDEA`, que nació abierto a propósito: el ADR se
escribió después de leerla, y sellarlo antes de que su texto fuera real habría sido un hash
caduco desde el primer minuto.

**No uses `redactar` para aprobar.** El texto no cambia al aprobar: lo único que cambia es que
pasó a estar acordado. Reenviar el cuerpo abriría la puerta a que un `borrador.md` local ya
desviado del documento vivo pisara lo que la wiki tenía, y encima con la orden que dice
«aprobado» — nadie lo revisaría. `estado` sustituye el bloque de metadatos y deja el resto del
documento byte a byte.

Aprobar **no cambia el hash** del ADR: el hash se calcula sin el bloque de metadatos, así que no
hay que ir sellando nada aguas abajo. El `ack` de arriba es otra cosa — cierra los sellos que
este ADR tiene *hacia* la IDEA de la que cuelga.

## Después de `aprobado`

Se acabó editar. Si más adelante la decisión deja de servir, procedes como dice tu definición:
`ADR` nuevo, el viejo retirado, y `planifier drift` para reportarme qué quedó aguas abajo. No lo
arregles tú.

```bash
planifier andamio "<la decisión nueva>" --tipo ADR --sustituye-a ADR-00N --aplicar
#   nace en borrador y hereda el origen de ADR-00N; se redacta, se discute, se acuerda
planifier estado ADR-0NN aprobado --aplicar
planifier sustituir ADR-00N --por ADR-0NN --aplicar
```

Los dos momentos son dos a propósito: **ADR-00N sigue vigente mientras el sustituto se discute**,
porque una decisión no se retira hasta que hay otra acordada en su sitio. El último comando marca
el viejo, escribe el enlace en los dos sentidos y repunta a los dependientes dejando su sello
abierto — que es la lista de lo que hay que releer, no la de lo que ya está resuelto.

Y lo que **no** vas a hacer: devolver un ADR aprobado a `borrador` para retocarlo. La CLI lo
rechaza y hace bien; existe `--forzar` sólo para deshacer un estado que se avanzó por error, no
para reabrir un acuerdo. Si crees que hace falta, la respuesta es un ADR nuevo.

## Al cerrar cada ADR

La idea que lo originó pasa a `promovida` — ya dio lugar a algo:

```bash
planifier estado IDEA-00N promovida --aplicar
planifier validar
```

Los índices de «Decisiones de arquitectura» y de «Ideas» se refrescan solos: `estado` republica
la página hogar del tipo que tocó, porque el estado *es* una de sus columnas. **No escribas tú
esa tabla**: se deriva de los documentos, y un índice a mano es el primero que miente.

## Si alguna no la entiendo

Preséntamela igualmente, pero en **consecuencias**: qué cuesta, qué tarda, qué pasa si se cae, qué
se vuelve difícil después. Si tras eso sigo sin verlo, te la delego — y te la delego **ésa**, no
todas. No hay un modo «decide tú»: hay decisiones concretas que te paso, en voz alta, una a una.

Cuando te delegue una:

1. Decides, y escribes en el ADR una sección `## Al delegar` con **qué asumiste** y **qué no se
   entendió**. Lo segundo es lo que más me sirve: dice dónde falló la traducción, no dónde fallé yo.
2. La cierras marcándolo, en la misma orden que la aprueba:

   ```bash
   planifier estado ADR-0NN aprobado --decidido-por modelo --aplicar
   ```

Sin la bandera consta que decidí yo, que es lo normal. La CLI rechaza delegar sin la sección, y el
validador reporta `DELEGACION_SIN_CONSTANCIA` si aparece a mano.

## Cómo termina el turno

Con un recuento de tres columnas: qué ADR quedaron **aprobados**, cuáles siguen en **borrador** y
qué falta para cerrarlos, y qué decisiones detectaste pero no tomamos.

**Y cuántas delegué**: «de 6 decisiones, 4 delegadas». Delegar es más cómodo que entender, así que
va a tender a ser el botón de «siguiente»; no lo prohíbo, pero quiero verlo. Si van saliendo casi
todas, dímelo en voz alta — probablemente el problema esté en cómo se están traduciendo, no en mí.

Los ADR `aprobado` son los que autorizan el trabajo posterior. El método único no exige RF, RNF ni US intermedios. No uses perfiles legacy para eludir una decisión pendiente: dime cuáles están listos y espera el acuerdo previsto por este flujo.

## Lo que NO haces en este turno

- **No escribes `ENT` ni `SPEC`.** Aunque la decisión ya deje clara la entidad. Ese es otro turno
  y otro agente.
- **No apruebas un ADR por tu cuenta.** El estado `aprobado` lo pongo yo, en voz alta.
- **No tocas un ADR que ya esté `aprobado`.** Ese es tu límite duro y es el que sostiene el
  mecanismo de drift entero.
