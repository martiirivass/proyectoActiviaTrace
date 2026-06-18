import { useState } from 'react'
import { Button } from '@/shared/components/ui/Button'
import { Input } from '@/shared/components/ui/Input'

interface FiltrosLiquidacionesProps {
  onCalcular: (cohorteId: string, periodo: string) => void
  onCargar: (cohorteId: string, periodo: string) => void
  loading: boolean
}

export function FiltrosLiquidaciones({ onCalcular, onCargar, loading }: FiltrosLiquidacionesProps) {
  const [cohorteId, setCohorteId] = useState('')
  const [periodo, setPeriodo] = useState('')

  const isValid = cohorteId.trim() !== '' && /^\d{4}-(0[1-9]|1[0-2])$/.test(periodo)

  return (
    <div className="flex flex-wrap items-end gap-4 rounded-lg border border-gray-200 bg-white p-4">
      <Input
        label="ID Cohorte"
        placeholder="Ingrese ID de cohorte"
        value={cohorteId}
        onChange={(e) => setCohorteId(e.target.value)}
      />
      <Input
        label="Período (AAAA-MM)"
        placeholder="2026-06"
        value={periodo}
        onChange={(e) => setPeriodo(e.target.value)}
      />
      <Button
        variant="secondary"
        onClick={() => onCargar(cohorteId, periodo)}
        disabled={!isValid || loading}
      >
        Cargar
      </Button>
      <Button
        onClick={() => onCalcular(cohorteId, periodo)}
        disabled={!isValid || loading}
        loading={loading}
      >
        Calcular
      </Button>
    </div>
  )
}
