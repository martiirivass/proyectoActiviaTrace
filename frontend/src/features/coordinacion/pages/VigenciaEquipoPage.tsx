import { useState } from 'react'
import { Card } from '@/shared/components/ui/Card'
import { Button } from '@/shared/components/ui/Button'
import { Alert } from '@/shared/components/ui/Alert'
import { useModificarVigencia } from '@/features/coordinacion/hooks/useEquipos'

export function VigenciaEquipoPage() {
  const mutation = useModificarVigencia()
  const [form, setForm] = useState({
    materia_id: '',
    carrera_id: '',
    cohorte_id: '',
    vigencia_desde: '',
    vigencia_hasta: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(form)
  }

  return (
    <div className="space-y-4">
      <h3 className="text-base font-medium text-gray-800">Modificar Vigencia de Equipo</h3>

      {mutation.isSuccess && (
        <Alert variant="success" message="Vigencia actualizada exitosamente" />
      )}
      {mutation.isError && (
        <Alert variant="error" message="Error al actualizar la vigencia" />
      )}

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <p className="text-sm text-gray-600">
            Actualiza la vigencia de todas las asignaciones de un equipo seleccionado.
          </p>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Materia ID</label>
              <input
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={form.materia_id}
                onChange={(e) => setForm((f) => ({ ...f, materia_id: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Carrera ID</label>
              <input
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={form.carrera_id}
                onChange={(e) => setForm((f) => ({ ...f, carrera_id: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Cohorte ID</label>
              <input
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={form.cohorte_id}
                onChange={(e) => setForm((f) => ({ ...f, cohorte_id: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Nueva vigencia desde</label>
              <input
                type="date"
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={form.vigencia_desde}
                onChange={(e) => setForm((f) => ({ ...f, vigencia_desde: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Nueva vigencia hasta</label>
              <input
                type="date"
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={form.vigencia_hasta}
                onChange={(e) => setForm((f) => ({ ...f, vigencia_hasta: e.target.value }))}
                required
              />
            </div>
          </div>
          <div className="flex justify-end">
            <Button type="submit" loading={mutation.isPending}>
              Actualizar Vigencia
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
