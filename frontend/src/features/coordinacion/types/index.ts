// ── Equipos Docentes ──────────────────────────────────────────
export interface EquipoAssignment {
  id: string
  docente_id: string
  docente_nombre: string
  docente_apellido: string
  materia_id: string
  materia_nombre: string
  carrera_nombre: string
  cohorte_id: string
  cohorte_nombre: string
  rol: string
  vigencia_desde: string
  vigencia_hasta: string
  estado: 'activo' | 'inactivo' | 'finalizado'
  report_relation?: string
}

export interface MisEquiposFiltros {
  estado?: string
  materia?: string
  rol?: string
  carrera?: string
  cohorte?: string
}

export interface AsignacionesFiltros {
  materia?: string
  carrera?: string
  cohorte?: string
  usuario?: string
  role?: string
  report_relation?: string
}

export interface AsignacionMasivaRequest {
  docentes_ids: string[]
  materia_id: string
  carrera_id: string
  cohorte_id: string
  rol: string
  vigencia_desde: string
  vigencia_hasta: string
}

export interface ClonarEquipoRequest {
  origen_materia_id: string
  origen_carrera_id: string
  origen_cohorte_id: string
  destino_cohorte_id: string
}

export interface VigenciaEquipoRequest {
  materia_id: string
  carrera_id: string
  cohorte_id: string
  vigencia_desde: string
  vigencia_hasta: string
}

// ── Avisos ────────────────────────────────────────────────────
export type AlcanceAviso = 'Global' | 'PorMateria' | 'PorCohorte' | 'PorRol'
export type SeveridadAviso = 'baja' | 'media' | 'alta' | 'critica'

export interface Aviso {
  id: string
  titulo: string
  contenido: string
  alcance: AlcanceAviso
  scope_id?: string
  severidad: SeveridadAviso
  vigencia_inicio: string
  vigencia_fin: string
  orden: number
  requiere_ack: boolean
  created_at: string
  updated_at: string
}

export interface AvisoFormData {
  titulo: string
  contenido: string
  alcance: AlcanceAviso
  scope_id?: string
  severidad: SeveridadAviso
  vigencia_inicio: string
  vigencia_fin: string
  orden: number
  requiere_ack: boolean
}

export interface AckStats {
  total_destinatarios: number
  acknowledgments_count: number
  acknowledgment_rate: number
}

// ── Tareas Internas ───────────────────────────────────────────
export type TareaEstado = 'pendiente' | 'en_curso' | 'completada' | 'cancelada'

export interface Tarea {
  id: string
  titulo: string
  descripcion: string
  estado: TareaEstado
  asignado_id: string
  asignado_nombre: string
  asignador_id: string
  asignador_nombre: string
  materia_id?: string
  materia_nombre?: string
  created_at: string
  updated_at: string
}

export interface TareaComment {
  id: string
  tarea_id: string
  autor_id: string
  autor_nombre: string
  contenido: string
  created_at: string
}

export interface TareaCreateRequest {
  titulo: string
  descripcion: string
  asignado_id: string
  materia_id?: string
}

export interface TareaDelegarRequest {
  tarea_id: string
  nuevo_asignado_id: string
}

export interface TareaEstadoChange {
  estado: TareaEstado
}

export interface TareaCommentRequest {
  tarea_id: string
  contenido: string
}

export interface TareasFiltros {
  docente?: string
  asignador?: string
  materia?: string
  estado?: string
  busqueda?: string
}

// ── Encuentros Admin ──────────────────────────────────────────
export interface EncuentroEntry {
  id: string
  materia_id: string
  materia_nombre: string
  cohorte_nombre: string
  docente_nombre: string
  fecha: string
  tema: string
  asistentes_count: number
  created_at: string
}

export interface EncuentrosAdminFiltros {
  materia?: string
  docente?: string
  fecha_desde?: string
  fecha_hasta?: string
}

// ── Coloquios ─────────────────────────────────────────────────
export interface ColoquioMetrics {
  total_alumnos_cargados: number
  instancias_activas: number
  reservas_activas: number
  notas_registradas: number
}

export interface Convocatoria {
  id: string
  materia_id: string
  materia_nombre: string
  instancia: string
  days: string[]
  cupos: number
  convocados: number
  reservas_activas: number
  cupos_libres: number
  created_at: string
  updated_at: string
}

export interface ConvocatoriaFormData {
  materia_id: string
  instancia: string
  days: string[]
  cupos: number
}

// ── Monitor ───────────────────────────────────────────────────
export interface MonitorAlumnoEntry {
  id: string
  legajo: string
  nombre: string
  apellido: string
  email: string
  materia_nombre: string
  regional: string
  comision: string
  estado_actividad: string
  criterio_clasificacion: string
  total_actividades: number
  aprobadas: number
  pendientes: number
}

export interface MonitorFiltrosCoordinacion {
  materia?: string
  regional?: string
  comision?: string
  busqueda?: string
  estado?: string
  criterio?: string
  fecha_desde?: string
  fecha_hasta?: string
  page?: number
  page_size?: number
}

export interface MonitorPaginatedResponse {
  items: MonitorAlumnoEntry[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ── Setup Cuatrimestre ───────────────────────────────────────
export interface WizardStepState {
  step: number
  cohorte?: {
    identifier: string
    name: string
    vigencia_desde: string
    vigencia_hasta: string
  }
  clone_origin?: {
    materia_id: string
    carrera_id: string
    cohorte_id: string
  }
  asignaciones?: AsignacionMasivaRequest[]
  programas?: Array<{
    materia_id: string
    file: File | null
  }>
  fechas?: Array<{
    materia_id: string
    fecha: string
    descripcion: string
  }>
  aviso?: {
    titulo: string
    contenido: string
  }
}

// ── Common ────────────────────────────────────────────────────
export interface SelectOption {
  value: string
  label: string
}
