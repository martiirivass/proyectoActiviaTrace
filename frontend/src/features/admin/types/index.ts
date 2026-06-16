export interface Carrera {
  id: string
  codigo: string
  nombre: string
  activo: boolean
  created_at: string
  updated_at: string
}

export interface CarreraFormData {
  codigo: string
  nombre: string
}

export interface Cohorte {
  id: string
  carrera_id: string
  carrera_nombre: string
  nombre: string
  anio: number
  activo: boolean
  created_at: string
  updated_at: string
}

export interface CohorteFormData {
  carrera_id: string
  nombre: string
  anio: number
}

export interface Materia {
  id: string
  codigo: string
  nombre: string
  activo: boolean
  created_at: string
  updated_at: string
}

export interface MateriaFormData {
  codigo: string
  nombre: string
}

export interface Dictado {
  id: string
  materia_id: string
  materia_nombre: string
  materia_codigo: string
  carrera_id: string
  carrera_nombre: string
  cohorte_id: string
  cohorte_nombre: string
  nombre: string
  created_at: string
  updated_at: string
}

export interface DictadoFormData {
  materia_id: string
  carrera_id: string
  cohorte_id: string
  nombre: string
}

export interface Usuario {
  id: string
  email: string
  nombre: string
  apellido: string
  dni: string
  roles: string[]
  regional?: string
  facturador: boolean
  activo: boolean
  cuil?: string
  cbu?: string
  alias_cbu?: string
  banco?: string
  legajo?: string
  legajo_profesional?: string
  created_at: string
  updated_at: string
}

export interface UsuarioFormData {
  email: string
  nombre: string
  apellido: string
  dni: string
  password?: string
  cuil?: string
  cbu?: string
  alias_cbu?: string
  banco?: string
  regional?: string
  legajo?: string
  legajo_profesional?: string
  facturador: boolean
}

export interface UsuarioFiltros {
  search?: string
  rol?: string
  activo?: boolean
  page?: number
  per_page?: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface AuditDashboard {
  acciones_por_dia: AccionesPorDia[]
  comunicaciones_por_docente: ComunicacionesPorDocente[]
  interacciones_por_docente_materia: InteraccionesPorDocenteMateria[]
  ultimas_acciones: AuditLogEntry[]
}

export interface AccionesPorDia {
  fecha: string
  total: number
}

export interface ComunicacionesPorDocente {
  docente: string
  pendientes: number
  enviando: number
  enviados: number
  error: number
  cancelados: number
  total: number
}

export interface InteraccionesPorDocenteMateria {
  docente: string
  materia: string
  total_acciones: number
  desglose?: Record<string, number>
}

export interface AuditLogEntry {
  id: string
  fecha_hora: string
  actor: string
  actor_id: string
  accion: string
  materia?: string
  materia_id?: string
  detalle: string
  ip?: string
  metadata?: Record<string, unknown>
}

export interface AuditLogFiltros {
  accion?: string
  actor_id?: string
  desde?: string
  hasta?: string
  materia_id?: string
  page?: number
  per_page?: number
  offset?: number
  limit?: number
}

export interface AuditLogResponse {
  items: AuditLogEntry[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface AuditoriaFiltros {
  desde?: string
  hasta?: string
  materia_id?: string
}
