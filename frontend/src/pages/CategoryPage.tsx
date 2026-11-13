import { ChevronLeft } from 'lucide-react'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { ErrorState } from '@/components/ErrorState'
import { ProductGrid } from '@/components/common/ProductGrid'
import { SortSelect } from '@/components/SortSelect'
import { EmptyState } from '@/components/common/EmptyState'
import { ProductGridSkeleton } from '@/components/common/Skeletons'
import { getCategories, getProducts, parseSort } from '@/lib/catalog'
import { useAsync } from '@/lib/use-async'

export function CategoryPage() {
  const { id = '' } = useParams()
  const [params] = useSearchParams()
  const sort = parseSort(params.get('sort'))

  const categories = useAsync(getCategories, [])
  const products = useAsync(() => getProducts({ categoryId: id, sort }), [id, sort])

  const category = categories.data?.find((c) => c.id === id)

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <Link to="/" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary">
            <ChevronLeft className="size-4" aria-hidden="true" /> All categories
          </Link>
          <h1 className="mt-2 text-2xl font-bold">{category?.name ?? 'Products'}</h1>
          {category?.description && <p className="text-muted-foreground">{category.description}</p>}
        </div>
        <SortSelect />
      </div>

      {products.loading && <ProductGridSkeleton />}

      {products.error && (
        <ErrorState message="We couldn't load the products." onRetry={products.reload} />
      )}

      {!products.loading && !products.error && products.data?.length === 0 && (
        <EmptyState title="No products in this category yet" hint="Try another category." />
      )}

      {products.data && products.data.length > 0 && <ProductGrid products={products.data} />}
    </div>
  )
}
