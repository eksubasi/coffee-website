import { Check, Minus, Pencil, Plus, Trash2, X } from 'lucide-react'
import { useState, type FormEvent } from 'react'

import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { EmptyState } from '@/components/common/EmptyState'
import { StockBadge } from '@/components/common/StockBadge'
import { ErrorState } from '@/components/ErrorState'
import { FormField } from '@/components/FormField'
import { DataTable, type Column } from '@/components/manage/DataTable'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { ApiError } from '@/lib/api'
import {
  createCategory,
  deleteCategory,
  listManagedCategories,
  listManagedProducts,
  updateCategory,
  updateStock,
  type ManagedCategory,
  type ManagedProduct,
} from '@/lib/manage-catalog'
import { LOW_STOCK_THRESHOLD } from '@/lib/stock'
import { toast } from '@/lib/toast'
import { useAsync } from '@/lib/use-async'

const errorText = (e: unknown, fallback: string) => (e instanceof ApiError && e.status !== 0 ? e.message : fallback)

/** /manage/categories — categories and stock levels for product managers (KAN-59, Req 12). */
export function CategoriesStockPage() {
  const categories = useAsync(listManagedCategories, [])

  return (
    <div className="space-y-10">
      <div>
        <h1 className="type-title">Categories &amp; stock</h1>
        <p className="type-caption">Organise the catalog and keep stock levels up to date.</p>
      </div>
      <CategoriesSection categories={categories.data} loading={categories.loading} error={categories.error} reload={categories.reload} />
      <StockSection categories={categories.data ?? []} />
    </div>
  )
}

// --- Categories ----------------------------------------------------------------------------------

function CategoriesSection({
  categories,
  loading,
  error,
  reload,
}: {
  categories?: ManagedCategory[]
  loading: boolean
  error?: unknown
  reload: () => void
}) {
  const [editing, setEditing] = useState<ManagedCategory>()
  const [toDelete, setToDelete] = useState<ManagedCategory>()

  async function confirmDelete() {
    if (!toDelete) return
    try {
      await deleteCategory(toDelete.id)
      toast.success(`Deleted ${toDelete.name}.`)
      if (editing?.id === toDelete.id) setEditing(undefined)
      reload()
    } catch (e) {
      toast.error(errorText(e, 'Could not delete the category.'))
      if (e instanceof ApiError && e.status === 409) {
        reload() // someone added a product meanwhile; refresh the counts
        return
      }
      throw e
    }
  }

  const columns: Column<ManagedCategory>[] = [
    {
      id: 'name',
      header: 'Category',
      sortValue: (c) => c.name,
      cell: (c) => (
        <div className="min-w-40">
          <p className="font-medium">{c.name}</p>
          {c.description && <p className="text-xs text-muted-foreground">{c.description}</p>}
        </div>
      ),
    },
    { id: 'count', header: 'Products', align: 'right', sortValue: (c) => c.productCount },
    {
      id: 'actions',
      header: 'Actions',
      align: 'right',
      cell: (c) => (
        <div className="flex justify-end gap-1">
          <Button variant="ghost" size="icon" onClick={() => setEditing(c)} aria-label={`Rename ${c.name}`}>
            <Pencil aria-hidden="true" />
          </Button>
          {c.productCount > 0 ? (
            <Tooltip>
              <TooltipTrigger asChild>
                {/* A disabled button gets no hover events, so the tooltip sits on a wrapper. */}
                <span tabIndex={0} className="inline-flex rounded-md" aria-label={`${c.name} can't be deleted while it has products`}>
                  <Button variant="ghost" size="icon" disabled aria-hidden="true" tabIndex={-1}>
                    <Trash2 />
                  </Button>
                </span>
              </TooltipTrigger>
              <TooltipContent>Move or delete its {c.productCount} product(s) first</TooltipContent>
            </Tooltip>
          ) : (
            <Button
              variant="ghost"
              size="icon"
              className="text-destructive hover:text-destructive"
              onClick={() => setToDelete(c)}
              aria-label={`Delete ${c.name}`}
            >
              <Trash2 aria-hidden="true" />
            </Button>
          )}
        </div>
      ),
    },
  ]

  return (
    <section className="space-y-4" aria-labelledby="categories-heading">
      <h2 id="categories-heading" className="type-heading">
        Categories
      </h2>
      <CategoryForm key={editing?.id ?? 'new'} category={editing} onDone={() => setEditing(undefined)} onSaved={reload} />
      {error ? (
        <ErrorState message="We couldn't load the categories." onRetry={reload} />
      ) : (
        <DataTable
          caption="Categories"
          columns={columns}
          rows={categories ?? []}
          rowKey={(c) => c.id}
          loading={loading}
          initialSort={{ columnId: 'name', direction: 'asc' }}
          empty={<EmptyState title="No categories yet" hint="Add one above." />}
        />
      )}
      <ConfirmDialog
        open={toDelete !== undefined}
        onOpenChange={(open) => !open && setToDelete(undefined)}
        title={`Delete the ${toDelete?.name ?? ''} category?`}
        description="It has no products, so nothing else changes."
        confirmLabel="Delete"
        destructive
        onConfirm={confirmDelete}
      />
    </section>
  )
}

/** Add a category, or rename the one passed in. */
function CategoryForm({
  category,
  onDone,
  onSaved,
}: {
  category?: ManagedCategory
  onDone: () => void
  onSaved: () => void
}) {
  const [name, setName] = useState(category?.name ?? '')
  const [description, setDescription] = useState(category?.description ?? '')
  const [error, setError] = useState<string>()
  const [busy, setBusy] = useState(false)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (!name.trim()) {
      setError('Enter a name.')
      return
    }
    setBusy(true)
    setError(undefined)
    try {
      const values = { name: name.trim(), description: description.trim() }
      const saved = category ? await updateCategory(category.id, values) : await createCategory(values)
      toast.success(category ? `Saved ${saved.name}.` : `Added ${saved.name}.`)
      onSaved()
      if (category) onDone()
      else {
        setName('')
        setDescription('')
      }
    } catch (e) {
      const data = e instanceof ApiError ? (e.data as Record<string, unknown> | undefined) : undefined
      const nameError = data && Array.isArray(data.name) ? data.name.join(' ') : undefined
      setError(nameError ?? errorText(e, 'Could not reach the server. Try again.'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      noValidate
      className="grid gap-3 rounded-xl border bg-card p-4 sm:grid-cols-[1fr_2fr_auto] sm:items-start"
      aria-label={category ? `Rename ${category.name}` : 'Add a category'}
    >
      <FormField
        id="category-name"
        label={category ? `Rename “${category.name}”` : 'New category'}
        placeholder="e.g. Tea"
        value={name}
        onChange={(e) => setName(e.target.value)}
        error={error}
      />
      <FormField
        id="category-description"
        label="Description (optional)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <div className="flex gap-2 sm:pt-6">
        <Button type="submit" disabled={busy}>
          {category ? <Check aria-hidden="true" /> : <Plus aria-hidden="true" />}
          {category ? 'Save' : 'Add'}
        </Button>
        {category && (
          <Button type="button" variant="outline" onClick={onDone} aria-label="Cancel renaming">
            <X aria-hidden="true" />
          </Button>
        )}
      </div>
    </form>
  )
}

// --- Stock ---------------------------------------------------------------------------------------

function StockSection({ categories }: { categories: ManagedCategory[] }) {
  const products = useAsync(listManagedProducts, [])
  // Rows updated on this page, so a stock change shows at once without reloading the whole table.
  const [updated, setUpdated] = useState<Record<number, ManagedProduct>>({})
  const [categoryFilter, setCategoryFilter] = useState('')
  const [lowOnly, setLowOnly] = useState(false)

  const rows = (products.data ?? [])
    .map((p) => updated[p.id] ?? p)
    .filter((p) => !categoryFilter || String(p.categoryId) === categoryFilter)
    .filter((p) => !lowOnly || p.stock <= LOW_STOCK_THRESHOLD)

  const columns: Column<ManagedProduct>[] = [
    {
      id: 'name',
      header: 'Product',
      sortValue: (p) => p.name,
      cell: (p) => (
        <div className="min-w-44">
          <p className="font-medium">{p.name}</p>
          <p className="text-xs text-muted-foreground">{p.categoryName}</p>
        </div>
      ),
    },
    { id: 'stock', header: 'Stock', sortValue: (p) => p.stock, cell: (p) => <StockBadge stock={p.stock} /> },
    {
      id: 'change',
      header: 'Change stock',
      align: 'right',
      cell: (p) => (
        <StockControl
          // Reset the number box whenever the saved stock changes.
          key={`${p.id}-${p.stock}`}
          product={p}
          onSaved={(saved) => setUpdated((u) => ({ ...u, [saved.id]: saved }))}
        />
      ),
    },
  ]

  return (
    <section className="space-y-4" aria-labelledby="stock-heading">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 id="stock-heading" className="type-heading">
            Stock
          </h2>
          <p className="type-caption">Use − and + for small changes, or type the counted amount and press Set.</p>
        </div>
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <label className="flex items-center gap-2">
            <span className="text-muted-foreground">Category</span>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="h-9 rounded-md border bg-background px-3 shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
            >
              <option value="">All</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={lowOnly} onChange={(e) => setLowOnly(e.target.checked)} className="size-4 accent-primary" />
            Low or out of stock only
          </label>
        </div>
      </div>

      {products.error ? (
        <ErrorState message="We couldn't load the products." onRetry={products.reload} />
      ) : (
        <DataTable
          caption="Stock levels"
          columns={columns}
          rows={rows}
          rowKey={(p) => p.id}
          loading={products.loading}
          initialSort={{ columnId: 'stock', direction: 'asc' }}
          empty={<EmptyState title="No products match" hint="Change the filters above." />}
        />
      )}
    </section>
  )
}

/** − / + buttons and an absolute "set to" box for one product. Uses the row-locking stock endpoint. */
function StockControl({ product, onSaved }: { product: ManagedProduct; onSaved: (p: ManagedProduct) => void }) {
  const [value, setValue] = useState(String(product.stock))
  const [busy, setBusy] = useState(false)

  async function save(update: { set: number } | { change: number }) {
    setBusy(true)
    try {
      const saved = await updateStock(product.id, update)
      onSaved(saved)
      toast.success(`${saved.name}: stock is now ${saved.stock}.`)
    } catch (e) {
      toast.error(errorText(e, 'Could not update the stock.'))
      setValue(String(product.stock))
    } finally {
      setBusy(false)
    }
  }

  const parsed = Number(value)
  const validSet = value.trim() !== '' && Number.isInteger(parsed) && parsed >= 0 && parsed !== product.stock

  return (
    <form
      className="flex items-center justify-end gap-1"
      onSubmit={(e) => {
        e.preventDefault()
        if (validSet) void save({ set: parsed })
      }}
    >
      <Button
        type="button"
        variant="outline"
        size="icon-sm"
        disabled={busy || product.stock <= 0}
        onClick={() => void save({ change: -1 })}
        aria-label={`Remove one ${product.name}`}
      >
        <Minus aria-hidden="true" />
      </Button>
      <input
        type="number"
        min={0}
        step={1}
        inputMode="numeric"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={busy}
        aria-label={`Stock for ${product.name}`}
        className="h-8 w-20 rounded-md border border-input bg-background px-2 text-right text-sm tabular-nums shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
      />
      <Button
        type="button"
        variant="outline"
        size="icon-sm"
        disabled={busy}
        onClick={() => void save({ change: 1 })}
        aria-label={`Add one ${product.name}`}
      >
        <Plus aria-hidden="true" />
      </Button>
      <Button type="submit" size="sm" variant="secondary" disabled={busy || !validSet}>
        Set
      </Button>
    </form>
  )
}
