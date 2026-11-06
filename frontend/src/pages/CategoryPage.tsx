import { ChevronLeft } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { ErrorState } from '@/components/ErrorState'
import { EmptyState } from '@/components/temp-kan30/EmptyState'
import { ProductCard } from '@/components/temp-kan30/ProductCard'
import { ProductGridSkeleton } from '@/components/temp-kan30/ProductGridSkeleton'
import { getCategories, getProducts } from '@/lib/catalog'
import { useAsync } from '@/lib/use-async'

export function CategoryPage() {
  const { id = '' } = useParams()
  const categories = useAsync(getCategories, [])
  const products = useAsync(() => getProducts(id), [id])

  const category = categories.data?.find((c) => c.id === id)

  return (
    <div className="space-y-6">
      <div>
        <Link to="/" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary">
          <ChevronLeft className="size-4" aria-hidden="true" /> All categories
        </Link>
        <h1 className="mt-2 text-2xl font-bold">{category?.name ?? 'Products'}</h1>
        {category?.description && <p className="text-muted-foreground">{category.description}</p>}
      </div>

      {products.loading && <ProductGridSkeleton />}

      {products.error && (
        <ErrorState message="We couldn't load the products." onRetry={products.reload} />
      )}

      {!products.loading && !products.error && products.data?.length === 0 && (
        <EmptyState title="No products in this category yet" hint="Try another category." />
      )}

      {products.data && products.data.length > 0 && (
        <ul className="grid grid-cols-1 gap-4 min-[480px]:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {products.data.map((product) => (
            <li key={product.id}>
              <ProductCard product={product} />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
