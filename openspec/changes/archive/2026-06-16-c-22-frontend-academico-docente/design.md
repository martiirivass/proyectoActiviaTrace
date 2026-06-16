## Context

El backend de activia-trace tiene todas las APIs del módulo académico-docente operativas: calificaciones (importación con preview, confirmación), umbral (CRUD + recalcular), análisis (atrasados, ranking, notas-finales, reportes-rapidos), exportar TPs sin corregir, comunicaciones (preview, envío individual/masivo, tracking por lote, seguimiento por materia), y monitor de seguimiento. El frontend actual (C-21) provee el shell: autenticación, layout con sidebar dinámico, cliente HTTP con refresh transparente, route guards, y componentes UI compartidos.

No existe ninguna página de dominio — el dashboard actual es un placeholder. Este cambio implementa todas las vistas que el rol PROFESOR necesita para operar sus comisiones.

**Stack vigente:** React 18 + TypeScript, Vite, TanStack Query v5, React Hook Form + Zod, Axios, Tailwind CSS v4, React Router v6 (createBrowserRouter).

**Restricciones:**
- No modificar backend.
- Consumir endpoints existentes de C-10 (calificaciones/umbral), C-11 (análisis), C-12 (comunicaciones).
- Seguir la estructura feature-based de C-21: `features/academico/{components,hooks,services,types,pages}`.
- Sin `any`, sin class components, componentes <200 LOC, lazy loading.

## Goals / Non-Goals

**Goals:**
- Dashboard del docente con resumen de comisiones (materias asignadas, métricas por comisión).
- Layout de tabs para navegar las vistas de una comisión: calificaciones, umbral, atrasados, ranking, notas, reportes, comunicaciones.
- Flujo completo de importación de calificaciones: subir archivo → preview con tabla de alumnos × actividades → checkbox de selección → confirmar importación → resumen.
- Configuración de umbral con slider numérico + edición de valores textuales aprobatorios + botón recalcular.
- Tabla de atrasados con filtro de búsqueda, indicación de causa, link a comunicación.
- Ranking de actividades aprobadas: tabla ordenable por posición, filtro por materia.
- Notas finales: tabla con promedio por alumno + desglose expandible de actividades.
- Reportes rápidos: métricas consolidadas + gráfico de barras simple de distribución por actividad.
- Exportar TPs sin corregir: botón de descarga directa (CSV) con indicador de carga.
- Comunicación a atrasados: redacción → preview modal → envío (individual/masivo a seleccionados) → tracking de estados con polling/refetch.
- Monitor de seguimiento (TUTOR/PROFESOR): tabla filtrable por alumno, comisión, regional, actividad, con métricas por alumno.
- Tests de los flujos críticos: import flow, tabla de atrasados, preview de comunicación, tracking de estados.
- Lazy loading de todas las páginas.
- Implementación en español (consistente con C-21).

**Non-Goals:**
- No implementar la lógica de aprobación de comunicaciones (NEXO/COORDINADOR) — eso pertenece a C-23.
- No implementar vistas de COORDINADOR/ADMIN (equipos, avisos, tareas, estructura) — C-23 y C-24.
- No implementar diseño visual final ni branding — mismo approach que C-21 (Tailwind base + tema neutro).
- No implementar notificaciones en tiempo real vía WebSocket — el tracking de comunicaciones usa polling/refetch.
- No implementar i18n.
- No implementar tema oscuro.
- No implementar tests E2E — solo unit + integration con Vitest + RTL + MSW.

## Decisions

### ADR-FE-008: Feature module propio `academico` separado de `auth`

**Decisión**: Crear `features/academico/` como módulo independiente de `features/auth/`.

**Racional**: C-21 estableció feature-based modules. `auth` es transversal (login/2FA/recuperación). `academico` es el primer módulo de dominio. Separarlos mantiene cohesión y evita que un módulo crezca sin límite. Cuando lleguen C-23 y C-24, cada uno tendrá su propio feature module.

### ADR-FE-009: Un solo grupo de rutas `/comision/:materiaId/:cohorteId` con tabs

**Decisión**: Las vistas de una comisión viven bajo una misma ruta paramétrica con un layout de tabs (sub-rutas anidadas). El dashboard del docente y el monitor son rutas independientes.

**Racional**:
- Todas las operaciones del profesor operan sobre una materia+cohorte específicos. Tener una URL compartida permite navegar entre tabs sin perder el contexto de comisión.
- `react-router-dom` Outlet anidado permite que el layout de tabs persista mientras cambia el contenido.
- Cada tab es una ruta hija (`/comision/:materiaId/:cohorteId/calificaciones`, `/umbral`, etc.) — lazy-loaded independientemente.

**Alternativa considerada**: Modal/dialog para cada vista. Rompe la navegabilidad y la capacidad de compartir URLs.

### ADR-FE-010: TanStack Query para todo el fetching — sin estado global adicional

**Decisión**: Todo el fetching de datos (comisiones, calificaciones, atrasados, ranking, comunicaciones, monitor) usa TanStack Query con custom hooks. Sin estado global (Zustand/Redux) para datos de servidor.

**Racional**:
- Los datos del módulo académico son lecturas de servidor con escrituras ocasionales (import, umbral, comunicación).
- TanStack Query maneja caching, refetch, stale-while-revalidate, paginación, loading/error states.
- No se necesita estado global para compartir datos entre tabs — cada hook de query es independiente con su propio cache key.
- Las mutaciones (importar calificaciones, enviar comunicación) usan `useMutation` con invalidación de queries relacionadas.

**Alternativa considerada**: Estado global con Zustand. No se justifica — el fetching sigue siendo server-state. Si se necesita compartir estado UI entre tabs (ej. filtro activo), se usa React state o URL search params.

### ADR-FE-011: Comunicaciones tracking con polling simple (no WebSocket)

**Decisión**: El tracking de estado de comunicaciones usa `refetchInterval` de TanStack Query (polling cada 5s) en lugar de WebSocket.

**Racional**:
- El backend no expone WebSocket para tracking en tiempo real.
- El ciclo de vida de una comunicación es de segundos a minutos (Pendiente → Enviando → Enviado/Error).
- Polling cada 5s es aceptable para este dominio. No hay requisito de latencia sub-second.
- TanStack Query maneja el polling con `refetchInterval` y detiene automáticamente cuando el componente se desmonta o cuando todos los mensajes alcanzan estado terminal (Enviado/Error/Cancelado).

**Alternativa considerada**: WebSocket nativo. Requeriría cambios en backend (C-12). No se justifica para el volumen y latencia requeridos.

### ADR-FE-012: Preview de importación como estado local del paso wizard

**Decisión**: Los datos del preview de importación (archivo parseado, actividades detectadas, selecciones del usuario) se mantienen en estado local del componente wizard, no en TanStack Query ni estado global.

**Racional**:
- El preview es efímero: existe solo durante el flujo de importación.
- No persiste entre navegaciones ni sesiones.
- Los datos son grandes (tabla alumnos × actividades) y no necesitan cache.
- El wizard tiene 3 pasos: Upload → Preview → Confirm. Cada paso transforma o enriquece los datos locales.
- Se usa `useState` + `useReducer` si la lógica es compleja.

**Alternativa considerada**: Cachear en TanStack Query con `staleTime: Infinity`. Los datos del preview no tienen key de query significativa y consumirían memoria innecesaria.

### ADR-FE-013: Formulario de comunicación con React Hook Form + Zod + preview modal

**Decisión**: El formulario de redacción de comunicación usa React Hook Form + Zod para validación, y el preview se muestra en un modal antes del envío.

**Racional**:
- RHF + Zod es el patrón establecido en C-21 para formularios.
- El preview es obligatorio (RN-16). Se implementa como paso intermedio: el usuario completa el formulario → hace clic en "Previsualizar" → se muestra modal con asunto, cuerpo renderizado y cantidad de destinatarios → botón "Enviar" confirma el envío.
- Los destinatarios se seleccionan desde la tabla de atrasados (checkboxes).
- El envío masivo crea un lote; el individual envía a un solo alumno.

### ADR-FE-014: Servicios organizados por dominio backend

**Decisión**: Cada grupo de endpoints backend (calificaciones, umbral, analisis, comunicaciones, monitor) tiene su propio archivo de servicio.

**Racional**:
- `calificacionesService.ts` — preview upload, confirm import
- `umbralService.ts` — get/update umbral, recalcular
- `analisisService.ts` — atrasados, ranking, notas-finales, reportes-rapidos, exportar TPs
- `comunicacionesService.ts` — preview, enviar individual, enviar masivo, tracking por lote, tracking por materia
- `monitorService.ts` — seguimiento con filtros

Cada servicio importa los helpers `get`, `post`, `patch`, `del` de `@/shared/api/api.ts`.

### ADR-FE-015: Tipos compartidos en `features/academico/types/`

**Decisión**: Todos los tipos DTO del módulo académico se definen en `features/academico/types/index.ts` (o archivos separados si crece).

**Racional**:
- Un único lugar de definición de tipos evita duplicación entre servicios y componentes.
- Los tipos reflejan las respuestas del backend (DTOs). No se definen tipos para requests internos de componentes a menos que sean significativamente diferentes.

## Component Tree

```
<App>
  <QueryClientProvider>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </QueryClientProvider>
</App>

Router (createBrowserRouter) — mismo layout que C-21:

├── /login → LoginPage (existente)
├── /2fa → TwoFactorPage (existente)
├── /recuperar → RecoveryPage (existente)
├── /restablecer → ResetPasswordPage (existente)
├── AuthLayout (AppLayout + AuthGuard)  ← NUEVAS RUTAS
│   ├── /dashboard → DocenteDashboardPage  ← NUEVA
│   │   └── <DocenteDashboard>
│   │       ├── ComisionCard (por cada materia asignada)
│   │       └── MetricasResumen
│   ├── /comision/:materiaId/:cohorteId → ComisionLayout  ← NUEVA
│   │   ├── index → redirect to /calificaciones
│   │   ├── calificaciones → CalificacionesPage
│   │   │   └── <ImportWizard>
│   │   │       ├── UploadStep (dropzone + archivo)
│   │   │       ├── PreviewStep (tabla + checkboxes)
│   │   │       └── ConfirmStep (resumen + resultado)
│   │   ├── umbral → UmbralPage
│   │   │   └── <UmbralConfig>
│   │   │       ├── UmbralSlider
│   │   │       └── ValoresTextualesEditor
│   │   ├── atrasados → AtrasadosPage
│   │   │   └── <AtrasadosTable>
│   │   │       ├── FiltroBusqueda
│   │   │       └── FilaAtrasado (causa + link a comunicación)
│   │   ├── ranking → RankingPage
│   │   │   └── <RankingTable> (ordenable)
│   │   ├── notas → NotasFinalesPage
│   │   │   └── <NotasTable>
│   │   │       └── FilaExpandible (actividades detalle)
│   │   ├── reportes → ReportesPage
│   │   │   └── <ReportesView>
│   │   │       ├── MetricasConsolidadas
│   │   │       └── DistribucionActividades (barras)
│   │   └── comunicaciones → ComunicacionesPage
│   │       └── <ComunicacionesView>
│   │           ├── FormularioRedaccion (RHF+Zod)
│   │           ├── PreviewModal
│   │           ├── TrackingTable (polling 5s)
│   │           └── EstadoBadge
│   └── /monitor → MonitorPage  ← NUEVA
│       └── <MonitorView>
│           ├── FiltrosPanel (alumno, comisión, regional, actividad)
│           └── MonitorTable (métricas por alumno)
├── /401 → UnauthorizedPage (existente)
└── * → NotFoundPage (existente)
```

## Data Flow

```
1. Dashboard docente:
   useQuery("comisiones") → GET /api/v1/materias/mis-comisiones (o similar)
     └── renderiza ComisionCard[] con métricas resumidas

2. Importación de calificaciones (wizard 3 pasos):
   Step 1: Upload → POST /api/v1/calificaciones/preview (multipart file)
     └── response: { actividades_detectadas, alumnos, parse_data }
     └── se almacena en estado local (useState)

   Step 2: Preview → usuario selecciona actividades con checkbox
     └── estado local: selectedActividades: string[]

   Step 3: Confirm → POST /api/v1/calificaciones/importar
     └── body: { materia_id, cohorte_id, actividades, parse_data }
     └── response: { registros_creados, resumen }
     └── onSuccess: invalidate queries de calificaciones y análisis

3. Umbral:
   GET /api/v1/umbral?materia_id=... → useQuery("umbral", materiaId)
     └── response: UmbralMateria | null (default 60%)

   PATCH /api/v1/umbral → useMutation
     └── body: { materia_id, umbral_pct, valores_aprobatorios }
     └── onSuccess: invalidateQuery("umbral")

   POST /api/v1/umbral/recalcular → useMutation
     └── body: { materia_id }
     └── onSuccess: toast success, invalidateQuery("umbral")

4. Atrasados:
   GET /api/v1/analisis/atrasados?materia_id=...&busqueda=... → useQuery
     └── response: Atrasado[] (alumno, actividad, causa)
     └── filter params se pasan como query params → refetch on change

5. Ranking:
   GET /api/v1/analisis/ranking?materia_id=... → useQuery
     └── response: RankingEntry[] (posicion, alumno, aprobadas, total, %)

6. Notas Finales:
   GET /api/v1/notas-finales?materia_id=... → useQuery
     └── response: NotaFinalEntry[] (alumno, promedio, actividades[])

7. Reportes Rápidos:
   GET /api/v1/analisis/reportes-rapidos?materia_id=... → useQuery
     └── response: ReporteRapido (alumnos total, actividades, aprobados, %)

8. Exportar TPs:
   GET /api/v1/analisis/exportar-tps?materia_id=... → response: Blob (CSV)
     └── trigger download via Blob + URL.createObjectURL

9. Comunicaciones (redacción → preview → envío → tracking):
   Preview: POST /api/v1/comunicaciones/preview
     └── body: { asunto, cuerpo, materia_id, destinatarios }
     └── response: { preview_html, cantidad_destinatarios }

   Envío masivo: POST /api/v1/comunicaciones/enviar-lote
     └── body: { asunto, cuerpo, materia_id, destinatarios }
     └── response: { lote_id, total_mensajes }

   Tracking: GET /api/v1/comunicaciones/lote/:loteId → useQuery(refetchInterval: 5000)
     └── response: { lote, distribucion: { pendiente, enviando, enviado, error, cancelado } }
     └── polling se detiene cuando pendiente=0 y enviando=0

   Seguimiento por materia: GET /api/v1/comunicaciones/materia/:materiaId → useQuery

10. Monitor de seguimiento:
    GET /api/v1/monitor/seguimiento?filtros... → useQuery
      └── response: MonitorEntry[] (alumno, total, aprobadas, desaprobadas, pendientes, %)
      └── filtros: alumno_id, email, comision, regional, actividad, min_actividades
```

## Route Design

```
Rutas existentes (C-21) — sin cambios:
  /login                → pública
  /2fa                  → pública
  /recuperar            → pública
  /restablecer          → pública
  /401                  → protegida (sin permiso)
  *                     → 404

Nuevas rutas protegidas (C-22):
  /dashboard                      → DocenteDashboardPage    (require: academico:ver)
  /comision/:materiaId/:cohorteId → ComisionLayout
    /calificaciones                → CalificacionesPage     (require: calificaciones:importar)
    /umbral                        → UmbralPage             (require: umbral:configurar)
    /atrasados                     → AtrasadosPage          (require: atrasados:ver)
    /ranking                       → RankingPage            (require: ranking:ver)
    /notas                         → NotasFinalesPage       (require: notas-finales:ver)
    /reportes                      → ReportesPage           (require: reportes:ver)
    /comunicaciones                → ComunicacionesPage     (require: comunicacion:enviar)
  /monitor                        → MonitorPage            (require: monitor:ver)
```

## Directory Structure

```
frontend/src/
├── features/
│   ├── auth/  (existente, sin cambios)
│   └── academico/                              ← NUEVO
│       ├── components/
│       │   ├── DocenteDashboard.tsx
│       │   ├── ComisionCard.tsx
│       │   ├── MetricasResumen.tsx
│       │   ├── ComisionTabs.tsx
│       │   ├── ImportWizard/
│       │   │   ├── UploadStep.tsx
│       │   │   ├── PreviewStep.tsx
│       │   │   ├── ConfirmStep.tsx
│       │   │   └── ImportWizard.tsx
│       │   ├── UmbralConfig.tsx
│       │   ├── UmbralSlider.tsx
│       │   ├── AtrasadosTable.tsx
│       │   ├── FiltroBusqueda.tsx
│       │   ├── RankingTable.tsx
│       │   ├── NotasTable.tsx
│       │   ├── ReportesView.tsx
│       │   ├── MetricasConsolidadas.tsx
│       │   ├── DistribucionActividades.tsx
│       │   ├── ComunicacionesView.tsx
│       │   ├── FormularioRedaccion.tsx
│       │   ├── PreviewModal.tsx
│       │   ├── TrackingTable.tsx
│       │   ├── EstadoBadge.tsx
│       │   ├── FiltrosPanel.tsx
│       │   └── MonitorTable.tsx
│       ├── hooks/
│       │   ├── useComisiones.ts
│       │   ├── useCalificaciones.ts
│       │   ├── useUmbral.ts
│       │   ├── useAtrasados.ts
│       │   ├── useRanking.ts
│       │   ├── useNotasFinales.ts
│       │   ├── useReportes.ts
│       │   ├── useExportarTPs.ts
│       │   ├── useComunicaciones.ts
│       │   └── useMonitor.ts
│       ├── services/
│       │   ├── calificacionesService.ts
│       │   ├── umbralService.ts
│       │   ├── analisisService.ts
│       │   ├── comunicacionesService.ts
│       │   └── monitorService.ts
│       ├── types/
│       │   └── index.ts
│       └── pages/
│           ├── DocenteDashboardPage.tsx
│           ├── ComisionLayoutPage.tsx
│           ├── CalificacionesPage.tsx
│           ├── UmbralPage.tsx
│           ├── AtrasadosPage.tsx
│           ├── RankingPage.tsx
│           ├── NotasFinalesPage.tsx
│           ├── ReportesPage.tsx
│           ├── ComunicacionesPage.tsx
│           └── MonitorPage.tsx
│       └── tests/                              ← Tests integrados
│           ├── ImportWizard.test.tsx
│           ├── AtrasadosTable.test.tsx
│           ├── ComunicacionesView.test.tsx
│           └── TrackingTable.test.tsx
├── shared/  (existente, sin cambios)
│   ├── api/api.ts
│   ├── components/ui/...
│   ├── components/layout/AppLayout.tsx
│   ├── components/guards/...
│   ├── hooks/useAuth.ts
│   └── providers/AuthProvider.tsx
└── router/index.tsx  (MODIFICADO: agregar nuevas rutas)
```

## Risks / Trade-offs

| Riesgo | Mitigación |
|--------|------------|
| **Importación de archivos grandes**: archivos .xlsx con muchos alumnos y actividades pueden ser lentos de parsear | El parsing ocurre server-side (C-10). El frontend solo envía el archivo y recibe el preview parseado. Si el upload es lento, mostrar barra de progreso nativa del navegador. |
| **Polling de tracking**: polling cada 5s puede generar carga innecesaria | El polling se detiene automáticamente cuando el tracking alcanza estado terminal (todas las comunicaciones del lote están en Enviado/Error/Cancelado). Se usa `refetchInterval` condicional de TanStack Query. |
| **Tamaño del bundle**: 10 nuevas páginas lazy-loaded | Cada página es un chunk independiente (Vite code-splitting con React.lazy). Las páginas oscilan entre 30-150 LOC. Los componentes compartidos (tabs, tablas, badges) se cargan sincrónicamente desde `components/`. |
| **Mantenibilidad de servicios**: 5 servicios con lógica repetitiva | Los servicios son capas delgadas que solo llaman a `get/post/patch/del` de `api.ts`. Sin lógica de negocio. Si hay patrones repetitivos, se extraen a un helper en `services/` compartido. |
| **Compatibilidad con permisos**: algunas rutas pueden requerir permisos que el PROFESOR no tiene | Cada ruta declara `require_permission` que el PermissionGuard verifica. Si un profesor no tiene acceso a una vista, se muestra estado "sin permisos" y la ruta no se renderiza. El menú lateral también filtra según permisos del usuario. |
