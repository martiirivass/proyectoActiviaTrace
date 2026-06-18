import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useEffect } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import type { Materia, MateriaFormData } from '@/features/admin/types'

const schema = z.object({
  codigo: z.string().min(1, 'El código es requerido'),
  nombre: z.string().min(1, 'El nombre es requerido'),
})

interface MateriaFormModalProps {
  item?: Materia | null
  onSave: (data: MateriaFormData) => void
  onClose: () => void
  loading: boolean
}

export function MateriaFormModal({ item, onSave, onClose, loading }: MateriaFormModalProps) {
  const { register, handleSubmit, formState: { errors }, reset } = useForm<MateriaFormData>({
    resolver: zodResolver(schema),
    defaultValues: { codigo: '', nombre: '' },
  })

  useEffect(() => {
    if (item) reset({ codigo: item.codigo, nombre: item.nombre })
  }, [item, reset])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-gray-900">
          {item ? 'Editar Materia' : 'Nueva Materia'}
        </h3>
        <form onSubmit={handleSubmit(onSave)} className="mt-4 space-y-4">
          <Input label="Código" error={errors.codigo?.message} {...register('codigo')} />
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
