type TabEntidad = 'carreras' | 'cohortes' | 'materias' | 'dictados'

interface TabsEntidadesProps {
  activeTab: TabEntidad
  onChange: (tab: TabEntidad) => void
}

const tabs: { key: TabEntidad; label: string }[] = [
  { key: 'carreras', label: 'Carreras' },
  { key: 'cohortes', label: 'Cohortes' },
  { key: 'materias', label: 'Materias' },
  { key: 'dictados', label: 'Dictados' },
]

export function TabsEntidades({ activeTab, onChange }: TabsEntidadesProps) {
  return (
    <div className="flex border-b border-gray-200">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          type="button"
          onClick={() => onChange(tab.key)}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === tab.key
              ? 'border-b-2 border-blue-600 text-blue-700'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}

export type { TabEntidad }
