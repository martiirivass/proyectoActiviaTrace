type TabGrilla = 'base' | 'plus'

interface TabsGrillaProps {
  activeTab: TabGrilla
  onChange: (tab: TabGrilla) => void
}

export function TabsGrilla({ activeTab, onChange }: TabsGrillaProps) {
  return (
    <div className="flex border-b border-gray-200">
      <button
        type="button"
        onClick={() => onChange('base')}
        className={`px-4 py-2 text-sm font-medium transition-colors ${
          activeTab === 'base'
            ? 'border-b-2 border-blue-600 text-blue-700'
            : 'text-gray-500 hover:text-gray-700'
        }`}
      >
        Salario Base
      </button>
      <button
        type="button"
        onClick={() => onChange('plus')}
        className={`px-4 py-2 text-sm font-medium transition-colors ${
          activeTab === 'plus'
            ? 'border-b-2 border-blue-600 text-blue-700'
            : 'text-gray-500 hover:text-gray-700'
        }`}
      >
        Salario Plus
      </button>
    </div>
  )
}

export type { TabGrilla }
