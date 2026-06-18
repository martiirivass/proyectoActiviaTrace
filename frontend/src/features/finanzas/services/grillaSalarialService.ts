import { get, post, put, del } from '@/shared/api/api'
import type { SalarioBase, SalarioBaseFormData, SalarioPlus, SalarioPlusFormData } from '@/features/finanzas/types'

export const grillaSalarialService = {
  getSalariosBase: (rol?: string, vigente?: boolean): Promise<SalarioBase[]> =>
    get<SalarioBase[]>('/grilla-salarial/base', {
      params: { ...(rol && { rol }), ...(vigente !== undefined && { vigente: vigente.toString() }) },
    }),

  createSalarioBase: (data: SalarioBaseFormData): Promise<SalarioBase> =>
    post<SalarioBase>('/grilla-salarial/base', data),

  updateSalarioBase: (id: string, data: Partial<SalarioBaseFormData>): Promise<SalarioBase> =>
    put<SalarioBase>(`/grilla-salarial/base/${id}`, data),

  deleteSalarioBase: (id: string): Promise<void> =>
    del<void>(`/grilla-salarial/base/${id}`),

  getSalariosPlus: (grupo?: string, rol?: string, vigente?: boolean): Promise<SalarioPlus[]> =>
    get<SalarioPlus[]>('/grilla-salarial/plus', {
      params: {
        ...(grupo && { grupo }),
        ...(rol && { rol }),
        ...(vigente !== undefined && { vigente: vigente.toString() }),
      },
    }),

  createSalarioPlus: (data: SalarioPlusFormData): Promise<SalarioPlus> =>
    post<SalarioPlus>('/grilla-salarial/plus', data),

  updateSalarioPlus: (id: string, data: Partial<SalarioPlusFormData>): Promise<SalarioPlus> =>
    put<SalarioPlus>(`/grilla-salarial/plus/${id}`, data),

  deleteSalarioPlus: (id: string): Promise<void> =>
    del<void>(`/grilla-salarial/plus/${id}`),
}
