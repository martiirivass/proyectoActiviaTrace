import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card } from '@/shared/components/ui/Card'
import { Button } from '@/shared/components/ui/Button'
import { Alert } from '@/shared/components/ui/Alert'
import { useCreateTarea } from '@/features/coordinacion/hooks/useTareas'

export default function NuevaTareaPage() {
  const navigate = useNavigate()
  const mutation = useCreateTarea()
  const [form, setForm] = useState({
    titulo: '',
    descripcion: '',
    asignado_id: '',
    materia_id: '',
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const payload = {
      ...form,
      materia_id: form.materia_id || undefined,
    }
    mutation.mutate(payload, {
      onSuccess: () => navigate('/dashboard/coordinacion/tareas'),
    })
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Nueva Tarea</h2>

      {mutation.isError && (
        <Alert variant="error" message="Error al crear la tarea" />
      )}

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700">Título</label>
            <input
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={form.titulo}
              onChange={(e) => setForm((f) => ({ ...f, titulo: e.target.value }))}
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">Descripción</label>
            <textarea
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              rows={4}
              value={form.descripcion}
              onChange={(e) => setForm((f) => ({ ...f, descripcion: e.target.value }))}
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">Asignar a (ID de usuario)</label>
            <input
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={form.asignado_id}
              onChange={(e) => setForm((f) => ({ ...f, asignado_id: e.target.value }))}
              required
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">Materia (opcional)</label>
            <input
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={form.materia_id}
              onChange={(e) => setForm((f) => ({ ...f, materia_id: e.target.value }))}
              placeholder="ID de materia"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate('/dashboard/coordinacion/tareas')}
            >
              Cancelar
            </Button>
            <Button type="submit" loading={mutation.isPending}>
              Crear Tarea
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
