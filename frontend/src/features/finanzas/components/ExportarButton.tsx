import { Button } from '@/shared/components/ui/Button'

interface ExportarButtonProps {
  onExport: () => void
  loading: boolean
}

export function ExportarButton({ onExport, loading }: ExportarButtonProps) {
  return (
    <Button variant="secondary" onClick={onExport} loading={loading}>
      Exportar CSV
    </Button>
  )
}
