import { ExternalLink, Pencil, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { EmptyState } from '@/components/common/EmptyState'
import { PriceTag } from '@/components/common/PriceTag'
import { StockBadge } from '@/components/common/StockBadge'
import { ErrorState } from '@/components/ErrorState'
import { DataTable, type Column } from '@/components/manage/DataTable'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api'
import { deleteProduct, listManagedProducts, type ManagedProduct } from '@/lib/manage-catalog'
import { toast } from '@/lib/toast'
import { useAsync } from '@/lib/use-async'
import { formatPrice } from '@/lib/utils'

/**
 * /manage/products — product list for product managers (KAN-50, Req 12).
 * Add and edit open the form page; delete asks first. Products that were ever ordered cannot be
 * deleted (the backend answers 409), so the message suggests setting their stock to 0 instead.
 */
export function ManageProductsPage() {
  const products = useAsync(listManagedProducts, [])
  const [toDelete, setToDelete] = useState<ManagedProduct>()

  async function confirmDelete() {
    if (!toDelete) return
    try {
      await deleteProduct(toDelete.id)
      toast.success(`Deleted ${toDelete.name}.`)
      products.reload()
    } catch (e) {
      if (e instanceof ApiError && e.status === 409) {
        // Retrying won't help: close the dialog and explain.
        toast.error(e.message)
        return
      }
      toast.error(e instanceof ApiError ? e.message : 'Could not delete the product.')
      throw e // keep the dialog open so they can retry
    }
  }

  const columns: Column<ManagedProduct>[] = [
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
      id: 'cost',
      header: 'Cost',
      align: 'right',
      sortValue: (p) => p.effectiveCost,
      cell: (p) => (
        <span className="tabular-nums">
          {formatPrice(p.effectiveCost)}
          {p.cost === null && (
            <span className="block text-xs text-muted-foreground" title="No cost entered: 50% of price is used">
              default 50%
            </span>
          )}
        </span>
      ),
    },
    { id: 'stock', header: 'Stock', sortValue: (p) => p.stock, cell: (p) => <StockBadge stock={p.stock} /> },
    {
      id: 'actions',
      header: 'Actions',
      align: 'right',
      cell: (p) => (
        <div className="flex justify-end gap-1">
          <Button asChild variant="ghost" size="icon" aria-label={`Open ${p.name} in the store`}>
            <Link to={`/product/${p.id}`}>
              <ExternalLink aria-hidden="true" />
            </Link>
          </Button>
          <Button asChild variant="ghost" size="icon" aria-label={`Edit ${p.name}`}>
            <Link to={`/manage/products/${p.id}/edit`}>
              <Pencil aria-hidden="true" />
            </Link>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="text-destructive hover:text-destructive"
            onClick={() => setToDelete(p)}
            aria-label={`Delete ${p.name}`}
          >
            <Trash2 aria-hidden="true" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="type-title">Products</h1>
          <p className="type-caption">
            {products.data ? `${products.data.length} products in the catalog.` : 'All products in the catalog.'}
          </p>
        </div>
        <Button asChild>
          <Link to="/manage/products/new">
            <Plus aria-hidden="true" /> Add product
          </Link>
        </Button>
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
          empty={<EmptyState title="No products yet" hint="Add the first product to start selling." />}
        />
      )}

      <ConfirmDialog
        open={toDelete !== undefined}
        onOpenChange={(open) => !open && setToDelete(undefined)}
        title={`Delete ${toDelete?.name ?? 'product'}?`}
        description="It disappears from the store. Products that customers have already ordered can't be deleted; set their stock to 0 instead."
        confirmLabel="Delete"
        destructive
        onConfirm={confirmDelete}
      />
    </div>
  )
}
