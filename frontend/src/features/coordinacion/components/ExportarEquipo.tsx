import { useState } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { useExportarEquipo } from '@/features/coordinacion/hooks/useEquipos'

export function ExportarEquipo() {
  const mutation = useExportarEquipo()
  const [materiaId, setMateriaId] = useState('')
  const [carreraId, setCarreraId] = useState('')
  const [cohorteId, setCohorteId] = useState('')
  const [showForm, setShowForm] = useState(false)

  const handleExport = () => {
    mutation.mutate(
      { materiaId, carreraId, cohorteId },
      {
        onSuccess: (data) => {
          const url = window.URL.createObjectURL(data)
          const a = document.createElement('a')
          a.href = url
          a.download = `equipo-${materiaId}-${cohorteId}.csv`
          a.click()
          window.URL.revokeObjectURL(url)
          setShowForm(false)
        },
      },
    )
  }

  return (
    <div>
      <Button variant="secondary" size="sm" onClick={() => setShowForm(!showForm)}>
        Exportar
      </Button>
      {showForm && (
        <div className="absolute z-10 mt-2 rounded-lg border border-gray-200 bg-white p-4 shadow-lg">
          <div className="mb-3 space-y-2">
            <input
              placeholder="Materia ID"
              className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
              value={materiaId}
              onChange={(e) => setMateriaId(e.target.value)}
            />
            <input
              placeholder="Carrera ID"
              className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
              value={carreraId}
              onChange={(e) => setCarreraId(e.target.value)}
            />
            <input
              placeholder="Cohorte ID"
              className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
              value={cohorteId}
              onChange={(e) => setCohorteId(e.target.value)}
            />
          </div>
          <Button size="sm" loading={mutation.isPending} onClick={handleExport}>
            Descargar
          </Button>
        </div>
      )}
    </div>
  )
}
