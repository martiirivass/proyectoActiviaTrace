import { Link } from 'react-router-dom'
import { Card } from '@/shared/components/ui/Card'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Button } from '@/shared/components/ui/Button'
import { useConvocatorias, useDeleteConvocatoria } from '@/features/coordinacion/hooks/useColoquios'

export default function ConvocatoriasListPage() {
  const { data: convocatorias, isLoading } = useConvocatorias()
  const deleteMutation = useDeleteConvocatoria()

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Convocatorias</h2>
        <Link to="/dashboard/coordinacion/coloquios/convocatorias/nueva">
          <Button size="sm">Nueva Convocatoria</Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : (
        <Card>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-gray-600">
                <th className="pb-2 pr-4 font-medium">Materia</th>
                <th className="pb-2 pr-4 font-medium">Instancia</th>
                <th className="pb-2 pr-4 font-medium">Días</th>
                <th className="pb-2 pr-4 font-medium">Cupos</th>
                <th className="pb-2 pr-4 font-medium">Convocados</th>
                <th className="pb-2 pr-4 font-medium">Reservas</th>
                <th className="pb-2 pr-4 font-medium">Cupos Libres</th>
                <th className="pb-2 font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {convocatorias?.map((c) => (
                <tr key={c.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 pr-4">{c.materia_nombre}</td>
                  <td className="py-2 pr-4">{c.instancia}</td>
                  <td className="py-2 pr-4">{c.days.join(', ')}</td>
                  <td className="py-2 pr-4">{c.cupos}</td>
                  <td className="py-2 pr-4">{c.convocados}</td>
                  <td className="py-2 pr-4">{c.reservas_activas}</td>
                  <td className="py-2 pr-4">{c.cupos_libres}</td>
                  <td className="py-2">
                    <div className="flex gap-2">
                      <Link
                        to={`/dashboard/coordinacion/coloquios/convocatorias/${c.id}/editar`}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        Editar
                      </Link>
                      <button
                        type="button"
                        className="text-red-600 hover:text-red-800"
                        onClick={() => {
                          if (window.confirm('¿Eliminar esta convocatoria?')) {
                            deleteMutation.mutate(c.id)
                          }
                        }}
                      >
                        Eliminar
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {(!convocatorias || convocatorias.length === 0) && (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-gray-500">
                    No hay convocatorias registradas
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
