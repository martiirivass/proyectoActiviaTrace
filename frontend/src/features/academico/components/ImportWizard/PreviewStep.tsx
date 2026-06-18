import { useState } from 'react'
import type { CalificacionPreview } from '@/features/academico/types'

interface PreviewStepProps {
  preview: CalificacionPreview
  selectedActividades: string[]
  onSelectionChange: (actividades: string[]) => void
}

export function PreviewStep({
  preview,
  selectedActividades,
  onSelectionChange,
}: PreviewStepProps) {
  const allSelected = selectedActividades.length === preview.actividades_detectadas.length

  const toggleAll = () => {
    if (allSelected) {
      onSelectionChange([])
    } else {
      onSelectionChange(preview.actividades_detectadas.map((a) => a.id))
    }
  }

  const toggleActividad = (id: string) => {
    if (selectedActividades.includes(id)) {
      onSelectionChange(selectedActividades.filter((a) => a !== id))
    } else {
      onSelectionChange([...selectedActividades, id])
    }
  }

  if (preview.actividades_detectadas.length === 0) {
    return (
      <div className="rounded-md bg-yellow-50 p-4 text-sm text-yellow-800">
        No se detectaron actividades en el archivo.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
          <input
            type="checkbox"
            checked={allSelected}
            onChange={toggleAll}
            className="h-4 w-4 rounded border-gray-300"
          />
          {allSelected ? 'Deseleccionar todas' : 'Seleccionar todas'}
        </label>
        <span className="text-sm text-gray-500">
          ({selectedActividades.length} de {preview.actividades_detectadas.length} seleccionadas)
        </span>
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200 text-sm">
          <thead className="bg-gray-50">
            <tr>
              {preview.metadatos_columnas.map((col) => (
                <th
                  key={col}
                  className="whitespace-nowrap px-4 py-2 text-left font-medium text-gray-600"
                >
                  {col}
                </th>
              ))}
              {preview.actividades_detectadas.map((act) => (
                <th
                  key={act.id}
                  className="whitespace-nowrap px-4 py-2 text-center font-medium text-gray-600"
                >
                  <label className="flex cursor-pointer items-center justify-center gap-1">
                    <input
                      type="checkbox"
                      checked={selectedActividades.includes(act.id)}
                      onChange={() => toggleActividad(act.id)}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <span className="truncate max-w-[120px]" title={act.nombre}>
                      {act.nombre}
                    </span>
                  </label>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {preview.alumnos.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                {preview.metadatos_columnas.map((col) => (
                  <td
                    key={col}
                    className="whitespace-nowrap px-4 py-2 text-gray-700"
                  >
                    {(row.alumno as Record<string, string>)[col] ?? '-'}
                  </td>
                ))}
                {preview.actividades_detectadas.map((act) => (
                  <td
                    key={act.id}
                    className="whitespace-nowrap px-4 py-2 text-center text-gray-700"
                  >
                    {row.valores[act.nombre] ?? '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
