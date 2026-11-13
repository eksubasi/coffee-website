import { useSearchParams } from 'react-router-dom'

import { ErrorState } from '@/components/ErrorState'
import { ProductGrid } from '@/components/ProductGrid'
import { SortSelect } from '@/components/SortSelect'
import { EmptyState } from '@/components/temp-kan30/EmptyState'
import { ProductGridSkeleton } from '@/components/temp-kan30/ProductGridSkeleton'
import { getProducts, parseSort } from '@/lib/catalog'
import { useAsync } from '@/lib/use-async'

/** /search?q=<text>&sort=<price-asc|price-desc|popularity> — searches across all categories (Req 7). */
export function SearchPage() {
  const [params] = useSearchParams()
  const q = (params.get('q') ?? '').trim()
  const sort = parseSort(params.get('sort'))

  const products = useAsync(async () => (q ? getProducts({ search: q, sort }) : []), [q, sort])
  const count = products.data?.length ?? 0

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{q ? `Results for “${q}”` : 'Search'}</h1>
          <p className="text-muted-foreground" aria-live="polite">
            {!q
              ? 'Type in the search box above to find products by name or description.'
              : products.data
                ? `${count} ${count === 1 ? 'product' : 'products'} found`
                : ' '}
          </p>
        </div>
        {q && <SortSelect />}
      </div>

      {q && products.loading && <ProductGridSkeleton />}

      {products.error && <ErrorState message="We couldn't run your search." onRetry={products.reload} />}

      {q && products.data?.length === 0 && (
        <EmptyState title={`No products match “${q}”`} hint="Check the spelling or try a shorter word." />
      )}

      {products.data && products.data.length > 0 && <ProductGrid products={products.data} />}
    </div>
  )
}
