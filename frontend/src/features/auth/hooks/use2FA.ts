import { useMutation, type UseMutationResult } from '@tanstack/react-query'
import { useAuth } from '@/shared/hooks/useAuth'
import { authApi } from '@/features/auth/services/authApi'

interface TwoFAInput {
  two_fa_token: string
  code: string
}

interface Use2FAResult {
  verify2fa: UseMutationResult<void, Error, TwoFAInput>
}

export function use2FA(): Use2FAResult {
  const { login: setSession } = useAuth()

  const verify2fa = useMutation<void, Error, TwoFAInput>({
    mutationFn: async ({ two_fa_token, code }: TwoFAInput) => {
      const response = await authApi.verify2fa({ two_fa_token, code })
      await setSession(response)
    },
  })

  return { verify2fa }
}
