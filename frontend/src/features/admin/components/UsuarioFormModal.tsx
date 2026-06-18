import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useEffect } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import type { Usuario, UsuarioFormData } from '@/features/admin/types'

const createSchema = z.object({
  email: z.string().email('Email inválido'),
  nombre: z.string().min(1, 'El nombre es requerido'),
  apellido: z.string().min(1, 'El apellido es requerido'),
  dni: z.string().min(1, 'El DNI es requerido'),
  password: z.string().min(6, 'La contraseña debe tener al menos 6 caracteres'),
  cuil: z.string().optional(),
  cbu: z.string().optional(),
  alias_cbu: z.string().optional(),
  banco: z.string().optional(),
  regional: z.string().optional(),
  legajo: z.string().optional(),
  legajo_profesional: z.string().optional(),
  facturador: z.boolean(),
})

const editSchema = z.object({
  email: z.string().email('Email inválido'),
  nombre: z.string().min(1, 'El nombre es requerido'),
  apellido: z.string().min(1, 'El apellido es requerido'),
  dni: z.string().min(1, 'El DNI es requerido'),
  password: z.string().optional(),
  cuil: z.string().optional(),
  cbu: z.string().optional(),
  alias_cbu: z.string().optional(),
  banco: z.string().optional(),
  regional: z.string().optional(),
  legajo: z.string().optional(),
  legajo_profesional: z.string().optional(),
  facturador: z.boolean(),
})

interface UsuarioFormModalProps {
  item?: Usuario | null
  onSave: (data: UsuarioFormData) => void
  onClose: () => void
  loading: boolean
}

export function UsuarioFormModal({ item, onSave, onClose, loading }: UsuarioFormModalProps) {
  const isEdit = !!item
  const { register, handleSubmit, formState: { errors }, reset } = useForm<UsuarioFormData>({
    resolver: zodResolver(isEdit ? editSchema : createSchema),
    defaultValues: {
      email: '',
      nombre: '',
      apellido: '',
      dni: '',
      password: '',
      cuil: '',
      cbu: '',
      alias_cbu: '',
      banco: '',
      regional: '',
      legajo: '',
      legajo_profesional: '',
      facturador: false,
    },
  })

  useEffect(() => {
    if (item) {
      reset({
        email: item.email,
        nombre: item.nombre,
        apellido: item.apellido,
        dni: item.dni,
        password: '',
        cuil: item.cuil ?? '',
        cbu: item.cbu ?? '',
        alias_cbu: item.alias_cbu ?? '',
        banco: item.banco ?? '',
        regional: item.regional ?? '',
        legajo: item.legajo ?? '',
        legajo_profesional: item.legajo_profesional ?? '',
        facturador: item.facturador,
      })
    }
  }, [item, reset])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-gray-900">
          {item ? 'Editar Usuario' : 'Nuevo Usuario'}
        </h3>

        <form onSubmit={handleSubmit(onSave)} className="mt-4 space-y-4">
          <Input label="Email" type="email" error={errors.email?.message} {...register('email')} />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Nombre" error={errors.nombre?.message} {...register('nombre')} />
            <Input label="Apellido" error={errors.apellido?.message} {...register('apellido')} />
          </div>
          <Input label="DNI" error={errors.dni?.message} {...register('dni')} />
          <Input
            label={isEdit ? 'Password (dejar vacío para mantener)' : 'Password'}
            type="password"
            error={errors.password?.message}
            {...register('password')}
          />

          <hr className="border-gray-200" />
          <p className="text-sm font-medium text-gray-700">Datos Personales (PII)</p>

          <div className="grid grid-cols-2 gap-4">
            <Input label="CUIL" {...register('cuil')} />
            <Input label="CBU" {...register('cbu')} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Alias CBU" {...register('alias_cbu')} />
            <Input label="Banco" {...register('banco')} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Regional" {...register('regional')} />
            <Input label="Legajo" {...register('legajo')} />
          </div>
          <Input label="Legajo Profesional" {...register('legajo_profesional')} />

          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" {...register('facturador')} className="rounded border-gray-300 text-blue-600" />
            <span className="font-medium text-gray-700">Facturador</span>
          </label>

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
