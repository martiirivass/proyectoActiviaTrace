import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useEffect } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import type { Dictado, DictadoFormData } from '@/features/admin/types'

const schema = z.object({
  materia_id: z.string().min(1, 'La materia es requerida'),
  carrera_id: z.string().min(1, 'La carrera es requerida'),
  cohorte_id: z.string().min(1, 'La cohorte es requerida'),
  nombre: z.string().min(1, 'El nombre es requerido'),
})

interface DictadoFormModalProps {
  item?: Dictado | null
  onSave: (data: DictadoFormData) => void
  onClose: () => void
  loading: boolean
}

export function DictadoFormModal({ item, onSave, onClose, loading }: DictadoFormModalProps) {
  const { register, handleSubmit, formState: { errors }, reset } = useForm<DictadoFormData>({
    resolver: zodResolver(schema),
    defaultValues: { materia_id: '', carrera_id: '', cohorte_id: '', nombre: '' },
  })

  useEffect(() => {
    if (item) reset({ materia_id: item.materia_id, carrera_id: item.carrera_id, cohorte_id: item.cohorte_id, nombre: item.nombre })
  }, [item, reset])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-gray-900">
          {item ? 'Editar Dictado' : 'Nuevo Dictado'}
        </h3>
        <form onSubmit={handleSubmit(onSave)} className="mt-4 space-y-4">
          <Input label="ID Materia" error={errors.materia_id?.message} {...register('materia_id')} />
          <Input label="ID Carrera" error={errors.carrera_id?.message} {...register('carrera_id')} />
          <Input label="ID Cohorte" error={errors.cohorte_id?.message} {...register('cohorte_id')} />
          <Input label="Nombre" error={errors.nombre?.message} {...register('nombre')} />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={onClose} disabled={loading}>Cancelar</Button>
            <Button type="submit" loading={loading}>{item ? 'Guardar Cambios' : 'Crear'}</Button>
          </div>
        </form>
      </div>
    </div>
  )
}
