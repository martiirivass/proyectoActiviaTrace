import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRecovery } from '@/features/auth/hooks/useRecovery'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'
import { Alert } from '@/shared/components/ui/Alert'

const recoverySchema = z.object({
  email: z
    .string()
    .min(1, 'El email es requerido')
    .email('Ingrese un email válido'),
})

type RecoveryFormData = z.infer<typeof recoverySchema>

export function RecoveryForm() {
  const { forgot } = useRecovery()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RecoveryFormData>({
    resolver: zodResolver(recoverySchema),
  })

  const onSubmit = (data: RecoveryFormData) => {
    forgot.mutate(data)
  }

  if (forgot.isSuccess) {
    return (
      <Alert variant="success" message="Si el email está registrado, recibirás un enlace de recuperación." />
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
      {forgot.isError && (
        <Alert
          variant="error"
          message={forgot.error?.message ?? 'Error al solicitar recuperación'}
        />
      )}

      <p className="text-sm text-gray-600">
        Ingresa tu email y te enviaremos un enlace para restablecer tu
        contraseña.
      </p>

      <Input
        label="Email"
        type="email"
        placeholder="correo@ejemplo.com"
        error={errors.email?.message}
        {...register('email')}
      />

      <Button type="submit" loading={forgot.isPending} className="w-full">
        Enviar enlace
      </Button>
    </form>
  )
}
