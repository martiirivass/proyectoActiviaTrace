type TabSegmento = 'general' | 'nexo' | 'factura'

interface TabsSegmentacionProps {
  activeTab: TabSegmento
  onChange: (tab: TabSegmento) => void
}

const tabs: { key: TabSegmento; label: string }[] = [
  { key: 'general', label: 'General' },
  { key: 'nexo', label: 'NEXO' },
  { key: 'factura', label: 'Factura' },
]

export function TabsSegmentacion({ activeTab, onChange }: TabsSegmentacionProps) {
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

export type { TabSegmento }
