import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Card } from '@/shared/components/ui/Card'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Button } from '@/shared/components/ui/Button'
import { useAvisos, useDeleteAviso } from '@/features/coordinacion/hooks/useAvisos'
import { AckStatsDisplay } from '@/features/coordinacion/components/AckStatsDisplay'

export default function AvisosPage() {
  const { data: avisos, isLoading } = useAvisos()
  const deleteMutation = useDeleteAviso()
  const [expandedId, setExpandedId] = useState<string | null>(null)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Avisos del Sistema</h2>
        <Link to="/dashboard/coordinacion/avisos/nuevo">
          <Button size="sm">Nuevo Aviso</Button>
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
                <th className="pb-2 pr-4 font-medium">Título</th>
                <th className="pb-2 pr-4 font-medium">Alcance</th>
                <th className="pb-2 pr-4 font-medium">Severidad</th>
                <th className="pb-2 pr-4 font-medium">Vigencia</th>
                <th className="pb-2 pr-4 font-medium">ACK Rate</th>
                <th className="pb-2 font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {avisos?.map((aviso) => (
                <tr key={aviso.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 pr-4 font-medium text-gray-900">{aviso.titulo}</td>
                  <td className="py-2 pr-4">{aviso.alcance}</td>
                  <td className="py-2 pr-4">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                        aviso.severidad === 'critica'
                          ? 'bg-red-100 text-red-700'
                          : aviso.severidad === 'alta'
                            ? 'bg-orange-100 text-orange-700'
                            : aviso.severidad === 'media'
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      {aviso.severidad}
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-xs text-gray-500">
                    {aviso.vigencia_inicio} — {aviso.vigencia_fin}
                  </td>
                  <td className="py-2 pr-4">
                    <AckStatsDisplay avisoId={aviso.id} />
                  </td>
                  <td className="py-2">
                    <div className="flex gap-2">
                      <button
                        type="button"
                        className="text-blue-600 hover:text-blue-800"
                        onClick={() => setExpandedId(expandedId === aviso.id ? null : aviso.id)}
                      >
                        {expandedId === aviso.id ? 'Ocultar' : 'Detalle'}
                      </button>
                      <Link
                        to={`/dashboard/coordinacion/avisos/${aviso.id}/editar`}
                        className="text-gray-600 hover:text-gray-800"
                      >
                        Editar
                      </Link>
                      <button
                        type="button"
                        className="text-red-600 hover:text-red-800"
                        onClick={() => {
                          if (window.confirm('¿Eliminar este aviso?')) {
                            deleteMutation.mutate(aviso.id)
                          }
                        }}
                      >
                        Eliminar
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {(!avisos || avisos.length === 0) && (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-gray-500">
                    No hay avisos publicados
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </Card>
      )}

      {expandedId && avisos && (
        <Card header={<span className="font-medium text-gray-900">Detalle del Aviso</span>}>
          <pre className="whitespace-pre-wrap text-sm text-gray-700">
            {avisos.find((a) => a.id === expandedId)?.contenido}
          </pre>
        </Card>
      )}
    </div>
  )
}
