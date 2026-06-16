import { useState } from 'react'
import { TabsGrilla, type TabGrilla } from './TabsGrilla'
import { SalarioBaseTable } from './SalarioBaseTable'
import { SalarioBaseFormModal } from './SalarioBaseFormModal'
import { SalarioPlusTable } from './SalarioPlusTable'
import { SalarioPlusFormModal } from './SalarioPlusFormModal'
import { useCreateSalarioBase, useUpdateSalarioBase, useCreateSalarioPlus, useUpdateSalarioPlus } from '@/features/finanzas/hooks/useGrillaSalarial'
import type { SalarioBase, SalarioPlus, SalarioBaseFormData, SalarioPlusFormData } from '@/features/finanzas/types'

export function GrillaSalarialView() {
  const [activeTab, setActiveTab] = useState<TabGrilla>('base')
  const [editingBase, setEditingBase] = useState<SalarioBase | null>(null)
  const [editingPlus, setEditingPlus] = useState<SalarioPlus | null>(null)
  const [showBaseForm, setShowBaseForm] = useState(false)
  const [showPlusForm, setShowPlusForm] = useState(false)

  const createBase = useCreateSalarioBase()
  const updateBase = useUpdateSalarioBase()
  const createPlus = useCreateSalarioPlus()
  const updatePlus = useUpdateSalarioPlus()

  const handleSaveBase = (data: SalarioBaseFormData) => {
    if (editingBase) {
      updateBase.mutate({ id: editingBase.id, data }, { onSuccess: () => { setShowBaseForm(false); setEditingBase(null) } })
    } else {
      createBase.mutate(data, { onSuccess: () => setShowBaseForm(false) })
    }
  }

  const handleSavePlus = (data: SalarioPlusFormData) => {
    if (editingPlus) {
      updatePlus.mutate({ id: editingPlus.id, data }, { onSuccess: () => { setShowPlusForm(false); setEditingPlus(null) } })
    } else {
      createPlus.mutate(data, { onSuccess: () => setShowPlusForm(false) })
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Grilla Salarial</h1>

      <TabsGrilla activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === 'base' && (
        <SalarioBaseTable
          onNew={() => { setEditingBase(null); setShowBaseForm(true) }}
          onEdit={(item) => { setEditingBase(item); setShowBaseForm(true) }}
        />
      )}

      {activeTab === 'plus' && (
        <SalarioPlusTable
          onNew={() => { setEditingPlus(null); setShowPlusForm(true) }}
          onEdit={(item) => { setEditingPlus(item); setShowPlusForm(true) }}
        />
      )}

      {showBaseForm && (
        <SalarioBaseFormModal
          item={editingBase}
          onSave={handleSaveBase}
          onClose={() => { setShowBaseForm(false); setEditingBase(null) }}
          loading={createBase.isPending || updateBase.isPending}
        />
      )}

      {showPlusForm && (
        <SalarioPlusFormModal
          item={editingPlus}
          onSave={handleSavePlus}
          onClose={() => { setShowPlusForm(false); setEditingPlus(null) }}
          loading={createPlus.isPending || updatePlus.isPending}
        />
      )}
    </div>
  )
}
