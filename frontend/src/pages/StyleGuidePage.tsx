import { Coffee, Heart } from 'lucide-react'
import type { ReactNode } from 'react'

import { EmptyState } from '@/components/common/EmptyState'
import { PriceTag } from '@/components/common/PriceTag'
import { ProductCard } from '@/components/common/ProductCard'
import { ProductCardSkeleton } from '@/components/common/Skeletons'
import { StockBadge } from '@/components/common/StockBadge'
import { Button } from '@/components/ui/button'
import { toast } from '@/lib/toast'
import type { Product } from '@/types'

/** Dev-only page (/styleguide) showing the design tokens and shared components. See STYLE_GUIDE.md. */

const colors = [
  ['background', 'bg-background'],
  ['card', 'bg-card'],
  ['primary', 'bg-primary'],
  ['secondary', 'bg-secondary'],
  ['muted', 'bg-muted'],
  ['accent', 'bg-accent'],
  ['accent-strong', 'bg-accent-strong'],
  ['success', 'bg-success'],
  ['warning', 'bg-warning'],
  ['destructive', 'bg-destructive'],
  ['border', 'bg-border'],
] as const

const sample: Product = {
  id: 'demo',
  categoryId: '1',
  categoryName: 'Coffee Beans',
  name: 'Kenya AA Single Origin, 250 g',
  model: 'DEMO-1',
  serialNumber: 'LOT-0001',
  description: 'Bright and juicy with blackcurrant notes.',
  stock: 14,
  price: 590,
  warranty: 'No warranty',
  distributor: 'Demo Roasters',
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="space-y-4">
      <h2 className="type-heading border-b pb-2">{title}</h2>
      {children}
    </section>
  )
}

export function StyleGuidePage() {
  return (
    <div className="space-y-12">
      <div>
        <h1 className="type-title">Style guide</h1>
        <p className="type-caption">Design tokens and shared components (KAN-30). Only available in development.</p>
      </div>

      <Section title="Colors">
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6">
          {colors.map(([name, bg]) => (
            <li key={name} className="overflow-hidden rounded-lg border bg-card text-sm">
              <div className={`h-14 ${bg}`} />
              <p className="px-3 py-2 font-mono text-xs">{name}</p>
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Typography">
        <div className="space-y-3">
          <p className="type-display">type-display — Coffee worth slowing down for</p>
          <p className="type-title">type-title — Page title</p>
          <p className="type-heading">type-heading — Section heading</p>
          <p className="type-body">type-body — Body text for descriptions and paragraphs.</p>
          <p className="type-caption">type-caption — Secondary information and hints.</p>
        </div>
      </Section>

      <Section title="Buttons">
        <div className="flex flex-wrap gap-3">
          <Button>Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="destructive">Delete</Button>
          <Button disabled>Disabled</Button>
        </div>
      </Section>

      <Section title="PriceTag">
        <div className="flex flex-wrap items-end gap-8">
          <PriceTag price={590} size="sm" />
          <PriceTag price={590} />
          <PriceTag price={590} size="lg" />
          <PriceTag price={472} originalPrice={590} />
        </div>
      </Section>

      <Section title="StockBadge">
        <div className="flex flex-wrap gap-3">
          <StockBadge stock={14} />
          <StockBadge stock={3} />
          <StockBadge stock={0} />
        </div>
      </Section>

      <Section title="ProductCard and skeleton">
        <div className="grid max-w-3xl grid-cols-1 gap-4 min-[480px]:grid-cols-2 lg:grid-cols-3">
          <ProductCard product={sample} />
          <ProductCard product={{ ...sample, id: 'demo-2', name: 'Hand Grinder', stock: 0 }} />
          <ProductCardSkeleton />
        </div>
      </Section>

      <Section title="EmptyState">
        <div className="grid gap-4 md:grid-cols-2">
          <EmptyState title="No products in this category yet" hint="Try another category." />
          <EmptyState
            icon={Heart}
            title="Your wishlist is empty"
            hint="Tap the heart on a product to save it."
            action={<Button size="sm">Browse coffee</Button>}
          />
        </div>
      </Section>

      <Section title="Toast">
        <div className="flex flex-wrap gap-3">
          <Button variant="outline" onClick={() => toast.success('Added to cart')}>
            Success toast
          </Button>
          <Button variant="outline" onClick={() => toast.error('Could not reach the server.')}>
            Error toast
          </Button>
          <Button variant="outline" onClick={() => toast('Signed out')}>
            <Coffee aria-hidden="true" /> Plain toast
          </Button>
        </div>
      </Section>
    </div>
  )
}
