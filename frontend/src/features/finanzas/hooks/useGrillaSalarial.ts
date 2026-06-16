import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { grillaSalarialService } from '@/features/finanzas/services/grillaSalarialService'
import type { SalarioBaseFormData, SalarioPlusFormData } from '@/features/finanzas/types'

export function useSalariosBase(rol?: string, vigente?: boolean) {
  return useQuery({
    queryKey: ['grilla-base', rol, vigente],
    queryFn: () => grillaSalarialService.getSalariosBase(rol, vigente),
  })
}

export function useCreateSalarioBase() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: SalarioBaseFormData) => grillaSalarialService.createSalarioBase(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['grilla-base'] }),
  })
}

export function useUpdateSalarioBase() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<SalarioBaseFormData> }) =>
      grillaSalarialService.updateSalarioBase(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['grilla-base'] }),
  })
}

export function useDeleteSalarioBase() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => grillaSalarialService.deleteSalarioBase(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['grilla-base'] }),
  })
}

export function useSalariosPlus(grupo?: string, rol?: string, vigente?: boolean) {
  return useQuery({
    queryKey: ['grilla-plus', grupo, rol, vigente],
    queryFn: () => grillaSalarialService.getSalariosPlus(grupo, rol, vigente),
  })
}

export function useCreateSalarioPlus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: SalarioPlusFormData) => grillaSalarialService.createSalarioPlus(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['grilla-plus'] }),
  })
}

export function useUpdateSalarioPlus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<SalarioPlusFormData> }) =>
      grillaSalarialService.updateSalarioPlus(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['grilla-plus'] }),
  })
}

export function useDeleteSalarioPlus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => grillaSalarialService.deleteSalarioPlus(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['grilla-plus'] }),
  })
}
