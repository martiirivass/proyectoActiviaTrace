interface DateRangePickerProps {
  fechaDesde: string
  fechaHasta: string
  onDesdeChange: (value: string) => void
  onHastaChange: (value: string) => void
}

export function DateRangePicker({
  fechaDesde,
  fechaHasta,
  onDesdeChange,
  onHastaChange,
}: DateRangePickerProps) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-sm text-gray-600">Desde:</label>
      <input
        type="date"
        className="rounded-md border border-gray-300 px-2 py-1.5 text-sm"
        value={fechaDesde}
        onChange={(e) => onDesdeChange(e.target.value)}
      />
      <label className="text-sm text-gray-600">Hasta:</label>
      <input
        type="date"
        className="rounded-md border border-gray-300 px-2 py-1.5 text-sm"
        value={fechaHasta}
        onChange={(e) => onHastaChange(e.target.value)}
      />
    </div>
  )
}
