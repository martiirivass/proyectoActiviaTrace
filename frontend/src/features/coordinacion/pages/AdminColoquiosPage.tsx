import { useState } from 'react'
import ColoquiosPage from '@/features/coordinacion/pages/ColoquiosPage'
import ConvocatoriasListPage from '@/features/coordinacion/pages/ConvocatoriasListPage'
import { Card } from '@/shared/components/ui/Card'

type SubSection = 'metricas' | 'convocatorias' | 'resultados' | 'reservas'

const sections: { id: SubSection; label: string }[] = [
  { id: 'metricas', label: 'Métricas' },
  { id: 'convocatorias', label: 'Convocatorias' },
  { id: 'resultados', label: 'Resultados' },
  { id: 'reservas', label: 'Agenda Reservas' },
]

export default function AdminColoquiosPage() {
  const [activeSection, setActiveSection] = useState<SubSection>('metricas')

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Administración de Coloquios</h2>

      <div className="flex gap-1 border-b border-gray-200">
        {sections.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setActiveSection(s.id)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeSection === s.id
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {activeSection === 'metricas' && <ColoquiosPage />}
      {activeSection === 'convocatorias' && <ConvocatoriasListPage />}
      {activeSection === 'resultados' && (
        <Card>
          <p className="text-sm text-gray-500">
            Resultados consolidados por convocatoria — próximamente
          </p>
        </Card>
      )}
      {activeSection === 'reservas' && (
        <Card>
          <p className="text-sm text-gray-500">
            Agenda de reservas activas — próximamente
          </p>
        </Card>
      )}
    </div>
  )
}
