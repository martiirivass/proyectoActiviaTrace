import { useState, useEffect } from 'react'
import { Button } from '@/shared/components/ui/Button'
import type { MonitorFiltros } from '@/features/academico/types'

interface FiltrosPanelProps {
  onFiltrosChange: (filtros: MonitorFiltros) => void
}

export function FiltrosPanel({ onFiltrosChange }: FiltrosPanelProps) {
  const [alumno, setAlumno] = useState('')
  const [email, setEmail] = useState('')
  const [comision, setComision] = useState('')
  const [regional, setRegional] = useState('')
  const [actividad, setActividad] = useState('')
  const [minActividades, setMinActividades] = useState('')

  const buildFiltros = (): MonitorFiltros => {
    const filtros: MonitorFiltros = {}
    if (alumno.trim()) filtros.alumno_id = alumno.trim()
    if (email.trim()) filtros.email = email.trim()
    if (comision.trim()) filtros.comision = comision.trim()
    if (regional.trim()) filtros.regional = regional.trim()
    if (actividad.trim()) filtros.actividad = actividad.trim()
    const min = Number(minActividades)
    if (min > 0) filtros.min_actividades = min
    return filtros
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      onFiltrosChange(buildFiltros())
    }, 300)
    return () => clearTimeout(timer)
  }, [alumno, email, comision, regional, actividad, minActividades])

  const handleReset = () => {
    setAlumno('')
    setEmail('')
    setComision('')
    setRegional('')
    setActividad('')
    setMinActividades('')
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700">Filtros</h3>
        <Button variant="ghost" size="sm" onClick={handleReset}>
          Limpiar
        </Button>
      </div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        <input
          type="text"
          value={alumno}
          onChange={(e) => setAlumno(e.target.value)}
          placeholder="Alumno"
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <input
          type="text"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <input
          type="text"
          value={comision}
          onChange={(e) => setComision(e.target.value)}
          placeholder="Comisión"
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <input
          type="text"
          value={regional}
          onChange={(e) => setRegional(e.target.value)}
          placeholder="Regional"
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <input
          type="text"
          value={actividad}
          onChange={(e) => setActividad(e.target.value)}
          placeholder="Actividad"
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
        <input
          type="number"
          value={minActividades}
          onChange={(e) => setMinActividades(e.target.value)}
          placeholder="Min. actividades"
          min={0}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
      </div>
    </div>
  )
}
