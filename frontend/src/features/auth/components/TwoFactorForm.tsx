import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { use2FA } from '@/features/auth/hooks/use2FA'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import { Alert } from '@/shared/components/ui/Alert'

const twoFASchema = z.object({
  code: z
    .string()
    .length(6, 'El código debe tener exactamente 6 dígitos')
    .regex(/^\d+$/, 'El código debe contener solo números'),
})

type TwoFAFormData = z.infer<typeof twoFASchema>

interface TwoFactorFormProps {
  twoFaToken: string
}

export function TwoFactorForm({ twoFaToken }: TwoFactorFormProps) {
  const { verify2fa } = use2FA()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TwoFAFormData>({
    resolver: zodResolver(twoFASchema),
  })

  const onSubmit = (data: TwoFAFormData) => {
    verify2fa.mutate({ two_fa_token: twoFaToken, code: data.code })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
      {verify2fa.isError && (
        <Alert
          variant="error"
          message={
            verify2fa.error?.message ?? 'Código de verificación inválido'
          }
        />
      )}

      <p className="text-sm text-gray-600">
        Ingresa el código de 6 dígitos de tu aplicación de autenticación.
      </p>

      <Input
        label="Código de verificación"
        placeholder="000000"
        maxLength={6}
        inputMode="numeric"
        autoComplete="one-time-code"
        error={errors.code?.message}
        {...register('code')}
      />

      <Button type="submit" loading={verify2fa.isPending} className="w-full">
        Verificar
      </Button>
    </form>
  )
}
