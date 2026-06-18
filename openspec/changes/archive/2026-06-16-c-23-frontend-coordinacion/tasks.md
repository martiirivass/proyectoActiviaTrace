## 1. Scaffolding and Shared Types

- [x] 1.1 Create `features/coordinacion/` module with subdirectories: `equipos/`, `avisos/`, `tareas/`, `monitores/`, `encuentros/`, `coloquios/`, `setup/`
- [x] 1.2 Create shared coordinacion types in `features/coordinacion/types/`: equipo, aviso, tarea, encuentro, coloquio interfaces
- [x] 1.3 Create base API services in `features/coordinacion/services/`: equiposService, avisosService, tareasService, encuentrosService, coloquiosService, setupService
- [x] 1.4 Add lazy imports and routes to `router/index.tsx` for all coordinacion pages under `/dashboard/coordinacion/*`

## 2. Equipos Docentes UI

- [x] 2.1 Create `EquiposDashboardPage` with tabs: Mis Equipos, Asignaciones, Asignación Masiva, Clonar, Exportar
- [x] 2.2 Create `MisEquiposPage` with filterable table of current user's assignments (F4.2)
- [x] 2.3 Create `AsignacionesPage` with searchable global assignments table (F4.3)
- [x] 2.4 Create `AsignacionMasivaPage` with multi-select docente picker, target selector, role picker, vigencia form (F4.4)
- [x] 2.5 Create `ClonarEquipoPage` with origin/target selectors and confirmation (F4.5)
- [x] 2.6 Create `VigenciaEquipoPage` with bulk date update for selected equipo (F4.6)
- [x] 2.7 Create `ExportarEquipo` button component with download trigger (F4.7)

## 3. Avisos UI

- [x] 3.1 Create `AvisosPage` with aviso list table (titulo, alcance, severidad, vigencia, ack rate)
- [x] 3.2 Create `AvisoFormPage` with form fields: titulo, contenido, alcance (dynamic selectors), severidad, vigencia dates, requiere_ack toggle
- [x] 3.3 Implement dynamic scope selectors (materia/cohorte/rol) controlled by alcance field
- [x] 3.4 Add acknowledgment stats display per aviso in list and detail views

## 4. Tareas Internas UI

- [x] 4.1 Create `TareasPage` with table of all tenant tasks, filterable by docente, asignador, materia, estado
- [x] 4.2 Create `MisTareasPage` view for current user's assigned tasks (F8.1)
- [x] 4.3 Create `TareaDetailPage` with task info, estado change, delegar action, comment thread
- [x] 4.4 Create `TareaDelegarModal` with user selector from team members (F8.2)
- [x] 4.5 Implement task comment submission and display

## 5. Monitores Transversales UI

- [x] 5.1 Create `MonitorGeneralPage` with filters: materia, regional, comision, free text, estado, criterio (F2.7)
- [x] 5.2 Create `MonitorCoordinacionPage` extending MonitorGeneralPage with date range filter (F2.9)
- [x] 5.3 Add export button and limpiar filtros to both monitor views
- [x] 5.4 Create shared `DateRangePicker` component for date range filtering

## 6. Encuentros Admin UI

- [x] 6.1 Create `EncuentrosAdminPage` with transversal encuentros table filtered by materia, docente, fecha (F6.5)

## 7. Coloquios UI

- [x] 7.1 Create `ColoquiosPage` with metrics panel (convocados, instancias, reservas, notas) (F7.1)
- [x] 7.2 Create `ConvocatoriasListPage` with table of all convocatorias and their metrics (F7.4)
- [x] 7.3 Create `ConvocatoriaFormPage` for creating/editing convocatorias with days and cupos (F7.3)
- [x] 7.4 Create `AdminColoquiosPage` with sub-sections: convocatorias CRUD, resultados consolidados, agenda reservas (F7.5)

## 8. Setup de Cuatrimestre UI

- [x] 8.1 Create `SetupCuatrimestrePage` as multi-step wizard with step state management
- [x] 8.2 Implement Step 1: Create cohorte form (identifier, name, vigencia dates)
- [x] 8.3 Implement Step 2: Clonar equipo (origin selector, target cohorte)
- [x] 8.4 Implement Step 3: Ajustar asignaciones (mass assignment interface)
- [x] 8.5 Implement Step 4: Cargar programas (file upload per materia × cohorte)
- [x] 8.6 Implement Step 5: Cargar fechas de evaluaciones
- [x] 8.7 Implement Step 6: Publicar aviso de bienvenida scoped to cohorte
- [x] 8.8 Add final confirmation/summary step and apply all mutations

## 9. Route Integration and Navigation

- [x] 9.1 Add all coordinacion route definitions to `router/index.tsx` with `requirePermission` guards
- [x] 9.2 Extract UnauthorizedPlaceholder and NotFoundPlaceholder to shared components
- [x] 9.3 Verify sidebar/nav shows coordinacion links only for COORDINADOR/ADMIN roles
