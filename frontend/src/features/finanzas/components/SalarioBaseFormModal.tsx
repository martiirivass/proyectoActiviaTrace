import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useEffect } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import type { SalarioBase, SalarioBaseFormData } from '@/features/finanzas/types'

const schema = z.object({
  rol: z.string().min(1, 'El rol es requerido'),
  monto: z.coerce.number().positive('El monto debe ser mayor a 0'),
  desde: z.string().min(1, 'La fecha desde es requerida'),
  hasta: z.string().nullable().optional(),
})

interface SalarioBaseFormModalProps {
  item?: SalarioBase | null
  onSave: (data: SalarioBaseFormData) => void
  onClose: () => void
  loading: boolean
}

export function SalarioBaseFormModal({ item, onSave, onClose, loading }: SalarioBaseFormModalProps) {
  const { register, handleSubmit, formState: { errors }, reset } = useForm<SalarioBaseFormData & { hasta: string | null }>({
    resolver: zodResolver(schema),
    defaultValues: {
      rol: '',
      monto: 0,
      desde: '',
      hasta: null,
    },
  })

  useEffect(() => {
    if (item) {
      reset({
        rol: item.rol,
        monto: item.monto,
        desde: item.desde,
        hasta: item.hasta,
      })
    }
  }, [item, reset])

  const onSubmit = (data: SalarioBaseFormData & { hasta: string | null }) => {
    onSave(data)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-gray-900">
          {item ? 'Editar Salario Base' : 'Nuevo Salario Base'}
        </h3>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-4 space-y-4">
          <Input
            label="Rol"
            placeholder="Ej: TUTOR, PROFESOR"
            error={errors.rol?.message}
            {...register('rol')}
          />
          <Input
            label="Monto"
            type="number"
            step="0.01"
            error={errors.monto?.message}
            {...register('monto')}
          />
          <Input
            label="Desde"
            type="date"
            error={errors.desde?.message}
            {...register('desde')}
          />
          <Input
            label="Hasta (opcional)"
            type="date"
            {...register('hasta')}
          />

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={onClose} disabled={loading}>
              Cancelar
            </Button>
            <Button type="submit" loading={loading}>
              {item ? 'Guardar Cambios' : 'Crear'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
