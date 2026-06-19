import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useEffect } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import type { Cohorte, CohorteFormData } from '@/features/admin/types'

const schema = z.object({
  carrera_id: z.string().min(1, 'La carrera es requerida'),
  nombre: z.string().min(1, 'El nombre es requerido'),
  anio: z.number().int().positive('El año debe ser positivo'),
})

interface CohorteFormModalProps {
  item?: Cohorte | null
  onSave: (data: CohorteFormData) => void
  onClose: () => void
  loading: boolean
}

export function CohorteFormModal({ item, onSave, onClose, loading }: CohorteFormModalProps) {
  const { register, handleSubmit, formState: { errors }, reset } = useForm<CohorteFormData>({
    resolver: zodResolver(schema),
    defaultValues: { carrera_id: '', nombre: '', anio: new Date().getFullYear() },
  })

  useEffect(() => {
    if (item) reset({ carrera_id: item.carrera_id, nombre: item.nombre, anio: item.anio })
  }, [item, reset])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-gray-900">
          {item ? 'Editar Cohorte' : 'Nueva Cohorte'}
        </h3>
        <form onSubmit={handleSubmit(onSave)} className="mt-4 space-y-4">
          <Input label="ID Carrera" error={errors.carrera_id?.message} {...register('carrera_id')} />
          <Input label="Nombre" error={errors.nombre?.message} {...register('nombre')} />
          <Input label="Año" type="number" error={errors.anio?.message} {...register('anio', { valueAsNumber: true })} />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={onClose} disabled={loading}>Cancelar</Button>
            <Button type="submit" loading={loading}>{item ? 'Guardar Cambios' : 'Crear'}</Button>
          </div>
        </form>
      </div>
    </div>
  )
}
