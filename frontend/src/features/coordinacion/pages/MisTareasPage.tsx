import { Link } from 'react-router-dom'
import { Card } from '@/shared/components/ui/Card'
import { Spinner } from '@/shared/components/ui/Spinner'
import { useMisTareas } from '@/features/coordinacion/hooks/useTareas'
import type { TareaEstado } from '@/features/coordinacion/types'

const estadoColors: Record<TareaEstado, string> = {
  pendiente: 'bg-yellow-100 text-yellow-700',
  en_curso: 'bg-blue-100 text-blue-700',
  completada: 'bg-green-100 text-green-700',
  cancelada: 'bg-gray-100 text-gray-600',
}

export default function MisTareasPage() {
  const { data: tareas, isLoading } = useMisTareas()

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Mis Tareas</h2>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : (
        <Card>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-gray-600">
                <th className="pb-2 pr-4 font-medium">Título</th>
                <th className="pb-2 pr-4 font-medium">Asignador</th>
                <th className="pb-2 pr-4 font-medium">Materia</th>
                <th className="pb-2 pr-4 font-medium">Estado</th>
                <th className="pb-2 font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {tareas?.map((t) => (
                <tr key={t.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 pr-4 font-medium text-gray-900">{t.titulo}</td>
                  <td className="py-2 pr-4">{t.asignador_nombre}</td>
                  <td className="py-2 pr-4 text-gray-500">{t.materia_nombre ?? '—'}</td>
                  <td className="py-2 pr-4">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${estadoColors[t.estado as TareaEstado] ?? 'bg-gray-100 text-gray-600'}`}
                    >
                      {t.estado}
                    </span>
                  </td>
                  <td className="py-2">
                    <Link
                      to={`/dashboard/coordinacion/tareas/${t.id}`}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      Ver
                    </Link>
                  </td>
                </tr>
              ))}
              {(!tareas || tareas.length === 0) && (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-gray-500">
                    No tienes tareas asignadas
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  )
}
