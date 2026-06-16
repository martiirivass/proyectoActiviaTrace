import { useMaterias, useDeleteMateria } from '@/features/admin/hooks/useEstructura'
import type { Materia } from '@/features/admin/types'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import { Button } from '@/shared/components/ui/Button'

interface MateriasTableProps {
  onEdit: (item: Materia) => void
  onNew: () => void
}

export function MateriasTable({ onEdit, onNew }: MateriasTableProps) {
  const { data, isLoading, error } = useMaterias()
  const deleteMutation = useDeleteMateria()

  if (isLoading) return <div className="flex justify-center py-8"><Spinner /></div>
  if (error) return <Alert variant="error" message="Error al cargar materias" />

  const items = data ?? []

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={onNew}>Nueva Materia</Button>
      </div>

      {items.length === 0 ? (
        <p className="py-8 text-center text-gray-500">No hay registros</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Código</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Nombre</th>
                <th className="px-4 py-3 text-center font-medium text-gray-600">Estado</th>
                <th className="px-4 py-3 text-center font-medium text-gray-600" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs">{item.codigo}</td>
                  <td className="px-4 py-3">{item.nombre}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                      item.activo ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {item.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex justify-center gap-2">
                      <Button variant="ghost" size="sm" onClick={() => onEdit(item)}>Editar</Button>
                      <Button variant="ghost" size="sm" onClick={() => deleteMutation.mutate(item.id)}>Eliminar</Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
