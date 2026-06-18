import { useMutation, type UseMutationResult } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { authApi } from '@/features/auth/services/authApi'
import { useAuth } from '@/shared/hooks/useAuth'
import type { LoginRequest } from '@/features/auth/types'

interface UseLoginResult {
  login: UseMutationResult<void, Error, LoginRequest>
}

export function useLogin(): UseLoginResult {
  const { login: setSession } = useAuth()
  const navigate = useNavigate()

  const login = useMutation<void, Error, LoginRequest>({
    mutationFn: async (data: LoginRequest) => {
      const response = await authApi.login(data)

      if (response.requires_2fa) {
        navigate('/2fa', {
          state: { two_fa_token: response.two_fa_token },
          replace: true,
        })
        return
      }

      await setSession(response)
    },
  })

  return { login }
}
