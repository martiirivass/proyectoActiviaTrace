import { useState } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { useDelegarTarea } from '@/features/coordinacion/hooks/useTareas'

interface TareaDelegarModalProps {
  tareaId: string
  onClose: () => void
}

export function TareaDelegarModal({ tareaId, onClose }: TareaDelegarModalProps) {
  const mutation = useDelegarTarea()
  const [nuevoAsignadoId, setNuevoAsignadoId] = useState('')

  const handleDelegar = () => {
    if (!nuevoAsignadoId) return
    mutation.mutate(
      { tarea_id: tareaId, nuevo_asignado_id: nuevoAsignadoId },
      { onSuccess: onClose },
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h3 className="mb-4 text-base font-semibold text-gray-900">Delegar Tarea</h3>
        <div className="mb-4">
          <label className="text-sm font-medium text-gray-700">Nuevo responsable (ID)</label>
          <input
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            value={nuevoAsignadoId}
            onChange={(e) => setNuevoAsignadoId(e.target.value)}
            placeholder="ID del usuario"
            autoFocus
          />
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button loading={mutation.isPending} onClick={handleDelegar}>
            Delegar
          </Button>
        </div>
      </div>
    </div>
  )
}
