import { Link } from 'react-router-dom'

import { ProductImage } from '@/components/ProductImage'
import { StockBadge } from '@/components/temp-kan30/StockBadge'
import { Card, CardContent } from '@/components/ui/card'
import { formatPrice } from '@/lib/utils'
import type { Product } from '@/types'

export function ProductCard({ product }: { product: Product }) {
  return (
    <Link
      to={`/product/${product.id}`}
      className="group block rounded-xl focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
      data-testid="product-card"
    >
      <Card className="h-full gap-0 overflow-hidden py-0 transition-shadow group-hover:shadow-md">
        <ProductImage src={product.imageUrl} alt={product.name} className="aspect-[4/3] w-full" />
        <CardContent className="space-y-2 p-4">
          <h3 className="font-medium leading-snug group-hover:text-primary">{product.name}</h3>
          <p className="text-lg font-semibold text-primary">{formatPrice(product.price)}</p>
          <StockBadge stock={product.stock} />
        </CardContent>
      </Card>
    </Link>
  )
}
