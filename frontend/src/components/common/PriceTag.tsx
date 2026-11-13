import { cn, formatPrice } from '@/lib/utils'

const sizes = {
  sm: { price: 'text-base', original: 'text-xs' },
  md: { price: 'text-lg', original: 'text-sm' },
  lg: { price: 'text-2xl', original: 'text-base' },
} as const

interface PriceTagProps {
  /** Current price in TRY. */
  price: number
  /** Price before a discount. Shown struck through, with the percentage, only when higher than `price`. */
  originalPrice?: number
  size?: keyof typeof sizes
  className?: string
}

/** Product price in TRY, with optional discount display (sales manager discounts, Req 11). */
export function PriceTag({ price, originalPrice, size = 'md', className }: PriceTagProps) {
  const discounted = originalPrice !== undefined && originalPrice > price
  const percentOff = discounted ? Math.round((1 - price / originalPrice) * 100) : 0

  return (
    <p className={cn('flex flex-wrap items-baseline gap-x-2 tabular-nums', className)} data-testid="price-tag">
      <span className={cn('font-semibold text-primary', sizes[size].price)}>
        {discounted && <span className="sr-only">Now </span>}
        {formatPrice(price)}
      </span>
      {discounted && (
        <>
          <s className={cn('text-muted-foreground', sizes[size].original)}>
            <span className="sr-only">was </span>
            {formatPrice(originalPrice)}
          </s>
          <span className="rounded-full bg-destructive/10 px-2 py-0.5 text-xs font-semibold text-destructive">
            −{percentOff}%
          </span>
        </>
      )}
    </p>
  )
}
