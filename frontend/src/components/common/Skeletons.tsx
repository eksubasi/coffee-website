import { Skeleton } from '@/components/ui/skeleton'

/** Placeholder with the same shape as ProductCard, shown while products load. */
export function ProductCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-xl border bg-card">
      <Skeleton className="aspect-[4/3] w-full rounded-none" />
      <div className="space-y-3 p-4">
        <Skeleton className="h-3 w-1/4" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-5 w-1/3" />
        <Skeleton className="h-5 w-24" />
      </div>
    </div>
  )
}

/** Grid of card placeholders; uses the same columns as ProductGrid so nothing jumps when data arrives. */
export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div
      className="grid grid-cols-1 gap-4 min-[480px]:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
      role="status"
      aria-busy="true"
      aria-label="Loading products"
    >
      {Array.from({ length: count }, (_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  )
}
