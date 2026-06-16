import { useQuery, useMutation } from '@tanstack/react-query'
import { setupService, type CreateCohorteRequest } from '@/features/coordinacion/services/setupService'
import { equiposService } from '@/features/coordinacion/services/equiposService'
import { avisosService } from '@/features/coordinacion/services/avisosService'
import type { ClonarEquipoRequest, AsignacionMasivaRequest, AvisoFormData } from '@/features/coordinacion/types'

export function useMateriasOptions() {
  return useQuery({
    queryKey: ['materias', 'options'],
    queryFn: () => setupService.getMateriasOptions(),
  })
}

export function useCohortesOptions() {
  return useQuery({
    queryKey: ['cohortes', 'options'],
    queryFn: () => setupService.getCohortesOptions(),
  })
}

export function useCreateCohorte() {
  return useMutation({
    mutationFn: (data: CreateCohorteRequest) => setupService.createCohorte(data),
  })
}

export function useClonarEquipoSetup() {
  return useMutation({
    mutationFn: (data: ClonarEquipoRequest) => equiposService.clonarEquipo(data),
  })
}

export function useAsignacionMasivaSetup() {
  return useMutation({
    mutationFn: (data: AsignacionMasivaRequest) => equiposService.asignacionMasiva(data),
  })
}

export function useUploadPrograma() {
  return useMutation({
    mutationFn: (data: { materia_id: string; cohorte_id: string; file: File }) =>
      setupService.uploadPrograma(data),
  })
}

export function useCargarFechas() {
  return useMutation({
    mutationFn: (data: Array<{ materia_id: string; fecha: string; descripcion: string }>) =>
      setupService.cargarFechas(data),
  })
}

export function usePublicarAvisoSetup() {
  return useMutation({
    mutationFn: (data: AvisoFormData) => avisosService.create(data),
  })
}
