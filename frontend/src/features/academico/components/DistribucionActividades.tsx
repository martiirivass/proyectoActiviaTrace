import type { DistribucionActividad } from '@/features/academico/types'

interface DistribucionActividadesProps {
  distribucion: DistribucionActividad[]
}

function BarraAprobacion({
  aprobados,
  desaprobados,
}: {
  aprobados: number
  desaprobados: number
}) {
  const total = aprobados + desaprobados
  if (total === 0) return <span className="text-xs text-gray-400">Sin datos</span>
  const pctAprobados = (aprobados / total) * 100

  return (
    <div className="flex items-center gap-2">
      <div className="h-4 w-32 overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-l-full bg-green-500"
          style={{ width: `${pctAprobados}%` }}
        />
        <div
          className="h-full rounded-r-full bg-red-500"
          style={{
            width: `${100 - pctAprobados}%`,
            marginTop: '-1rem',
            marginLeft: `${pctAprobados}%`,
          }}
        />
      </div>
      <span className="text-xs text-gray-600">
        {aprobados}/{total}
      </span>
    </div>
  )
}

export function DistribucionActividades({
  distribucion,
}: DistribucionActividadesProps) {
  if (!distribucion || distribucion.length === 0) {
    return (
      <p className="text-sm text-gray-500">
        No hay distribución de actividades disponible.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              Actividad
            </th>
            <th className="px-4 py-3 text-center font-medium text-gray-600">
              Alumnos con nota
            </th>
            <th className="px-4 py-3 text-center font-medium text-gray-600">
              Promedio
            </th>
            <th className="px-4 py-3 text-center font-medium text-gray-600">
              Aprobados
            </th>
            <th className="px-4 py-3 text-center font-medium text-gray-600">
              Desaprobados
            </th>
            <th className="px-4 py-3 text-left font-medium text-gray-600">
              Distribución
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {distribucion.map((act, idx) => (
            <tr key={idx} className="hover:bg-gray-50">
              <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-900">
                {act.nombre}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-center text-gray-700">
                {act.alumnos_con_nota}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-center text-gray-700">
                {act.promedio !== null ? act.promedio.toFixed(1) : '—'}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-center text-green-600">
                {act.aprobados}
              </td>
              <td className="whitespace-nowrap px-4 py-3 text-center text-red-600">
                {act.desaprobados}
              </td>
              <td className="px-4 py-3">
                <BarraAprobacion
                  aprobados={act.aprobados}
                  desaprobados={act.desaprobados}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
