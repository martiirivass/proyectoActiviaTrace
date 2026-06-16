import { useState } from 'react'
import { useDictados, useDeleteDictado } from '@/features/admin/hooks/useEstructura'
import type { Dictado } from '@/features/admin/types'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'

interface DictadosTableProps {
  onEdit: (item: Dictado) => void
  onNew: () => void
}

export function DictadosTable({ onEdit, onNew }: DictadosTableProps) {
  const [materiaId, setMateriaId] = useState('')
  const [cohorteId, setCohorteId] = useState('')
  const { data, isLoading, error } = useDictados(materiaId || undefined, cohorteId || undefined)
  const deleteMutation = useDeleteDictado()

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-4">
        <Input label="ID Materia" placeholder="Filtrar" value={materiaId} onChange={(e) => setMateriaId(e.target.value)} />
        <Input label="ID Cohorte" placeholder="Filtrar" value={cohorteId} onChange={(e) => setCohorteId(e.target.value)} />
        <Button onClick={onNew}>Nuevo Dictado</Button>
      </div>

      {isLoading && <div className="flex justify-center py-8"><Spinner /></div>}
      {error && <Alert variant="error" message="Error al cargar dictados" />}

      {!isLoading && !error && (!data || data.length === 0) && (
        <p className="py-8 text-center text-gray-500">No hay registros</p>
      )}

      {!isLoading && !error && data && data.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Materia</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Carrera</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Cohorte</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Nombre Dictado</th>
                <th className="px-4 py-3 text-center font-medium text-gray-600" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">{item.materia_nombre}</td>
                  <td className="px-4 py-3">{item.carrera_nombre}</td>
                  <td className="px-4 py-3">{item.cohorte_nombre}</td>
                  <td className="px-4 py-3">{item.nombre}</td>
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
