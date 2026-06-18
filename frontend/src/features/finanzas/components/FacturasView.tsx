import { useState, useCallback } from 'react'
import { FiltrosFacturas } from './FiltrosFacturas'
import { FacturasTable } from './FacturasTable'
import { FacturaFormModal } from './FacturaFormModal'
import { ConfirmAbonarModal } from './ConfirmAbonarModal'
import { ConfirmDeleteModal } from './ConfirmDeleteModal'
import { useFacturas, useCreateFactura, useUpdateFactura, useAbonarFactura, useDeleteFactura } from '@/features/finanzas/hooks/useFacturas'
import type { Factura, FacturaFiltros, FacturaFormData } from '@/features/finanzas/types'
import { Spinner } from '@/shared/components/ui/Spinner'
import { Alert } from '@/shared/components/ui/Alert'
import { Button } from '@/shared/components/ui/Button'

export function FacturasView() {
  const [filtros, setFiltros] = useState<FacturaFiltros>({})
  const { data, isLoading, error } = useFacturas(filtros)
  const createMutation = useCreateFactura()
  const updateMutation = useUpdateFactura()
  const abonarMutation = useAbonarFactura()
  const deleteMutation = useDeleteFactura()

  const [showForm, setShowForm] = useState(false)
  const [editingFactura, setEditingFactura] = useState<Factura | null>(null)
  const [abonandoId, setAbonandoId] = useState<string | null>(null)
  const [abonarError, setAbonarError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleFilter = useCallback((f: FacturaFiltros) => {
    setFiltros(f)
  }, [])

  const handleSave = (formData: FacturaFormData) => {
    if (editingFactura) {
      updateMutation.mutate({ id: editingFactura.id, data: formData }, {
        onSuccess: () => { setShowForm(false); setEditingFactura(null) },
      })
    } else {
      createMutation.mutate(formData, {
        onSuccess: () => { setShowForm(false); setEditingFactura(null) },
      })
    }
  }

  const handleAbonar = useCallback((id: string) => {
    setAbonandoId(id)
    setAbonarError(null)
  }, [])

  const handleConfirmAbonar = useCallback(() => {
    if (!abonandoId) return
    abonarMutation.mutate(abonandoId, {
      onSuccess: () => setAbonandoId(null),
      onError: (err) => {
        const msg = err instanceof Error ? err.message : ''
        if (msg.includes('409') || msg.includes('ya está abonada')) {
          setAbonarError('La factura ya está abonada')
        } else {
          setAbonarError(msg || 'Error al abonar la factura')
        }
      },
    })
  }, [abonandoId, abonarMutation])

  const handleDelete = useCallback((id: string) => {
    setDeletingId(id)
  }, [])

  const handleConfirmDelete = useCallback(() => {
    if (!deletingId) return
    deleteMutation.mutate(deletingId, {
      onSuccess: () => setDeletingId(null),
    })
  }, [deletingId, deleteMutation])

  const items = data ?? []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Facturas</h1>
        <Button onClick={() => { setEditingFactura(null); setShowForm(true) }}>
          Nueva Factura
        </Button>
      </div>

      <FiltrosFacturas onFilter={handleFilter} />

      {isLoading && <div className="flex justify-center py-8"><Spinner /></div>}
      {error && <Alert variant="error" message="Error al cargar facturas" />}

      {!isLoading && !error && (
        <FacturasTable
          items={items}
          onAbonar={handleAbonar}
          onDelete={handleDelete}
          onEdit={(item) => { setEditingFactura(item); setShowForm(true) }}
          abonandoId={abonandoId}
        />
      )}

      {showForm && (
        <FacturaFormModal
          item={editingFactura}
          onSave={handleSave}
          onClose={() => { setShowForm(false); setEditingFactura(null) }}
          loading={createMutation.isPending || updateMutation.isPending}
        />
      )}

      {abonandoId && (
        <ConfirmAbonarModal
          onConfirm={handleConfirmAbonar}
          onCancel={() => { setAbonandoId(null); setAbonarError(null) }}
          loading={abonarMutation.isPending}
          error={abonarError}
        />
      )}

      {deletingId && (
        <ConfirmDeleteModal
          message="¿Estás seguro de eliminar esta factura?"
          onConfirm={handleConfirmDelete}
          onCancel={() => setDeletingId(null)}
          loading={deleteMutation.isPending}
        />
      )}
    </div>
  )
}
