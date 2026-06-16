## 1. Feature module scaffolding y types

- [x] 1.1 Create `features/academico/` directory structure: `components/`, `hooks/`, `services/`, `types/`, `pages/`
- [x] 1.2 Create `features/academico/types/index.ts` with all DTOs: Comision, Alumno, Actividad, CalificacionPreview, UmbralMateria, AtrasadoEntry, RankingEntry, NotaFinalEntry, ReporteRapido, Comunicacion, LoteComunicacion, MonitorEntry, filtros de monitor

## 2. Services — Capa de API

- [x] 2.1 Create `calificacionesService.ts`: uploadPreview(file) → POST /calificaciones/preview (multipart), confirmImport(data) → POST /calificaciones/importar
- [x] 2.2 Create `umbralService.ts`: getUmbral(materiaId) → GET /umbral, updateUmbral(data) → PATCH /umbral, recalcular(materiaId) → POST /umbral/recalcular
- [x] 2.3 Create `analisisService.ts`: getAtrasados(materiaId, busqueda?) → GET /analisis/atrasados, getRanking(materiaId) → GET /analisis/ranking, getNotasFinales(materiaId) → GET /notas-finales, getReportes(materiaId) → GET /analisis/reportes-rapidos, exportarTPs(materiaId) → GET /analisis/exportar-tps (blob)
- [x] 2.4 Create `comunicacionesService.ts`: preview(data) → POST /comunicaciones/preview, enviarIndividual(data) → POST /comunicaciones/enviar, enviarLote(data) → POST /comunicaciones/enviar-lote, getTrackingPorLote(loteId) → GET /comunicaciones/lote/:loteId, getTrackingPorMateria(materiaId) → GET /comunicaciones/materia/:materiaId
- [x] 2.5 Create `monitorService.ts`: getSeguimiento(filtros) → GET /monitor/seguimiento with query params (alumno_id, email, comision, regional, actividad, min_actividades)

## 3. Hooks — TanStack Query wrappers

- [x] 3.1 Create `useComisiones.ts`: useQuery("comisiones") → lista de materias asignadas del docente
- [x] 3.2 Create `useCalificaciones.ts`: useMutation for uploadPreview, useMutation for confirmImport; invalidate queries on success
- [x] 3.3 Create `useUmbral.ts`: useQuery("umbral", materiaId), useMutation updateUmbral, useMutation recalcular; invalidate on success
- [x] 3.4 Create `useAtrasados.ts`: useQuery("atrasados", {materiaId, busqueda}) con debounced search param
- [x] 3.5 Create `useRanking.ts`: useQuery("ranking", materiaId)
- [x] 3.6 Create `useNotasFinales.ts`: useQuery("notas-finales", materiaId)
- [x] 3.7 Create `useReportes.ts`: useQuery("reportes", materiaId)
- [x] 3.8 Create `useExportarTPs.ts`: useMutation that triggers CSV download via Blob + URL.createObjectURL
- [x] 3.9 Create `useComunicaciones.ts`: useQuery("comunicaciones-materia", materiaId), useQuery("comunicaciones-lote", loteId, {refetchInterval: conditional 5000}), useMutation for preview, useMutation for enviarIndividual, useMutation for enviarLote
- [x] 3.10 Create `useMonitor.ts`: useQuery("monitor-seguimiento", filtros) with refetch on filter change

## 4. Docente Dashboard

- [x] 4.1 Create `DocenteDashboardPage.tsx`: lazy-loaded page, renders DocenteDashboard component
- [x] 4.2 Create `ComisionCard.tsx`: card component showing materia name, cohorte, metricas (alumnos, atrasados, pendientes), click navigates to /comision/:materiaId/:cohorteId
- [x] 4.3 Create `MetricasResumen.tsx`: small stat cards (kpi style) for dashboard summary
- [x] 4.4 Create `DocenteDashboard.tsx`: composes ComisionCard[] grid, loading spinner, error state, empty state

## 5. Comisión Layout con tabs

- [x] 5.1 Create `ComisionLayoutPage.tsx`: lazy-loaded layout page, reads materiaId + cohorteId from route params, renders ComisionTabs + <Outlet />
- [x] 5.2 Create `ComisionTabs.tsx`: tab navigation component with links to /comision/:materiaId/:cohorteId/{calificaciones|umbral|atrasados|ranking|notas|reportes|comunicaciones}, highlights active tab from current route

## 6. Calificaciones — Wizard de importación

- [x] 6.1 Create `CalificacionesPage.tsx`: lazy-loaded page, renders ImportWizard
- [x] 6.2 Create `UploadStep.tsx`: dropzone + file input for .xlsx/.csv, validates format client-side, calls uploadPreview mutation on file select, shows loading/error states
- [x] 6.3 Create `PreviewStep.tsx`: table of alumnos × actividades with checkboxes per activity column, shows metadatos as fixed columns, "Select All" / "Deselect All" toggle
- [x] 6.4 Create `ConfirmStep.tsx`: resumen card (actividades a importar, alumnos afectados), "Confirmar importación" button, success/error result display
- [x] 6.5 Create `ImportWizard.tsx`: orchestrator component managing wizard state (step index + preview data), renders current step, step indicator (1/3, 2/3, 3/3), back/next/confirm navigation

## 7. Umbral de aprobación

- [x] 7.1 Create `UmbralPage.tsx`: lazy-loaded page, renders UmbralConfig
- [x] 7.2 Create `UmbralSlider.tsx`: slider + numeric input synchronized, validation 0-100, shows current value
- [x] 7.3 Create `UmbralConfig.tsx`: loads umbral via useUmbral, shows UmbralSlider + valoresTextuales editor + save button + recalcular button, loading/error states

## 8. Atrasados, Ranking, Notas Finales, Reportes

- [x] 8.1 Create `AtrasadosPage.tsx`: lazy-loaded page, renders AtrasadosTable with FiltroBusqueda
- [x] 8.2 Create `FiltroBusqueda.tsx`: debounced search input component
- [x] 8.3 Create `AtrasadosTable.tsx`: table with columns (alumno, email, actividad, causa badge), summary header "X atrasados", "Comunicar" button per row, loading/empty/error states
- [x] 8.4 Create `RankingPage.tsx`: lazy-loaded page, renders RankingTable
- [x] 8.5 Create `RankingTable.tsx`: sorted table (posición, nombre, email, comisión, aprobadas, total, % con barra de progreso), loading/empty/error states
- [x] 8.6 Create `NotasFinalesPage.tsx`: lazy-loaded page, renders NotasTable
- [x] 8.7 Create `NotasTable.tsx`: table with expandible rows — columnas (nombre, email, comisión, actividades consideradas, nota final), row expand shows detalle de actividades individuales, loading/empty/error states
- [x] 8.8 Create `ReportesPage.tsx`: lazy-loaded page, renders ReportesView
- [x] 8.9 Create `MetricasConsolidadas.tsx`: KPI cards row (total alumnos, total actividades, promedio general, aprobados, desaprobados, % aprobación)
- [x] 8.10 Create `DistribucionActividades.tsx`: table per actividad (nombre, alumnos con nota, promedio, aprobados, desaprobados) + simple bar chart (CSS/SVG) of aprobados vs desaprobados per activity
- [x] 8.11 Create `ReportesView.tsx`: composes MetricasConsolidadas + DistribucionActividades, loading/empty/error states

## 9. Exportar TPs sin corregir

- [x] 9.1 Include export button in a dedicated page or section — single button "Exportar TPs sin corregir" with download icon, triggers CSV download via useExportarTPs, loading spinner on button while downloading, disabled when no data

## 10. Comunicaciones a alumnos

- [x] 10.1 Create `ComunicacionesPage.tsx`: lazy-loaded page, renders ComunicacionesView
- [x] 10.2 Create `FormularioRedaccion.tsx`: React Hook Form + Zod validation (asunto required, cuerpo required), textarea for body, table with checkboxes for selecting destinatarios from atrasados/alumnos
- [x] 10.3 Create `PreviewModal.tsx`: modal dialog showing asunto, cuerpo renderizado, destinatarios count, "Enviar" / "Cancelar" buttons, loading state on submit, error display
- [x] 10.4 Create `EstadoBadge.tsx`: badge component mapping estado → color (Pendiente=gris, Enviando=azul, Enviado=verde, Error=rojo, Cancelado=naranja)
- [x] 10.5 Create `TrackingTable.tsx`: table of sent communications (destinatario enmascarado, asunto, estado badge, fecha), distribution summary (X pendientes, Y enviados, etc.), polling via useComunicaciones with conditional refetchInterval
- [x] 10.6 Create `ComunicacionesView.tsx`: tabbed or split view with FormularioRedaccion + Preview modal + TrackingTable section, loading/empty/error states

## 11. Monitor de seguimiento

- [x] 11.1 Create `MonitorPage.tsx`: lazy-loaded page, renders MonitorView
- [x] 11.2 Create `FiltrosPanel.tsx`: filter form with inputs for alumno, email, comisión, regional, actividad, min_actividades; triggers refetch on change
- [x] 11.3 Create `MonitorTable.tsx`: table with columns (nombre, email, comisión, regional, total, aprobadas, desaprobadas, pendientes, % con barra de progreso colorida), loading/empty/error states
- [x] 11.4 Create `MonitorView.tsx`: composes FiltrosPanel + MonitorTable

## 12. Router — Integrar nuevas rutas

- [x] 12.1 Add lazy imports for all new pages in `router/index.tsx`: DocenteDashboardPage, ComisionLayoutPage, CalificacionesPage, UmbralPage, AtrasadosPage, RankingPage, NotasFinalesPage, ReportesPage, ComunicacionesPage, MonitorPage
- [x] 12.2 Add new protected routes under the existing AuthGuard/AppLayout in the router config:
  - `/dashboard` → DocenteDashboardPage
  - `/comision/:materiaId/:cohorteId` → ComisionLayoutPage (with nested routes for each tab)
  - `/monitor` → MonitorPage
- [x] 12.3 Add permission guards to routes where appropriate (PermissionGuard with `require_permission`)
- [x] 12.4 Update AppLayout sidebar menu items to include new routes for PROFESOR role dynamically

## 13. Tests

- [x] 13.1 Create MSW handlers for academico endpoints: calificaciones/preview, calificaciones/importar, umbral, analisis/atrasados, analisis/ranking, notas-finales, analisis/reportes-rapidos, analisis/exportar-tps, comunicaciones (preview, enviar, enviar-lote, lote/:id, materia/:id), monitor/seguimiento
- [x] 13.2 Write `ImportWizard.test.tsx`:
  - Renders upload step with dropzone
  - Shows validation error on invalid file format
  - Progresses through wizard steps (upload → preview → confirm)
  - Calls confirm API and shows success result
- [x] 13.3 Write `AtrasadosTable.test.tsx`:
  - Renders atrasados list
  - Displays correct cause badge (rojo/naranja)
  - Filters by search input
  - Shows empty state when no atrasados
- [x] 13.4 Write `ComunicacionesView.test.tsx`:
  - Renders redaction form with validation
  - Shows preview modal on "Previsualizar" click
  - Sends communication on confirm
  - Shows tracking table with polling
- [x] 13.5 Write `TrackingTable.test.tsx`:
  - Shows distribution summary
  - Displays correct estado badges
  - Shows empty state when no communications
