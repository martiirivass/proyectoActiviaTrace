import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/shared/components/ui/Button'
import type { Alumno } from '@/features/academico/types'

const redaccionSchema = z.object({
  asunto: z.string().min(1, 'El asunto es requerido'),
  cuerpo: z.string().min(1, 'El cuerpo es requerido'),
})

type RedaccionFormData = z.infer<typeof redaccionSchema>

interface FormularioRedaccionProps {
  alumnos: Alumno[]
  selectedIds: string[]
  onSelectionChange: (ids: string[]) => void
  onPreview: (data: RedaccionFormData & { destinatarios: string[] }) => void
  isLoading: boolean
}

export function FormularioRedaccion({
  alumnos,
  selectedIds,
  onSelectionChange,
  onPreview,
  isLoading,
}: FormularioRedaccionProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RedaccionFormData>({
    resolver: zodResolver(redaccionSchema),
  })

  const onSubmit = (data: RedaccionFormData) => {
    onPreview({ ...data, destinatarios: selectedIds })
  }

  const toggleAlumno = (id: string) => {
    if (selectedIds.includes(id)) {
      onSelectionChange(selectedIds.filter((a) => a !== id))
    } else {
      onSelectionChange([...selectedIds, id])
    }
  }

  const toggleAll = () => {
    if (selectedIds.length === alumnos.length) {
      onSelectionChange([])
    } else {
      onSelectionChange(alumnos.map((a) => a.id))
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">
          Asunto
        </label>
        <input
          {...register('asunto')}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Asunto de la comunicación"
        />
        {errors.asunto && (
          <p className="mt-1 text-sm text-red-600">{errors.asunto.message}</p>
        )}
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">
          Cuerpo
        </label>
        <textarea
          {...register('cuerpo')}
          rows={5}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Contenido de la comunicación"
        />
        {errors.cuerpo && (
          <p className="mt-1 text-sm text-red-600">{errors.cuerpo.message}</p>
        )}
      </div>

      <div>
        <div className="mb-2 flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">
            Destinatarios ({selectedIds.length} seleccionados)
          </label>
          <button
            type="button"
            onClick={toggleAll}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            {selectedIds.length === alumnos.length
              ? 'Deseleccionar todos'
              : 'Seleccionar todos'}
          </button>
        </div>
        {alumnos.length === 0 ? (
          <p className="text-sm text-gray-500">
            No hay alumnos disponibles para esta comisión.
          </p>
        ) : (
          <div className="max-h-48 overflow-y-auto rounded-md border border-gray-200">
            {alumnos.map((alumno) => (
              <label
                key={alumno.id}
                className="flex cursor-pointer items-center gap-2 border-b border-gray-100 px-3 py-2 text-sm last:border-0 hover:bg-gray-50"
              >
                <input
                  type="checkbox"
                  checked={selectedIds.includes(alumno.id)}
                  onChange={() => toggleAlumno(alumno.id)}
                  className="h-4 w-4 rounded border-gray-300"
                />
                <span className="text-gray-700">
                  {alumno.apellido}, {alumno.nombre}
                </span>
                <span className="text-xs text-gray-400">{alumno.email}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      <Button
        type="submit"
        loading={isLoading}
        disabled={selectedIds.length === 0}
      >
        Previsualizar
      </Button>
    </form>
  )
}
