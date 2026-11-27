import { ChevronLeft } from 'lucide-react'
import { useState, type ChangeEvent, type FormEvent, type ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ErrorState } from '@/components/ErrorState'
import { FormField } from '@/components/FormField'
import { ProductImage } from '@/components/ProductImage'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { ApiError } from '@/lib/api'
import {
  createProduct,
  emptyProductForm,
  getManagedProduct,
  listManagedCategories,
  PRODUCT_FIELD_MAP,
  productToForm,
  updateProduct,
  type ManagedCategory,
  type ManagedProduct,
  type ProductFormValues,
} from '@/lib/manage-catalog'
import { toast } from '@/lib/toast'
import { useAsync } from '@/lib/use-async'
import { formatPrice } from '@/lib/utils'

type Errors = Partial<Record<keyof ProductFormValues, string>>

const controlClass =
  'w-full min-w-0 rounded-md border border-input bg-background px-3 text-base shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 aria-invalid:border-destructive md:text-sm'

/**
 * /manage/products/new and /manage/products/:id/edit (KAN-50, Req 9 + 12).
 * Price and starting stock can only be set when adding: afterwards prices belong to the sales
 * manager (Req 11) and stock changes go through Categories & stock (KAN-59), as the backend enforces.
 */
export function ProductFormPage() {
  const { id } = useParams()
  const editing = id !== undefined

  const categories = useAsync(listManagedCategories, [])
  const product = useAsync<ManagedProduct | undefined>(
    () => (id ? getManagedProduct(id) : Promise.resolve(undefined)),
    [id],
  )

  const loading = categories.loading || product.loading
  const error = categories.error ?? product.error

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <Link
          to="/manage/products"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary"
        >
          <ChevronLeft className="size-4" aria-hidden="true" /> All products
        </Link>
        <h1 className="type-title mt-2">
          {editing ? `Edit ${product.data?.name ?? 'product'}` : 'Add a product'}
        </h1>
      </div>

      {error ? (
        <ErrorState
          message={
            error instanceof ApiError && error.status === 404 ? 'This product no longer exists.' : "We couldn't load the form."
          }
          onRetry={() => {
            categories.reload()
            product.reload()
          }}
        />
      ) : loading || !categories.data ? (
        <Skeleton className="h-96 w-full" aria-label="Loading" />
      ) : (
        <ProductForm
          // Remount when switching products so the fields start from that product's values.
          key={id ?? 'new'}
          product={product.data}
          categories={categories.data}
        />
      )}
    </div>
  )
}

function ProductForm({ product, categories }: { product?: ManagedProduct; categories: ManagedCategory[] }) {
  const navigate = useNavigate()
  const creating = product === undefined
  const [values, setValues] = useState<ProductFormValues>(() => (product ? productToForm(product) : emptyProductForm()))
  const [errors, setErrors] = useState<Errors>({})
  const [formError, setFormError] = useState<string>()
  const [busy, setBusy] = useState(false)

  const set =
    (field: keyof ProductFormValues) =>
    (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setValues((v) => ({ ...v, [field]: event.target.value }))

  function validate(): Errors {
    const next: Errors = {}
    const required: [keyof ProductFormValues, string][] = [
      ['name', 'Enter a name.'],
      ['model', 'Enter the model code.'],
      ['serialNumber', 'Enter the serial or lot number.'],
      ['description', 'Enter a description.'],
      ['categoryId', 'Choose a category.'],
      ['distributorName', 'Enter the distributor.'],
    ]
    for (const [field, message] of required) if (!String(values[field]).trim()) next[field] = message

    if (creating) {
      const price = Number(values.price)
      if (!values.price.trim() || !Number.isFinite(price) || price <= 0) next.price = 'Enter a price above 0.'
      const stock = Number(values.stock)
      if (!Number.isInteger(stock) || stock < 0) next.stock = 'Stock must be a whole number, 0 or more.'
    }
    if (values.cost.trim()) {
      const cost = Number(values.cost)
      if (!Number.isFinite(cost) || cost < 0) next.cost = 'Cost must be 0 or more, or left empty.'
    }
    if (values.warrantyStatus === 'Under warranty') {
      const months = Number(values.warrantyMonths)
      if (!Number.isInteger(months) || months <= 0) next.warrantyMonths = 'Enter the warranty length in months.'
    }
    if (values.roastDate && values.expiryDate && values.expiryDate <= values.roastDate) {
      next.expiryDate = 'Expiry date must be after the roast date.'
    }
    return next
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(undefined)
    const found = validate()
    setErrors(found)
    if (Object.keys(found).length > 0) {
      setFormError('Please fix the highlighted fields.')
      return
    }

    setBusy(true)
    try {
      const saved = product ? await updateProduct(product.id, values) : await createProduct(values)
      toast.success(creating ? `Added ${saved.name}. It's in the store now.` : `Saved ${saved.name}.`)
      navigate('/manage/products')
    } catch (e) {
      if (e instanceof ApiError && e.status === 400 && e.data && typeof e.data === 'object') {
        // Show the backend's field errors (e.g. "product with this model already exists.") next to the field.
        const fieldErrors: Errors = {}
        const unmatched: string[] = []
        for (const [key, value] of Object.entries(e.data as Record<string, unknown>)) {
          const message = Array.isArray(value) ? value.join(' ') : String(value)
          const field = PRODUCT_FIELD_MAP[key]
          if (field) fieldErrors[field] = message
          else unmatched.push(message)
        }
        setErrors(fieldErrors)
        setFormError(unmatched.length > 0 ? unmatched.join(' ') : 'Please fix the highlighted fields.')
      } else {
        setFormError(e instanceof ApiError && e.status !== 0 ? e.message : 'Could not reach the server. Try again.')
      }
    } finally {
      setBusy(false)
    }
  }

  const field = (name: keyof ProductFormValues) => ({ value: String(values[name]), onChange: set(name), error: errors[name] })

  return (
    <form onSubmit={onSubmit} className="space-y-6" noValidate data-testid="product-form">
      {formError && (
        <Alert variant="destructive" data-testid="form-error">
          <AlertDescription>{formError}</AlertDescription>
        </Alert>
      )}

      <Section title="Basics">
        <FormField id="name" label="Name" required {...field('name')} />
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField id="model" label="Model code" required hint="Unique, e.g. DB-ETH-250" {...field('model')} />
          <FormField id="serialNumber" label="Serial / lot number" required {...field('serialNumber')} />
        </div>
        <SelectField id="categoryId" label="Category" error={errors.categoryId}>
          <select
            id="categoryId"
            value={values.categoryId}
            onChange={set('categoryId')}
            aria-invalid={errors.categoryId ? true : undefined}
            aria-describedby={errors.categoryId ? 'categoryId-error' : undefined}
            className={`${controlClass} h-9`}
          >
            <option value="">Choose a category…</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </SelectField>
        <SelectField id="description" label="Description" error={errors.description}>
          <textarea
            id="description"
            rows={4}
            value={values.description}
            onChange={set('description')}
            aria-invalid={errors.description ? true : undefined}
            aria-describedby={errors.description ? 'description-error' : undefined}
            className={`${controlClass} py-2`}
          />
        </SelectField>
      </Section>

      <Section title="Price and stock">
        {!product ? (
          <div className="grid gap-4 sm:grid-cols-3">
            <FormField id="price" label="Price (TRY)" type="number" min="0.01" step="0.01" inputMode="decimal" required {...field('price')} />
            <FormField id="stock" label="Starting stock" type="number" min="0" step="1" inputMode="numeric" {...field('stock')} />
            <FormField id="cost" label="Cost (TRY, optional)" type="number" min="0" step="0.01" inputMode="decimal" hint="Empty: 50% of price is used for profit." {...field('cost')} />
          </div>
        ) : (
          <>
            <dl className="grid gap-4 rounded-lg bg-muted/60 p-4 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-muted-foreground">Price</dt>
                <dd className="font-medium">{formatPrice(product.price)}</dd>
                <dd className="text-xs text-muted-foreground">Set by the sales manager.</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Stock</dt>
                <dd className="font-medium">{product.stock}</dd>
                <dd className="text-xs text-muted-foreground">
                  Change it in{' '}
                  <Link to="/manage/categories" className="text-accent-strong underline">
                    Categories &amp; stock
                  </Link>
                  .
                </dd>
              </div>
            </dl>
            <FormField id="cost" label="Cost (TRY, optional)" type="number" min="0" step="0.01" inputMode="decimal" hint="Empty: 50% of price is used for profit." {...field('cost')} />
          </>
        )}
      </Section>

      <Section title="Warranty and distributor">
        <div className="grid gap-4 sm:grid-cols-2">
          <SelectField id="warrantyStatus" label="Warranty">
            <select
              id="warrantyStatus"
              value={values.warrantyStatus}
              onChange={(e) =>
                setValues((v) => ({
                  ...v,
                  warrantyStatus: e.target.value as ProductFormValues['warrantyStatus'],
                  warrantyMonths: e.target.value === 'No warranty' ? '0' : v.warrantyMonths === '0' ? '24' : v.warrantyMonths,
                }))
              }
              className={`${controlClass} h-9`}
            >
              <option value="No warranty">No warranty</option>
              <option value="Under warranty">Under warranty</option>
            </select>
          </SelectField>
          {values.warrantyStatus === 'Under warranty' && (
            <FormField id="warrantyMonths" label="Warranty (months)" type="number" min="1" step="1" inputMode="numeric" {...field('warrantyMonths')} />
          )}
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField id="distributorName" label="Distributor" required {...field('distributorName')} />
          <FormField id="distributorContact" label="Distributor contact (optional)" {...field('distributorContact')} />
        </div>
      </Section>

      <Section title="Details" hint="Optional. Roast and expiry dates are for coffee; capacity is for equipment.">
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField id="brand" label="Brand" {...field('brand')} />
          <FormField id="origin" label="Origin" hint="For coffee, e.g. Ethiopia or Blend" {...field('origin')} />
          <FormField id="roastDate" label="Roast date" type="date" {...field('roastDate')} />
          <FormField id="expiryDate" label="Expiry date" type="date" {...field('expiryDate')} />
          <FormField id="weightCapacity" label="Weight / capacity" hint="e.g. 250 g or Water tank: 1.5 L" {...field('weightCapacity')} />
        </div>
      </Section>

      <Section title="Image">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
          <ProductImage
            src={values.image.trim() ? `/${values.image.trim().replace(/^\//, '')}` : undefined}
            alt="Image preview"
            className="aspect-square w-32 shrink-0 rounded-lg border"
          />
          <div className="flex-1">
            <FormField
              id="image"
              label="Image path (optional)"
              placeholder="products/my-product.webp"
              hint="Put the file in frontend/public/products (see scripts/prepare_product_images.py). Empty shows a placeholder."
              {...field('image')}
            />
          </div>
        </div>
      </Section>

      <div className="flex flex-wrap justify-end gap-2 border-t pt-4">
        <Button asChild variant="outline">
          <Link to="/manage/products">Cancel</Link>
        </Button>
        <Button type="submit" disabled={busy}>
          {busy ? 'Saving…' : creating ? 'Add product' : 'Save changes'}
        </Button>
      </div>
    </form>
  )
}

function Section({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <fieldset className="space-y-4 rounded-xl border bg-card p-5">
      <legend className="px-1 font-semibold">{title}</legend>
      {hint && <p className="-mt-2 text-sm text-muted-foreground">{hint}</p>}
      {children}
    </fieldset>
  )
}

/** Label + any control (select, textarea) + inline error, like FormField does for inputs. */
function SelectField({ id, label, error, children }: { id: string; label: string; error?: string; children: ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {error && (
        <p id={`${id}-error`} className="text-xs text-destructive">
          {error}
        </p>
      )}
    </div>
  )
}
