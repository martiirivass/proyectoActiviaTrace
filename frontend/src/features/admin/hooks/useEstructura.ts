import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { estructuraService } from '@/features/admin/services/estructuraService'
import type { CarreraFormData, CohorteFormData, MateriaFormData, DictadoFormData } from '@/features/admin/types'

export function useCarreras() {
  return useQuery({
    queryKey: ['carreras'],
    queryFn: () => estructuraService.getCarreras(),
  })
}

export function useCreateCarrera() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CarreraFormData) => estructuraService.createCarrera(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['carreras'] }),
  })
}

export function useUpdateCarrera() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CarreraFormData> }) =>
      estructuraService.updateCarrera(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['carreras'] }),
  })
}

export function useDeleteCarrera() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => estructuraService.deleteCarrera(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['carreras'] }),
  })
}

export function useCohortes(carreraId?: string) {
  return useQuery({
    queryKey: ['cohortes', carreraId],
    queryFn: () => estructuraService.getCohortes(carreraId),
  })
}

export function useCreateCohorte() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CohorteFormData) => estructuraService.createCohorte(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cohortes'] }),
  })
}

export function useUpdateCohorte() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CohorteFormData> }) =>
      estructuraService.updateCohorte(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cohortes'] }),
  })
}

export function useDeleteCohorte() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => estructuraService.deleteCohorte(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['cohortes'] }),
  })
}

export function useMaterias() {
  return useQuery({
    queryKey: ['materias'],
    queryFn: () => estructuraService.getMaterias(),
  })
}

export function useCreateMateria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: MateriaFormData) => estructuraService.createMateria(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['materias'] }),
  })
}

export function useUpdateMateria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<MateriaFormData> }) =>
      estructuraService.updateMateria(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['materias'] }),
  })
}

export function useDeleteMateria() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => estructuraService.deleteMateria(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['materias'] }),
  })
}

export function useDictados(materiaId?: string, cohorteId?: string) {
  return useQuery({
    queryKey: ['dictados', materiaId, cohorteId],
    queryFn: () => estructuraService.getDictados(materiaId, cohorteId),
  })
}

export function useCreateDictado() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: DictadoFormData) => estructuraService.createDictado(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['dictados'] }),
  })
}

export function useUpdateDictado() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<DictadoFormData> }) =>
      estructuraService.updateDictado(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['dictados'] }),
  })
}

export function useDeleteDictado() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => estructuraService.deleteDictado(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['dictados'] }),
  })
}
