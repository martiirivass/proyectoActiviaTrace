import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card } from '@/shared/components/ui/Card'
import { Button } from '@/shared/components/ui/Button'
import { Alert } from '@/shared/components/ui/Alert'
import { useCreateConvocatoria, useConvocatoria, useUpdateConvocatoria } from '@/features/coordinacion/hooks/useColoquios'
import type { ConvocatoriaFormData } from '@/features/coordinacion/types'

export default function ConvocatoriaFormPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isEdit = !!id
  const { data: existing } = useConvocatoria(id)
  const createMutation = useCreateConvocatoria()
  const updateMutation = useUpdateConvocatoria()

  const [form, setForm] = useState<ConvocatoriaFormData>({
    materia_id: existing?.materia_id ?? '',
    instancia: existing?.instancia ?? '',
    days: existing?.days ?? [],
    cupos: existing?.cupos ?? 0,
  })

  const [dayInput, setDayInput] = useState('')

  const addDay = () => {
    if (dayInput.trim() && !form.days.includes(dayInput.trim())) {
      setForm((f) => ({ ...f, days: [...f.days, dayInput.trim()] }))
      setDayInput('')
    }
  }

  const removeDay = (day: string) => {
    setForm((f) => ({ ...f, days: f.days.filter((d) => d !== day) }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isEdit && id) {
      updateMutation.mutate(
        { id, data: form },
        { onSuccess: () => navigate('/dashboard/coordinacion/coloquios/convocatorias') },
      )
    } else {
      createMutation.mutate(form, {
        onSuccess: () => navigate('/dashboard/coordinacion/coloquios/convocatorias'),
      })
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">
        {isEdit ? 'Editar Convocatoria' : 'Nueva Convocatoria'}
      </h2>

      {(createMutation.isError || updateMutation.isError) && (
        <Alert variant="error" message="Error al guardar la convocatoria" />
      )}

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700">Materia</label>
            <input
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={form.materia_id}
              onChange={(e) => setForm((f) => ({ ...f, materia_id: e.target.value }))}
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700">Instancia</label>
            <input
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={form.instancia}
              onChange={(e) => setForm((f) => ({ ...f, instancia: e.target.value }))}
              required
              placeholder="Ej: Primer Llamado, Segundo Llamado"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700">Cupos</label>
            <input
              type="number"
              min={1}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={form.cupos}
              onChange={(e) => setForm((f) => ({ ...f, cupos: Number(e.target.value) }))}
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700">Días</label>
            <div className="mt-1 flex gap-2">
              <input
                className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={dayInput}
                onChange={(e) => setDayInput(e.target.value)}
                placeholder="Ej: 2026-07-15"
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addDay())}
              />
              <Button type="button" variant="secondary" size="sm" onClick={addDay}>
                Agregar
              </Button>
            </div>
            {form.days.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {form.days.map((day) => (
                  <span
                    key={day}
                    className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700"
                  >
                    {day}
                    <button
                      type="button"
                      onClick={() => removeDay(day)}
                      className="text-blue-500 hover:text-blue-700"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate('/dashboard/coordinacion/coloquios/convocatorias')}
            >
              Cancelar
            </Button>
            <Button type="submit" loading={isPending}>
              {isEdit ? 'Guardar Cambios' : 'Crear Convocatoria'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
