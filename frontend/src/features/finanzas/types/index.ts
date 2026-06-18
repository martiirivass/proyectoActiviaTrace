export type EstadoLiquidacion = 'Abierta' | 'Cerrada'

export interface Liquidacion {
  id: string
  docente_id: string
  docente_nombre: string
  docente_apellido: string
  rol: string
  monto_base: number
  monto_plus: number
  total: number
  es_nexo: boolean
  excluido_por_factura: boolean
  estado: EstadoLiquidacion
  cohorte_id: string
  periodo: string
  created_at: string
  updated_at: string
}

export interface LiquidacionKPI {
  total_facturante: number
  total_no_facturante: number
  cantidad_facturante: number
  cantidad_no_facturante: number
}

export interface LiquidacionResponse {
  items: Liquidacion[]
  kpis: LiquidacionKPI
}

export interface LiquidacionHistorialEntry {
  id: string
  fecha: string
  usuario: string
  cohorte: string
  periodo: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface SalarioBase {
  id: string
  rol: string
  monto: number
  desde: string
  hasta: string | null
  vigente: boolean
}

export interface SalarioBaseFormData {
  rol: string
  monto: number
  desde: string
  hasta?: string | null
}

export interface SalarioPlus {
  id: string
  grupo: string
  rol: string
  descripcion: string
  monto: number
  desde: string
  hasta: string | null
  vigente: boolean
}

export interface SalarioPlusFormData {
  grupo: string
  rol: string
  descripcion: string
  monto: number
  desde: string
  hasta?: string | null
}

export type EstadoFactura = 'Pendiente' | 'Abonada'

export interface Factura {
  id: string
  docente_id: string
  docente_nombre: string
  docente_apellido: string
  periodo: string
  detalle: string
  referencia_archivo?: string
  tamano_kb?: number
  materia_id?: string
  materia_nombre?: string
  comision?: string
  monto: number
  estado: EstadoFactura
  fecha_abono?: string
  created_at: string
  updated_at: string
}

export interface FacturaFormData {
  docente_id: string
  periodo: string
  detalle: string
  referencia_archivo?: string
  tamano_kb?: number
  materia_id?: string
  comision?: string
}

export interface FacturaFiltros {
  periodo?: string
  estado?: EstadoFactura
  usuario_id?: string
}
