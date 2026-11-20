import { Minus, Plus } from 'lucide-react'

import { Button } from '@/components/ui/button'

interface QuantitySelectorProps {
  value: number
  min?: number
  max: number
  onChange: (value: number) => void
  label?: string
  size?: 'default' | 'sm'
}

/** −/+ stepper clamped to [min, max]. The + button disables at max so stock can never be exceeded. */
export function QuantitySelector({
  value,
  min = 1,
  max,
  onChange,
  label = 'quantity',
  size = 'default',
}: QuantitySelectorProps) {
  const iconSize = size === 'sm' ? 'size-8' : 'size-10'
  return (
    <div className="inline-flex items-center gap-1" role="group" aria-label={label}>
      <Button
        type="button"
        variant="outline"
        size="icon"
        className={iconSize}
        onClick={() => onChange(Math.max(min, value - 1))}
        disabled={value <= min}
        aria-label={`Decrease ${label}`}
      >
        <Minus />
      </Button>
      <output
        className="min-w-10 text-center font-medium tabular-nums"
        aria-live="polite"
        data-testid="quantity-value"
      >
        {value}
      </output>
      <Button
        type="button"
        variant="outline"
        size="icon"
        className={iconSize}
        onClick={() => onChange(Math.min(max, value + 1))}
        disabled={value >= max}
        aria-label={`Increase ${label}`}
      >
        <Plus />
      </Button>
    </div>
  )
}
