---
name: ux-ui
description: Convención de la casa para diseño frontend, estética sensorial y UX/UI — jerarquía visual, sistema espacial 4px/8px, paleta semántica, micro-interacciones, cinéticas fluidas y erradicación del look genérico de IA.
version: 1
requiere: []
---

# UX/UI — Diseño Frontend y Estética Sensorial

Cómo se diseñan y construyen interfaces de usuario **aquí**. No es CSS genérico: es el estándar visual y sensorial de la casa, el que garantiza que cualquier pantalla parezca concebida por un diseñador de producto senior y erradica el «estilo genérico de IA».

Esta convención es el **valor por defecto**. Si un `ADR` del pack dice otra cosa, **gana el ADR** — y si eso pasa, dilo: significa que la convención se quedó vieja o que este proyecto es una excepción que nadie escribió.

---

## 1. Erradicación del "Look Genérico de IA" (Anti-Patrones Prohibidos)

Los modelos de lenguaje tienden por defecto a generar interfaces clónicas, desproporcionadas y desprovistas de contexto visual:

| Lo que la IA tiende a hacer | Por qué está mal | Qué se hace AQUÍ |
|---|---|---|
| Fondos planos negros o blancos puros sin profundidad | Fatiga visual, aspecto plano y barato | Fondo multicapa (`bg-slate-950` con paneles `bg-slate-900/80` y bordes sutiles `border-slate-800/80` con backdrop blur) |
| Degradados morados o púrpuras genéricos (`from-purple-500 to-indigo-500`) | Es el sello delate de plantillas de IA no refinadas | Colores semánticos funcionales: base neutra Slate/Zinc con toques esmeralda (éxito/activo), cian (info/tokens) o ámbar (advertencia) |
| Tarjetas gigantes centradas que ocupan toda la pantalla en blanco | Desperdicio de viewport y sensación de pantalla vacía | Densidad equilibrada de información, grids adaptativos, layouts divididos (header, filtros, contenido, panel lateral) |
| Pantallas completas metidas en un solo archivo de 800 líneas | Inmantenible, rompe reactividad y reutilización | Componentes pequeños, modulares y desacoplados (<150 líneas) |
| Spinner genérico girando en medio de una pantalla en blanco | Causa layout shift y desorientación | Skeleton loaders que calcan la geometría exacta del contenido final |
| Botones y tarjetas flotantes sin feedback interactivo | La interfaz se siente estática, rígida y muerta | Micro-interacciones cinéticas: hover sutil, active con micro-compresión (`active:scale-[0.98]`) y focus rings accesibles |

---

## 2. Sistema Espacial y Geometría (Rhythm 4px / 8px)

1. **Escala Armónica Obligatoria:** Todo espaciado (`margin`, `padding`, `gap`, dimensiones) se define estrictamente en múltiplos de 4px y 8px:
   - `4px` (`p-1`, `gap-1`), `8px` (`p-2`, `gap-2`), `12px` (`p-3`), `16px` (`p-4`), `24px` (`p-6`), `32px` (`p-8`).
   - Prohibido inventar espaciados aleatorios (`style={{ margin: '13px' }}`).
2. **Resiliencia de Maquetación (Cero Overflow Horizontal):**
   - El viewport horizontal nunca debe desbordarse (`overflow-x: hidden` o contenedores con `min-w-0` y `truncate`).
   - En layouts Flex/Grid con textos largos (nombres de archivo, URLs, hashes, correos), el contenedor padre debe tener `min-w-0` y el texto debe usar `truncate` o `break-all` según corresponda.
3. **Jerarquía Visual de Contenedores:**
   - Nivel 0 (Lienzo / Fondo): `bg-slate-950`
   - Nivel 1 (Sidebar / Header / Paneles): `bg-slate-900/90` con borde `border-slate-800`
   - Nivel 2 (Tarjetas / Filas / Modales): `bg-slate-900/60` o `bg-slate-850` con borde `border-slate-800/80`
   - Nivel 3 (Inputs / Badges / Acciones): `bg-slate-950` o `bg-slate-800/80` con bordes de contraste

---

## 3. Tipografía y Tokens Semánticos

1. **Escala Tipográfica:**
   - **Títulos Principales:** `text-xl` o `text-2xl font-bold tracking-tight text-white`
   - **Títulos de Sección / Modales:** `text-base font-semibold text-slate-100`
   - **Texto del Cuerpo:** `text-sm text-slate-300 leading-relaxed`
   - **Metadatos y Etiquetas:** `text-xs text-slate-400`
   - **Badges, Monospace y Hashes:** `text-[11px] font-mono tracking-wider`
2. **Hashes, UUIDs y Códigos:** Siempre en tipografía monospace (`font-mono`) con fondo diferenciado y botón de copiado de 1 clic con feedback visual.
3. **Contraste y Accesibilidad (WCAG AA):**
   - El texto secundario nunca debe bajar a grises ilegibles (prohibido `text-slate-600` sobre fondos oscuros para texto importante; usar `text-slate-400` como mínimo).

---

## 4. Cinéticas y Micro-interacciones

Una interfaz moderna se siente táctil y viva:
- **Transiciones:** `transition-all duration-150 ease-out` o `transition-colors duration-150`.
- **Efecto Táctil al Clic:** En botones, tarjetas clickeables y tabs interactivos:
  ```css
  active:scale-[0.98] transition-transform duration-100
  ```
- **Foco Accesible por Teclado:**
  ```css
  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950
  ```
- **Feedback de Copiado Inmediato:** Al hacer clic en un botón de copiar, cambiar el icono de `Copy` a `Check` en verde durante 2000ms antes de restaurarlo.

---

## 5. Los 4 Estados Obligatorios de Interfaz

Toda pantalla o componente de datos debe contemplar explícitamente:
1. **Estado Cargando (Loading):** Skeletons que respetan las dimensiones y formas del contenido real (nunca una pantalla vacía con un loader genérico).
2. **Estado Vacío (Empty State):** Cuando una búsqueda, filtro o colección no tiene elementos:
   - Icono contextual elegante dentro de un contenedor suave (`bg-slate-800/50 p-3 rounded-full`).
   - Título claro («No se encontraron elementos»).
   - Mensaje explicativo de una frase («Prueba ajustando los filtros de búsqueda o crea uno nuevo»).
   - Botón de Acción Principal (CTA) para resolver la situación («Crear elemento» o «Limpiar filtros»).
3. **Estado de Error:** Banner informativo con descripción del problema y botón de reintento (`Reintentar`), nunca mensajes de error sin salida para el usuario.
4. **Estado Listo / Datos:** Renderizado pulcro, con soporte para paginación o virtualización si la lista excede 30 elementos.

---

## 6. Lo que en UX/UI parece diseño y en realidad es una decisión

| Parece… | Y en realidad es |
|---|---|
| Añadir una biblioteca de componentes externa (shadcn, MUI, Chakra) | Comprometer al bundle y arquitectura del proyecto |
| Meter una vista entera en una sola página | Decisión destructiva de modularidad que genera deuda técnica masiva |
| Usar un color arbitrario para un estado | Romper el sistema semántico global del software |
| Omitir el estado vacío de una lista | Generar confusión y sensación de fallo en el usuario final |

---

## Los comandos no están aquí

Cómo se ejecuta la suite de tests visuales o el dev server de **este** repositorio viene en el pack. Están ahí a propósito: la convención es de la casa y los comandos son del repositorio.
