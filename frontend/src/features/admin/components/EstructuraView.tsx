import { useState } from 'react'
import { TabsEntidades, type TabEntidad } from './TabsEntidades'
import { CarrerasTable } from './CarrerasTable'
import { CarreraFormModal } from './CarreraFormModal'
import { CohortesTable } from './CohortesTable'
import { CohorteFormModal } from './CohorteFormModal'
import { MateriasTable } from './MateriasTable'
import { MateriaFormModal } from './MateriaFormModal'
import { DictadosTable } from './DictadosTable'
import { DictadoFormModal } from './DictadoFormModal'
import { useCreateCarrera, useUpdateCarrera, useCreateCohorte, useUpdateCohorte, useCreateMateria, useUpdateMateria, useCreateDictado, useUpdateDictado } from '@/features/admin/hooks/useEstructura'
import type { Carrera, Cohorte, Materia, Dictado, CarreraFormData, CohorteFormData, MateriaFormData, DictadoFormData } from '@/features/admin/types'

export function EstructuraView() {
  const [activeTab, setActiveTab] = useState<TabEntidad>('carreras')

  const [editingCarrera, setEditingCarrera] = useState<Carrera | null>(null)
  const [editingCohorte, setEditingCohorte] = useState<Cohorte | null>(null)
  const [editingMateria, setEditingMateria] = useState<Materia | null>(null)
  const [editingDictado, setEditingDictado] = useState<Dictado | null>(null)
  const [showForm, setShowForm] = useState(false)

  const createCarrera = useCreateCarrera()
  const updateCarrera = useUpdateCarrera()
  const createCohorte = useCreateCohorte()
  const updateCohorte = useUpdateCohorte()
  const createMateria = useCreateMateria()
  const updateMateria = useUpdateMateria()
  const createDictado = useCreateDictado()
  const updateDictado = useUpdateDictado()

  const handleSaveCarrera = (data: CarreraFormData) => {
    if (editingCarrera) {
      updateCarrera.mutate({ id: editingCarrera.id, data }, { onSuccess: () => { setShowForm(false); setEditingCarrera(null) } })
    } else {
      createCarrera.mutate(data, { onSuccess: () => setShowForm(false) })
    }
  }

  const handleSaveCohorte = (data: CohorteFormData) => {
    if (editingCohorte) {
      updateCohorte.mutate({ id: editingCohorte.id, data }, { onSuccess: () => { setShowForm(false); setEditingCohorte(null) } })
    } else {
      createCohorte.mutate(data, { onSuccess: () => setShowForm(false) })
    }
  }

  const handleSaveMateria = (data: MateriaFormData) => {
    if (editingMateria) {
      updateMateria.mutate({ id: editingMateria.id, data }, { onSuccess: () => { setShowForm(false); setEditingMateria(null) } })
    } else {
      createMateria.mutate(data, { onSuccess: () => setShowForm(false) })
    }
  }

  const handleSaveDictado = (data: DictadoFormData) => {
    if (editingDictado) {
      updateDictado.mutate({ id: editingDictado.id, data }, { onSuccess: () => { setShowForm(false); setEditingDictado(null) } })
    } else {
      createDictado.mutate(data, { onSuccess: () => setShowForm(false) })
    }
  }

  const loading =
    createCarrera.isPending || updateCarrera.isPending ||
    createCohorte.isPending || updateCohorte.isPending ||
    createMateria.isPending || updateMateria.isPending ||
    createDictado.isPending || updateDictado.isPending

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Estructura Académica</h1>

      <TabsEntidades activeTab={activeTab} onChange={setActiveTab} />

      {activeTab === 'carreras' && (
        <CarrerasTable
          onNew={() => { setEditingCarrera(null); setShowForm(true) }}
          onEdit={(item) => { setEditingCarrera(item); setShowForm(true) }}
        />
      )}

      {activeTab === 'cohortes' && (
        <CohortesTable
          onNew={() => { setEditingCohorte(null); setShowForm(true) }}
          onEdit={(item) => { setEditingCohorte(item); setShowForm(true) }}
        />
      )}

      {activeTab === 'materias' && (
        <MateriasTable
          onNew={() => { setEditingMateria(null); setShowForm(true) }}
          onEdit={(item) => { setEditingMateria(item); setShowForm(true) }}
        />
      )}

      {activeTab === 'dictados' && (
        <DictadosTable
          onNew={() => { setEditingDictado(null); setShowForm(true) }}
          onEdit={(item) => { setEditingDictado(item); setShowForm(true) }}
        />
      )}

      {showForm && activeTab === 'carreras' && (
        <CarreraFormModal
          item={editingCarrera}
          onSave={handleSaveCarrera}
          onClose={() => { setShowForm(false); setEditingCarrera(null) }}
          loading={loading}
        />
      )}

      {showForm && activeTab === 'cohortes' && (
        <CohorteFormModal
          item={editingCohorte}
          onSave={handleSaveCohorte}
          onClose={() => { setShowForm(false); setEditingCohorte(null) }}
          loading={loading}
        />
      )}

      {showForm && activeTab === 'materias' && (
        <MateriaFormModal
          item={editingMateria}
          onSave={handleSaveMateria}
          onClose={() => { setShowForm(false); setEditingMateria(null) }}
          loading={loading}
        />
      )}

      {showForm && activeTab === 'dictados' && (
        <DictadoFormModal
          item={editingDictado}
          onSave={handleSaveDictado}
          onClose={() => { setShowForm(false); setEditingDictado(null) }}
          loading={loading}
        />
      )}
    </div>
  )
}
