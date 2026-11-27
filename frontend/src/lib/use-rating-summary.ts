import { useCallback, useState } from 'react'

import { getProduct } from '@/lib/catalog'
import type { Product } from '@/types'

export interface RatingSummaryData {
  average: number | null
  count: number
}

/** Keeps the average + count in one place so the product header and the reviews section never disagree. */
export function useRatingSummary(product: Product) {
  const [summary, setSummary] = useState<RatingSummaryData>({ average: product.averageRating, count: product.ratingCount })

  // After the customer rates, ask the API for the new average instead of guessing it locally.
  const refresh = useCallback(async () => {
    try {
      const fresh = await getProduct(product.id)
      setSummary({ average: fresh.averageRating, count: fresh.ratingCount })
    } catch {
      /* the old numbers stay on screen */
    }
  }, [product.id])

  return [summary, refresh] as const
}
