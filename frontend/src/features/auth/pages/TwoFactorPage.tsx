import { useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { TwoFactorForm } from '@/features/auth/components/TwoFactorForm'
import { Card } from '@/shared/components/ui/Card'

export default function TwoFactorPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const twoFaToken = (location.state as { two_fa_token?: string } | null)
    ?.two_fa_token

  useEffect(() => {
    if (!twoFaToken) {
      navigate('/login', { replace: true })
    }
  }, [twoFaToken, navigate])

  if (!twoFaToken) {
    return null
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-gray-50 px-4">
      <Card
        className="w-full max-w-md"
        header={<h1 className="text-xl font-semibold text-gray-900">Verificación en dos pasos</h1>}
      >
        <TwoFactorForm twoFaToken={twoFaToken} />
      </Card>
    </div>
  )
}
