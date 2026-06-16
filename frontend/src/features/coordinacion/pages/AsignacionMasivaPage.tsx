import { useState } from 'react'
import { Card } from '@/shared/components/ui/Card'
import { Button } from '@/shared/components/ui/Button'
import { Alert } from '@/shared/components/ui/Alert'
import { useAsignacionMasiva } from '@/features/coordinacion/hooks/useEquipos'
import type { AsignacionMasivaRequest } from '@/features/coordinacion/types'

export function AsignacionMasivaPage() {
  const mutation = useAsignacionMasiva()
  const [form, setForm] = useState({
    docentes: '',
    materia_id: '',
    carrera_id: '',
    cohorte_id: '',
    rol: 'PROFESOR',
    vigencia_desde: '',
    vigencia_hasta: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const docentesIds = form.docentes.split(',').map((d) => d.trim()).filter(Boolean)
    if (docentesIds.length === 0) return

    const payload: AsignacionMasivaRequest = {
      docentes_ids: docentesIds,
      materia_id: form.materia_id,
      carrera_id: form.carrera_id,
      cohorte_id: form.cohorte_id,
      rol: form.rol,
      vigencia_desde: form.vigencia_desde,
      vigencia_hasta: form.vigencia_hasta,
    }
    mutation.mutate(payload)
  }

  return (
    <div className="space-y-4">
      <h3 className="text-base font-medium text-gray-800">Asignación Masiva</h3>

      {mutation.isSuccess && (
        <Alert variant="success" message="Asignación masiva completada exitosamente" />
      )}
      {mutation.isError && (
        <Alert variant="error" message="Error al realizar la asignación masiva" />
      )}

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700">IDs de Docentes (separados por coma)</label>
            <textarea
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              rows={3}
              value={form.docentes}
              onChange={(e) => setForm((f) => ({ ...f, docentes: e.target.value }))}
              placeholder="docente-id-1, docente-id-2, ..."
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
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
              <label className="text-sm font-medium text-gray-700">Rol</label>
              <select
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={form.rol}
                onChange={(e) => setForm((f) => ({ ...f, rol: e.target.value }))}
              >
                <option value="PROFESOR">Profesor</option>
                <option value="TUTOR">Tutor</option>
                <option value="COORDINADOR">Coordinador</option>
                <option value="NEXO">Nexo</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Vigencia desde</label>
              <input
                type="date"
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={form.vigencia_desde}
                onChange={(e) => setForm((f) => ({ ...f, vigencia_desde: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Vigencia hasta</label>
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
              Asignar
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
