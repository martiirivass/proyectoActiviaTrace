import { useState } from 'react'
import { Card } from '@/shared/components/ui/Card'
import { Button } from '@/shared/components/ui/Button'
import { Alert } from '@/shared/components/ui/Alert'
import { useClonarEquipo } from '@/features/coordinacion/hooks/useEquipos'

export function ClonarEquipoPage() {
  const mutation = useClonarEquipo()
  const [form, setForm] = useState({
    origen_materia_id: '',
    origen_carrera_id: '',
    origen_cohorte_id: '',
    destino_cohorte_id: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(form)
  }

  return (
    <div className="space-y-4">
      <h3 className="text-base font-medium text-gray-800">Clonar Equipo entre Períodos</h3>

      {mutation.isSuccess && (
        <Alert variant="success" message="Equipo clonado exitosamente" />
      )}
      {mutation.isError && (
        <Alert variant="error" message="Error al clonar el equipo" />
      )}

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <p className="text-sm text-gray-600">
            Duplica todas las asignaciones de un equipo origen hacia una nueva cohorte destino.
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Origen — Materia ID</label>
              <input
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={form.origen_materia_id}
                onChange={(e) => setForm((f) => ({ ...f, origen_materia_id: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Origen — Carrera ID</label>
              <input
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={form.origen_carrera_id}
                onChange={(e) => setForm((f) => ({ ...f, origen_carrera_id: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Origen — Cohorte ID</label>
              <input
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={form.origen_cohorte_id}
                onChange={(e) => setForm((f) => ({ ...f, origen_cohorte_id: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Destino — Cohorte ID</label>
              <input
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={form.destino_cohorte_id}
                onChange={(e) => setForm((f) => ({ ...f, destino_cohorte_id: e.target.value }))}
                required
              />
            </div>
          </div>
          <div className="flex justify-end">
            <Button type="submit" loading={mutation.isPending}>
              Clonar Equipo
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
