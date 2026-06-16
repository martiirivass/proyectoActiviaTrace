import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useEffect } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import type { SalarioPlus, SalarioPlusFormData } from '@/features/finanzas/types'

const schema = z.object({
  grupo: z.string().min(1, 'El grupo es requerido'),
  rol: z.string().min(1, 'El rol es requerido'),
  descripcion: z.string().min(1, 'La descripción es requerida'),
  monto: z.coerce.number().positive('El monto debe ser mayor a 0'),
  desde: z.string().min(1, 'La fecha desde es requerida'),
  hasta: z.string().nullable().optional(),
})

interface SalarioPlusFormModalProps {
  item?: SalarioPlus | null
  onSave: (data: SalarioPlusFormData) => void
  onClose: () => void
  loading: boolean
}

export function SalarioPlusFormModal({ item, onSave, onClose, loading }: SalarioPlusFormModalProps) {
  const { register, handleSubmit, formState: { errors }, reset } = useForm<SalarioPlusFormData & { hasta: string | null }>({
    resolver: zodResolver(schema),
    defaultValues: {
      grupo: '',
      rol: '',
      descripcion: '',
      monto: 0,
      desde: '',
      hasta: null,
    },
  })

  useEffect(() => {
    if (item) {
      reset({
        grupo: item.grupo,
        rol: item.rol,
        descripcion: item.descripcion,
        monto: item.monto,
        desde: item.desde,
        hasta: item.hasta,
      })
    }
  }, [item, reset])

  const onSubmit = (data: SalarioPlusFormData & { hasta: string | null }) => {
    onSave(data)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-gray-900">
          {item ? 'Editar Salario Plus' : 'Nuevo Salario Plus'}
        </h3>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-4 space-y-4">
          <Input label="Grupo" error={errors.grupo?.message} {...register('grupo')} />
          <Input label="Rol" error={errors.rol?.message} {...register('rol')} />
          <Input label="Descripción" error={errors.descripcion?.message} {...register('descripcion')} />
          <Input label="Monto" type="number" step="0.01" error={errors.monto?.message} {...register('monto')} />
          <Input label="Desde" type="date" error={errors.desde?.message} {...register('desde')} />
          <Input label="Hasta (opcional)" type="date" {...register('hasta')} />

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
