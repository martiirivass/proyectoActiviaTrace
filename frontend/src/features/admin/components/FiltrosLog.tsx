import { useState } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import type { AuditLogFiltros } from '@/features/admin/types'

interface FiltrosLogProps {
  onFilter: (filtros: AuditLogFiltros) => void
}

export function FiltrosLog({ onFilter }: FiltrosLogProps) {
  const [accion, setAccion] = useState('')
  const [actorId, setActorId] = useState('')
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [materiaId, setMateriaId] = useState('')

  const handleFilter = () => {
    const f: AuditLogFiltros = { limit: 50 }
    if (accion) f.accion = accion
    if (actorId) f.actor_id = actorId
    if (desde) f.desde = desde
    if (hasta) f.hasta = hasta
    if (materiaId) f.materia_id = materiaId
    onFilter(f)
  }

  const handleClear = () => {
    setAccion('')
    setActorId('')
    setDesde('')
    setHasta('')
    setMateriaId('')
    onFilter({ limit: 50 })
  }

  return (
    <div className="flex flex-wrap items-end gap-4 rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-gray-700">Acción</label>
        <select
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={accion}
          onChange={(e) => setAccion(e.target.value)}
        >
          <option value="">Todas</option>
          <option value="CALIFICACIONES_IMPORTAR">CALIFICACIONES_IMPORTAR</option>
          <option value="COMUNICACION_ENVIAR">COMUNICACION_ENVIAR</option>
          <option value="LIQUIDACION_CALCULAR">LIQUIDACION_CALCULAR</option>
          <option value="LIQUIDACION_CERRAR">LIQUIDACION_CERRAR</option>
          <option value="USUARIO_CREAR">USUARIO_CREAR</option>
          <option value="USUARIO_ACTUALIZAR">USUARIO_ACTUALIZAR</option>
        </select>
      </div>
      <Input label="ID Actor" placeholder="Filtrar por actor" value={actorId} onChange={(e) => setActorId(e.target.value)} />
      <Input label="Desde" type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
      <Input label="Hasta" type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} />
      <Input label="ID Materia" placeholder="Filtrar por materia" value={materiaId} onChange={(e) => setMateriaId(e.target.value)} />
      <Button onClick={handleFilter}>Filtrar</Button>
      <Button variant="ghost" onClick={handleClear}>Limpiar Filtros</Button>
    </div>
  )
}
