import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { facturasService } from '@/features/finanzas/services/facturasService'
import type { FacturaFormData, FacturaFiltros } from '@/features/finanzas/types'

export function useFacturas(filtros?: FacturaFiltros) {
  return useQuery({
    queryKey: ['facturas', filtros],
    queryFn: () => facturasService.listar(filtros),
  })
}

export function useFactura(id: string) {
  return useQuery({
    queryKey: ['factura', id],
    queryFn: () => facturasService.getById(id),
    enabled: !!id,
  })
}

export function useCreateFactura() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: FacturaFormData) => facturasService.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['facturas'] }),
  })
}

export function useUpdateFactura() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<FacturaFormData> }) =>
      facturasService.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['facturas'] }),
  })
}

export function useAbonarFactura() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => facturasService.abonar(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['facturas'] }),
  })
}

export function useDeleteFactura() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => facturasService.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['facturas'] }),
  })
}
