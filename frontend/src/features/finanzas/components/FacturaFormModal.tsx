import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useEffect } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import type { Factura, FacturaFormData } from '@/features/finanzas/types'

const schema = z.object({
  docente_id: z.string().min(1, 'El docente es requerido'),
  periodo: z.string().regex(/^\d{4}-(0[1-9]|1[0-2])$/, 'Formato de período inválido (AAAA-MM)'),
  detalle: z.string().min(1, 'El detalle es requerido'),
  referencia_archivo: z.string().optional(),
  tamano_kb: z.coerce.number().optional(),
  materia_id: z.string().optional(),
  comision: z.string().optional(),
}).refine(
  (data) => !data.materia_id || data.comision,
  { message: 'Debe seleccionar una comisión si especifica una materia', path: ['comision'] },
)

interface FacturaFormModalProps {
  item?: Factura | null
  onSave: (data: FacturaFormData) => void
  onClose: () => void
  loading: boolean
}

export function FacturaFormModal({ item, onSave, onClose, loading }: FacturaFormModalProps) {
  const { register, handleSubmit, formState: { errors }, reset, watch } = useForm<FacturaFormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      docente_id: '',
      periodo: '',
      detalle: '',
      referencia_archivo: '',
      tamano_kb: undefined,
      materia_id: '',
      comision: '',
    },
  })

  const materiaId = watch('materia_id')

  useEffect(() => {
    if (item) {
      reset({
        docente_id: item.docente_id,
        periodo: item.periodo,
        detalle: item.detalle,
        referencia_archivo: item.referencia_archivo ?? '',
        tamano_kb: item.tamano_kb,
        materia_id: item.materia_id ?? '',
        comision: item.comision ?? '',
      })
    }
  }, [item, reset])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
        <h3 className="text-lg font-semibold text-gray-900">
          {item ? 'Editar Factura' : 'Nueva Factura'}
        </h3>

        <form onSubmit={handleSubmit(onSave)} className="mt-4 space-y-4">
          <Input label="ID Docente" error={errors.docente_id?.message} {...register('docente_id')} />
          <Input label="Período (AAAA-MM)" placeholder="2026-06" error={errors.periodo?.message} {...register('periodo')} />
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-gray-700">Detalle</label>
            <textarea
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-base transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              {...register('detalle')}
            />
            {errors.detalle && <p className="text-sm text-red-600">{errors.detalle.message}</p>}
          </div>
          <Input label="Referencia Archivo (opcional)" {...register('referencia_archivo')} />
          <Input label="Tamaño KB (opcional)" type="number" {...register('tamano_kb')} />
          <Input label="ID Materia (opcional)" {...register('materia_id')} />

          {materiaId && (
            <Input
              label="Comisión (requerido si hay materia)"
              error={errors.comision?.message}
              {...register('comision')}
            />
          )}

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
