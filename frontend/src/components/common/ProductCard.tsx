import { Link } from 'react-router-dom'

import { PriceTag } from '@/components/common/PriceTag'
import { StockBadge } from '@/components/common/StockBadge'
import { ProductImage } from '@/components/ProductImage'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { Product } from '@/types'

/** Product tile for grids (category, search, wishlist). The whole card links to the product page. */
export function ProductCard({ product }: { product: Product }) {
  const soldOut = product.stock <= 0

  return (
    <Link
      to={`/product/${product.id}`}
      className="group block h-full rounded-xl focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
      data-testid="product-card"
    >
      <Card className="h-full gap-0 overflow-hidden py-0 transition-shadow group-hover:shadow-md">
        <ProductImage
          src={product.imageUrl}
          alt={product.name}
          className={cn('aspect-[4/3] w-full transition-transform group-hover:scale-[1.02]', soldOut && 'opacity-60')}
        />
        <CardContent className="flex flex-1 flex-col gap-2 p-4">
          {product.categoryName && (
            <p className="text-xs font-medium uppercase tracking-wide text-accent-strong">{product.categoryName}</p>
          )}
          <h3 className="font-medium leading-snug group-hover:text-primary">{product.name}</h3>
          <div className="mt-auto space-y-2 pt-1">
            <PriceTag price={product.price} />
            <StockBadge stock={product.stock} />
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
