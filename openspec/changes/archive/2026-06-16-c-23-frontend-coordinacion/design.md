## Context

C-22 established the feature-based frontend pattern for the `academico/` module. C-23 follows the same architecture, conventions, and shared components to add the `coordinacion/` feature module for COORDINADOR/ADMIN roles. All backend APIs already exist and are deployed. The router uses `createBrowserRouter` with `AuthGuard` + `AppLayout`, and every page is lazy-loaded.

## Goals / Non-Goals

**Goals:**
- Provide full CRUD and workflow UIs for coordinacion features (equipos, avisos, tareas, monitores, encuentros, coloquios, setup cuatrimestre)
- Follow existing patterns from `features/academico/`: TanStack Query hooks, React Hook Form + Zod validation, Axios services, feature-based module structure
- Reuse shared components (Button, Input, Card, Spinner, Alert, Table)
- Every page under 200 LOC, split into hooks/components/services/types
- Route grouping under `/dashboard/coordinacion/*` for consistency

**Non-Goals:**
- No backend changes (all APIs exist)
- No changes to the existing router shell, auth guard, or layout
- No new shared UI components unless absolutely necessary for coordination-specific patterns

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Structure | Feature module `features/coordinacion/` with subdirectories per domain | Same pattern as `features/academico/` — each domain (equipos, avisos, tareas, monitores, encuentros, coloquios, setup) gets its own `{components,hooks,services,types,pages}/` |
| Route base | `/dashboard/coordinacion/*` | Clear namespace; existing `AppLayout` handles sidebar. Monitor routes reuse `/dashboard/monitor` (same as C-22 but with extended permissions) |
| Data fetching | TanStack Query with query factories per domain | Match C-22 pattern — `useQuery` for lists, `useMutation` for writes, stale time of 30s for fresh data |
| Forms | React Hook Form + Zod schemas | Consistent with C-22. Complex forms (setup wizard, aviso, convocatoria) use `zodResolver` |
| Table pattern | Shared table wrapper with sort/filter/export | Complex tables in equipos, avisos, coloquios need sorting, filtering, export; shared `Table` component with configurable columns |
| Permissions | Guard routes by permission string via `requirePermission` | Already established in C-21 AuthGuard; each route declares its required permiso (e.g., `equipos:asignar`, `avisos:publicar`) |
| Setup wizard | Single-page multipart form with step state | FL-03 flow is sequential; React state tracks step, accumulated data, and submission at end. Avoids complex routing within the wizard |
| Date-range | Reusable `DateRangePicker` component | Needed for monitor (F2.9) and filters; build as a shared component wrapping native inputs or a lightweight lib |
| Coloquio metrics | TanStack Query prefetch on page load | Metrics panel is read-only aggregate; fetched with `useQuery` on mount, no websocket needed |

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Monitor general (F2.7) may have large datasets | Paginate server-side; use TanStack Query's `keepPreviousData` to avoid flicker on page changes; add debounced search |
| Setup wizard could lose state on navigation | Manage wizard state in a top-level component; confirm before navigating away with `beforeunload` or route blocker |
| Overlapping routes between C-22 and C-23 (monitores) | C-22 already has `/dashboard/monitor` for PROFESOR; C-23 extends with additional filters (date range) and wider scope. Use permission-based rendering within the same route or child routes |
| Aviso form scope switching (dynamic fields) | Use a controlled form with `watch("alcance")` from React Hook Form to conditionally render selector fields |
