import { useMutation, type UseMutationResult } from '@tanstack/react-query'
import { authApi } from '@/features/auth/services/authApi'

interface ForgotInput {
  email: string
}

interface ResetInput {
  token: string
  password: string
}

interface UseRecoveryResult {
  forgot: UseMutationResult<void, Error, ForgotInput>
  reset: UseMutationResult<void, Error, ResetInput>
}

export function useRecovery(): UseRecoveryResult {
  const forgot = useMutation<void, Error, ForgotInput>({
    mutationFn: async (data: ForgotInput) => {
      await authApi.forgot(data)
    },
  })

  const reset = useMutation<void, Error, ResetInput>({
    mutationFn: async (data: ResetInput) => {
      await authApi.reset(data)
    },
  })

  return { forgot, reset }
}
