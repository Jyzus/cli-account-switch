---
name: react-base
description: Convención de la casa para arquitectura frontend en React — erradicación de páginas monolíticas, modularidad por features, separación de presentación y lógica con hooks, y componentes pequeños con responsabilidad única.
version: 1
requiere: [ux-ui]
---

# React Base — Arquitectura y Estructura de Componentes

Cómo se construyen aplicaciones React **aquí**. No es React genérico de tutorial: es la arquitectura modular de la casa, la que erradica las páginas monolíticas gigantes generadas por IAs y garantiza escalabilidad, mantenibilidad y facilidad de prueba.

Esta convención es el **valor por defecto**. Si un `ADR` del pack dice otra cosa, **gana el ADR** — y si eso pasa, dilo: significa que la convención se quedó vieja o que este proyecto es una excepción que nadie escribió.

---

## 1. La Regla Anti-Monolito (Erradicación del Archivo Único)

El error más común de los agentes de IA es meter toda una pantalla (estado, llamadas API, modales, formularios, tablas, tarjetas, filtros) en un único archivo de 500 u 800 líneas.

**EN ESTA CASA ESO ESTÁ TERMINANTEMENTE PROHIBIDO:**

1. **La Vista / Página es solo un Orquestador Liviano:**
   - Un archivo de vista (`<Feature>View.tsx` o `page.tsx`) **nunca debe superar 150–200 líneas**.
   - Su única responsabilidad es invocar los hooks de negocio y ensamblar los subcomponentes visuales.
   - Prohibido definir componentes internos gigantes o escribir llamadas a API directamente dentro del archivo de la página.
2. **Principio de Responsabilidad Única (SRP):**
   - Si un bloque visual tiene más de 40 líneas o maneja su propio estado interactivo (un modal, una barra de filtros, una tarjeta de elemento, un header con acciones), **se extrae a su propio archivo de componente**.

---

## 2. Arquitectura de Carpetas Orientada a Features (`features/<nombre>/`)

Todo módulo o capacidad se organiza en su propia carpeta autocontenida:

```
src/features/<nombre-feature>/
├── components/
│   ├── <Feature>View.tsx          # Vista orquestadora liviana (<150 líneas)
│   ├── <Feature>Header.tsx        # Título, metadatos, breadcrumbs y botón primario CTA
│   ├── <Feature>FilterBar.tsx     # Barra de búsqueda, tabs de filtro y ordenamiento
│   ├── <Feature>Grid.tsx          # Contenedor de lista o grid responsivo
│   ├── <Feature>Card.tsx          # Ficha individual (con hover, badges, botones de acción)
│   ├── <Feature>DetailModal.tsx   # Modal o Drawer de inspección profunda / edición
│   └── <Feature>EmptyState.tsx    # Estado vacío ilustrado cuando no hay resultados
├── hooks/
│   ├── use<Feature>.ts            # Custom hook con llamadas a React Query (query, mutations)
│   └── use<Feature>Filters.ts     # Custom hook para filtros, orden y sincronización con URL
├── services/
│   └── <feature>.service.ts       # Cliente HTTP y funciones tipadas de comunicación
├── types.ts                       # Interfaces y tipos específicos del dominio de la feature
└── __tests__/
    └── <Feature>View.test.tsx     # Tests de integración y renderizado del módulo
```

---

## 3. Separación de Lógica y Presentación

1. **La Lógica de Red y Estado vive en Custom Hooks:**
   - Las vistas y componentes de presentación no contienen llamadas directas a `fetch` ni efectos asíncronos complejos (`useEffect` con llamadas de red).
   - Se utiliza **TanStack React Query** (`useQuery`, `useMutation`) encapsulado dentro de `hooks/use<Feature>.ts`.
   - Esto permite que los componentes de UI sean puros, testeables y fáciles de mockear en tests unitarios.
2. **Componentes Tontos vs Contenedores Inteligentes:**
   - `<Feature>Card.tsx` y `<Feature>Header.tsx` reciben props y emiten callbacks (`onSelect`, `onDelete`, `onCopy`).
   - No deciden cómo se hace la mutación en la base de datos; la vista o el hook orquestador se encarga de ello.

---

## 4. Reutilización de Primitivas Compartidas (`@/shared/components/`)

No inventes componentes básicos desde cero en cada feature:
- Botones: Reutilizar `@/shared/components/Button` (`variant="primary" | "secondary" | "outline" | "ghost" | "danger"`).
- Tarjetas: Reutilizar `@/shared/components/Card` (`hoverable={true}`).
- Badges: Reutilizar `@/shared/components/Badge` o variantes semánticas tipadas.
- Utilidades de clase: Reutilizar `cn(...)` de `@/shared/lib/utils` (combinación de `clsx` y `tailwind-merge`).

---

## 5. Gestión del Estado

1. **Estado del Servidor (Server State):** Gestionado exclusivamente con TanStack React Query. Evita copiar datos del servidor a estados locales (`useState`) a menos que se esté editando un borrador en un formulario.
2. **Estado en URL (URL State):** Filtros, pestañas activas, parámetros de búsqueda y paginación deben reflejarse en los search params (`useSearchParams`) para que las URLs sean compartibles y respeten el historial del navegador.
3. **Estado Local Efímero:** `useState` confinado estrictamente al subcomponente que lo necesita (ej. un modal abierto/cerrado o un input con debounce).

---

## 6. Lo que en React parece código y en realidad es una decisión

| Parece… | Y en realidad es |
|---|---|
| Escribir 600 líneas en un solo archivo de página | Generar una deuda técnica de modularidad crítica |
| Meter un `fetch` dentro de un `useEffect` | Romper el sistema de cache, reintentos y estados de carga de la app |
| Crear una biblioteca de componentes paralela | Romper la coherencia de diseño del sistema |
| Instalar una librería externa de estado (Redux, Zustand) | Introducir una dependencia de arquitectura no acordada en el pack |
| Silenciar dependencias de hooks con `eslint-disable` | Provocar fugas de memoria o datos desactualizados en producción |

---

## Los comandos no están aquí

Cómo se corre la suite de tests (`vitest`, `jest`) o el compilador de TypeScript (`tsc -b`) de **este** repositorio viene en el pack. Están ahí a propósito: la convención es de la casa y los comandos son del repositorio.
