---
name: nextjs-base
description: Convención de la casa para Next.js con App Router — separación de Server y Client Components, arquitectura modular colocalizada, Server Actions tipados y optimización de renderizado.
version: 1
requiere: [react-base]
---

# Next.js Base — Arquitectura con App Router

Cómo se construyen aplicaciones Next.js **aquí**. Diseñado sobre la base de `react-base`, aprovecha las capacidades nativas del App Router para maximizar la velocidad de carga, optimizar el bundle del cliente y mantener una separación limpia de responsabilidades.

Esta convención es el **valor por defecto**. Si un `ADR` del pack dice otra cosa, **gana el ADR** — y si eso pasa, dilo: significa que la convención se quedó vieja o que este proyecto es una excepción que nadie escribió.

---

## 1. La Frontera Server vs Client Components

La regla fundamental de Next.js es mantener el código en el servidor por defecto y enviar Javascript al navegador únicamente cuando sea indispensable:

1. **Server Components por Defecto:**
   - Todos los layouts, páginas y componentes contenedores son Server Components a menos que requieran explícitamente eventos del DOM (`onClick`, `onChange`), hooks de ciclo de vida (`useState`, `useEffect`) o APIs del navegador (`window`, `localStorage`).
2. **`'use client'` Solo en las Hojas del Árbol:**
   - **PROHIBIDO** colocar `'use client'` al principio de un archivo de página (`page.tsx`) completo. Hacerlo degrada la página a una SPA tradicional y arruina los beneficios de streaming y SSR.
   - Extrae únicamente los elementos interactivos a componentes hoja dedicados (ej. `<SearchInput />`, `<ActionDropdown />`, `<InteractiveModal />`) y márcalos con `'use client'`. Pásales los datos del servidor como props o mediante composición de `children`.

---

## 2. Estructura de Rutas y Colocalización Privada

Organización canónica dentro de `app/`:

```
app/
├── layout.tsx                     # Root layout (fuentes, providers globales, metadatos)
├── (dashboard)/                   # Route group (sin alterar la URL)
│   ├── layout.tsx                 # Shell del dashboard (sidebar, header)
│   └── proyectos/
│       └── [id]/
│           ├── page.tsx           # Server Component orquestador liviano
│           ├── loading.tsx        # Skeleton layout automático durante streaming
│           ├── error.tsx          # Error boundary del segmento ('use client')
│           ├── not-found.tsx      # Vista 404 del segmento
│           └── _components/       # Componentes colocalizados privados de la ruta
│               ├── ProjectHeader.tsx
│               ├── ProjectFilters.tsx ('use client')
│               └── ProjectDetailModal.tsx ('use client')
```

- Las carpetas que inician con guion bajo (`_components/`, `_lib/`, `_actions/`) son privadas y no generan rutas públicas.
- Para features transversales y de gran escala, reutiliza la convención de `features/<nombre>/` definida en `react-base`.

---

## 3. Data Fetching y Server Actions

1. **Data Fetching en Server Components:**
   - Realiza llamadas asíncronas directamente en el cuerpo del Server Component:
     ```tsx
     export default async function ProjectPage({ params }: { params: { id: string } }) {
       const project = await getProjectById(params.id);
       return <ProjectView project={project} />;
     }
     ```
   - No expongas endpoints API intermedios innecesarios si la página puede consultar la capa de datos o servicios directamente en el servidor.
2. **Mutaciones con Server Actions:**
   - Define acciones en archivos dedicados con la directiva `'use server'`.
   - Valida estrictamente todos los argumentos de entrada con esquemas de validación (Zod o Valibot).
   - Usa `revalidatePath(...)` o `revalidateTag(...)` para refrescar el caché del servidor de forma determinista tras una mutación exitosa.

---

## 4. Metadatos y SEO

- Exporta objetos `metadata` estáticos o la función `generateMetadata` en cada `page.tsx` para generar títulos, descripciones y open graph dinámicos basados en la entidad bajo visualización.

---

## 5. Lo que en Next.js parece código y en realidad es una decisión

| Parece… | Y en realidad es |
|---|---|
| Poner `'use client'` al inicio de toda la página | Desactivar Server Components y saturar el bundle de cliente |
| Crear una ruta `app/api/...` para consultar datos que usa la misma página | Agregar latencia HTTP interna y complejidad innecesaria |
| Omitir `loading.tsx` | Perder el streaming instantáneo y dejar la navegación en blanco |
| Modificar el `next.config.js` para añadir plugins pesados | Afectar los tiempos de compilación y empaquetado de todo el equipo |

---

## Los comandos no están aquí

Cómo se corre el build de producción (`next build`) o el servidor de desarrollo (`next dev`) de **este** repositorio viene en el pack. Están ahí a propósito: la convención es de la casa y los comandos son del repositorio.
