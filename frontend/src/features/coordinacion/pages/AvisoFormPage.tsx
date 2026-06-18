import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card } from '@/shared/components/ui/Card'
import { Button } from '@/shared/components/ui/Button'
import { Alert } from '@/shared/components/ui/Alert'
import { DynamicScopeSelectors } from '@/features/coordinacion/components/DynamicScopeSelectors'
import { useCreateAviso, useAviso, useUpdateAviso } from '@/features/coordinacion/hooks/useAvisos'
import type { AvisoFormData, AlcanceAviso, SeveridadAviso } from '@/features/coordinacion/types'

export default function AvisoFormPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isEdit = !!id
  const { data: existing } = useAviso(id)
  const createMutation = useCreateAviso()
  const updateMutation = useUpdateAviso()

  const [form, setForm] = useState<AvisoFormData>({
    titulo: existing?.titulo ?? '',
    contenido: existing?.contenido ?? '',
    alcance: (existing?.alcance as AlcanceAviso) ?? 'Global',
    scope_id: existing?.scope_id ?? '',
    severidad: (existing?.severidad as SeveridadAviso) ?? 'baja',
    vigencia_inicio: existing?.vigencia_inicio ?? '',
    vigencia_fin: existing?.vigencia_fin ?? '',
    orden: existing?.orden ?? 0,
    requiere_ack: existing?.requiere_ack ?? false,
  })

  const update = (partial: Partial<AvisoFormData>) =>
    setForm((f) => ({ ...f, ...partial }))

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const payload = { ...form, scope_id: form.alcance === 'Global' ? undefined : form.scope_id }

    if (isEdit && id) {
      updateMutation.mutate(
        { id, data: payload },
        { onSuccess: () => navigate('/dashboard/coordinacion/avisos') },
      )
    } else {
      createMutation.mutate(payload, {
        onSuccess: () => navigate('/dashboard/coordinacion/avisos'),
      })
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">
        {isEdit ? 'Editar Aviso' : 'Nuevo Aviso'}
      </h2>

      {(createMutation.isError || updateMutation.isError) && (
        <Alert variant="error" message="Error al guardar el aviso" />
      )}

      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700">Título</label>
            <input
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              value={form.titulo}
              onChange={(e) => update({ titulo: e.target.value })}
              required
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700">Contenido</label>
            <textarea
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              rows={4}
              value={form.contenido}
              onChange={(e) => update({ contenido: e.target.value })}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Alcance</label>
              <select
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={form.alcance}
                onChange={(e) => update({ alcance: e.target.value as AlcanceAviso })}
              >
                <option value="Global">Global</option>
                <option value="PorMateria">Por Materia</option>
                <option value="PorCohorte">Por Cohorte</option>
                <option value="PorRol">Por Rol</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Severidad</label>
              <select
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={form.severidad}
                onChange={(e) => update({ severidad: e.target.value as SeveridadAviso })}
              >
                <option value="baja">Baja</option>
                <option value="media">Media</option>
                <option value="alta">Alta</option>
                <option value="critica">Crítica</option>
              </select>
            </div>
          </div>

          <DynamicScopeSelectors
            alcance={form.alcance}
            scopeId={form.scope_id ?? ''}
            onScopeIdChange={(v) => update({ scope_id: v })}
          />

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Vigencia desde</label>
              <input
                type="date"
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={form.vigencia_inicio}
                onChange={(e) => update({ vigencia_inicio: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Vigencia hasta</label>
              <input
                type="date"
                className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                value={form.vigencia_fin}
                onChange={(e) => update({ vigencia_fin: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Requiere ACK</label>
            <input
              type="checkbox"
              checked={form.requiere_ack}
              onChange={(e) => update({ requiere_ack: e.target.checked })}
              className="rounded border-gray-300"
            />
          </div>

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => navigate('/dashboard/coordinacion/avisos')}
            >
              Cancelar
            </Button>
            <Button type="submit" loading={isPending}>
              {isEdit ? 'Guardar Cambios' : 'Publicar Aviso'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
