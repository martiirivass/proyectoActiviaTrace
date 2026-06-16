import { useSalariosPlus, useDeleteSalarioPlus } from '@/features/finanzas/hooks/useGrillaSalarial'
import type { SalarioPlus } from '@/features/finanzas/types'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import { Button } from '@/shared/components/ui/Button'

interface SalarioPlusTableProps {
  onEdit: (item: SalarioPlus) => void
  onNew: () => void
}

export function SalarioPlusTable({ onEdit, onNew }: SalarioPlusTableProps) {
  const { data, isLoading, error } = useSalariosPlus()
  const deleteMutation = useDeleteSalarioPlus()

  if (isLoading) return <div className="flex justify-center py-8"><Spinner /></div>
  if (error) return <Alert variant="error" message="Error al cargar salarios plus" />

  const items = data ?? []

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={onNew}>Nuevo Salario Plus</Button>
      </div>

      {items.length === 0 ? (
        <p className="py-8 text-center text-gray-500">No hay registros</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Grupo</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Rol</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Descripción</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600">Monto</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Desde</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Hasta</th>
                <th className="px-4 py-3 text-center font-medium text-gray-600" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">{item.grupo}</td>
                  <td className="px-4 py-3">{item.rol}</td>
                  <td className="px-4 py-3">{item.descripcion}</td>
                  <td className="px-4 py-3 text-right">${item.monto.toLocaleString()}</td>
                  <td className="px-4 py-3">{item.desde}</td>
                  <td className="px-4 py-3">{item.hasta ?? '—'}</td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex justify-center gap-2">
                      <Button variant="ghost" size="sm" onClick={() => onEdit(item)}>Editar</Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteMutation.mutate(item.id)}
                        loading={deleteMutation.isPending}
                      >
                        Eliminar
                      </Button>
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
