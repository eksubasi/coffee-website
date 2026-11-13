import { ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'

import { PriceTag } from '@/components/common/PriceTag'
import { StockBadge } from '@/components/common/StockBadge'
import { ErrorState } from '@/components/ErrorState'
import { DataTable, type Column } from '@/components/manage/DataTable'
import { getProducts } from '@/lib/catalog'
import { useAsync } from '@/lib/use-async'
import type { Product } from '@/types'

const columns: Column<Product>[] = [
  {
    id: 'name',
    header: 'Product',
    sortValue: (p) => p.name,
    cell: (p) => (
      <div className="min-w-48">
        <p className="font-medium">{p.name}</p>
        <p className="text-xs text-muted-foreground">{p.model}</p>
      </div>
    ),
  },
  { id: 'category', header: 'Category', sortValue: (p) => p.categoryName },
  {
    id: 'price',
    header: 'Price',
    align: 'right',
    sortValue: (p) => p.price,
    cell: (p) => <PriceTag price={p.price} size="sm" className="justify-end" />,
  },
  {
    id: 'stock',
    header: 'Stock',
    sortValue: (p) => p.stock,
    cell: (p) => <StockBadge stock={p.stock} />,
  },
  {
    id: 'view',
    header: 'Store page',
    align: 'right',
    cell: (p) => (
      <Link
        to={`/product/${p.id}`}
        className="inline-flex items-center gap-1 text-accent-strong hover:underline"
        aria-label={`Open ${p.name} in the store`}
      >
        View <ExternalLink className="size-3.5" aria-hidden="true" />
      </Link>
    ),
  },
]

/**
 * /manage/products — product list for product managers.
 * KAN-49 ships the read-only table; KAN-50 adds the add / edit / delete form and the manage endpoints.
 */
export function ManageProductsPage() {
  const products = useAsync(() => getProducts(), [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="type-title">Products</h1>
        <p className="type-caption">
          {products.data ? `${products.data.length} products in the catalog.` : 'All products in the catalog.'}
        </p>
      </div>

      {products.error ? (
        <ErrorState message="We couldn't load the products." onRetry={products.reload} />
      ) : (
        <DataTable
          caption="Products"
          columns={columns}
          rows={products.data ?? []}
          rowKey={(p) => p.id}
          loading={products.loading}
          initialSort={{ columnId: 'name', direction: 'asc' }}
        />
      )}
    </div>
  )
}
