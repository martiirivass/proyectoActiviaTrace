export interface Comision {
  materia_id: string
  cohorte_id: string
  materia_nombre: string
  cohorte_nombre: string
  alumnos_count: number
  atrasados_count: number
  pendientes_count: number
}

export interface Alumno {
  id: string
  legajo: string
  nombre: string
  apellido: string
  email: string
}

export interface ActividadDetectada {
  id: string
  nombre: string
  tipo: 'numerica' | 'textual'
}

export interface AlumnoPreviewRow {
  alumno: Alumno
  valores: Record<string, string | number | null>
}

export interface CalificacionPreview {
  actividades_detectadas: ActividadDetectada[]
  alumnos: AlumnoPreviewRow[]
  metadatos_columnas: string[]
}

export interface ConfirmImportRequest {
  materia_id: string
  cohorte_id: string
  actividades: string[]
  parse_data: unknown
}

export interface ImportResult {
  registros_creados: number
  resumen: unknown
}

export interface UmbralMateria {
  umbral_pct: number
  valores_aprobatorios: string[]
}

export interface UpdateUmbralRequest {
  materia_id: string
  umbral_pct: number
  valores_aprobatorios: string[]
}

export type CausaAtraso = 'nota_bajo_umbral' | 'actividad_faltante'

export interface AtrasadoEntry {
  alumno: Alumno
  actividad: string
  causa: CausaAtraso
}

export interface RankingEntry {
  posicion: number
  alumno: Alumno
  email: string
  comision: string
  aprobadas: number
  total: number
  porcentaje: number
}

export interface ActividadDetalle {
  nombre: string
  nota: string | number | null
}

export interface NotaFinalEntry {
  alumno: Alumno
  email: string
  comision: string
  actividades_consideradas: number
  nota_final: number | null
  actividades: ActividadDetalle[]
}

export interface DistribucionActividad {
  nombre: string
  alumnos_con_nota: number
  promedio: number | null
  aprobados: number
  desaprobados: number
}

export interface ReporteRapido {
  alumnos_total: number
  actividades_total: number
  promedio_general: number | null
  aprobados: number
  desaprobados: number
  pct_aprobacion: number | null
  distribucion_actividades: DistribucionActividad[]
}

export interface ComunicacionPreviewRequest {
  asunto: string
  cuerpo: string
  materia_id: string
  destinatarios: string[]
}

export interface ComunicacionPreview {
  preview_html: string
  cantidad_destinatarios: number
}

export interface EnviarComunicacionRequest {
  asunto: string
  cuerpo: string
  materia_id: string
  destinatarios: string[]
}

export interface EnviarComunicacionResponse {
  lote_id: string
  total_mensajes: number
  mensaje_id?: string
}

export type EstadoComunicacion = 'pendiente' | 'enviando' | 'enviado' | 'error' | 'cancelado'

export interface TrackingMessage {
  id: string
  destinatario: string
  asunto: string
  estado: EstadoComunicacion
  fecha_envio: string | null
}

export interface TrackingDistribucion {
  pendiente: number
  enviando: number
  enviado: number
  error: number
  cancelado: number
}

export interface TrackingLote {
  lote: { id: string }
  mensajes: TrackingMessage[]
  distribucion: TrackingDistribucion
}

export interface SeguimientoMateria {
  comunicaciones: TrackingMessage[]
  distribucion: TrackingDistribucion
}

export interface MonitorEntry {
  alumno: Alumno
  email: string
  comision: string
  regional: string
  total: number
  aprobadas: number
  desaprobadas: number
  pendientes: number
  porcentaje: number
}

export interface MonitorFiltros {
  alumno_id?: string
  email?: string
  comision?: string
  regional?: string
  actividad?: string
  min_actividades?: number
}
