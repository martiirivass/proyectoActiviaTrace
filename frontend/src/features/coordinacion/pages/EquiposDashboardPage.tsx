import { useState } from 'react'
import { MisEquiposPage } from '@/features/coordinacion/pages/MisEquiposPage'
import { AsignacionesPage } from '@/features/coordinacion/pages/AsignacionesPage'
import { AsignacionMasivaPage } from '@/features/coordinacion/pages/AsignacionMasivaPage'
import { ClonarEquipoPage } from '@/features/coordinacion/pages/ClonarEquipoPage'
import { VigenciaEquipoPage } from '@/features/coordinacion/pages/VigenciaEquipoPage'

type TabId = 'mis-equipos' | 'asignaciones' | 'asignacion-masiva' | 'clonar' | 'vigencia'

const tabs: { id: TabId; label: string }[] = [
  { id: 'mis-equipos', label: 'Mis Equipos' },
  { id: 'asignaciones', label: 'Asignaciones' },
  { id: 'asignacion-masiva', label: 'Asignación Masiva' },
  { id: 'clonar', label: 'Clonar Equipo' },
  { id: 'vigencia', label: 'Vigencia' },
]

export default function EquiposDashboardPage() {
  const [activeTab, setActiveTab] = useState<TabId>('mis-equipos')

  return (
    <div>
      <h2 className="mb-4 text-lg font-semibold text-gray-900">
        Gestión de Equipos Docentes
      </h2>
      <div className="mb-6 flex gap-1 border-b border-gray-200">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {activeTab === 'mis-equipos' && <MisEquiposPage />}
      {activeTab === 'asignaciones' && <AsignacionesPage />}
      {activeTab === 'asignacion-masiva' && <AsignacionMasivaPage />}
      {activeTab === 'clonar' && <ClonarEquipoPage />}
      {activeTab === 'vigencia' && <VigenciaEquipoPage />}
    </div>
  )
}
