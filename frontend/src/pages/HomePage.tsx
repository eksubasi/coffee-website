import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import { ErrorState } from '@/components/ErrorState'
import { EmptyState } from '@/components/temp-kan30/EmptyState'
import { Skeleton } from '@/components/ui/skeleton'
import { getCategories } from '@/lib/catalog'
import { useAsync } from '@/lib/use-async'

export function HomePage() {
  const { data: categories, error, loading, reload } = useAsync(getCategories, [])

  return (
    <div className="space-y-10">
      <section className="rounded-2xl bg-primary px-6 py-12 text-primary-foreground sm:px-12 sm:py-16">
        <h1 className="max-w-xl text-3xl font-bold leading-tight sm:text-4xl">
          Coffee worth slowing down for.
        </h1>
        <p className="mt-3 max-w-lg text-primary-foreground/80">
          Freshly roasted beans, brewing gear and gifts. Pick a category to start browsing.
        </p>
      </section>

      <section aria-labelledby="categories-heading">
        <h2 id="categories-heading" className="mb-4 text-xl font-semibold">
          Shop by category
        </h2>

        {loading && (
          <div
            className="grid grid-cols-1 gap-4 min-[480px]:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
            aria-busy="true"
            aria-label="Loading categories"
          >
            {Array.from({ length: 7 }, (_, i) => (
              <Skeleton key={i} className="h-28 rounded-xl" />
            ))}
          </div>
        )}

        {error && <ErrorState message="We couldn't load the categories." onRetry={reload} />}

        {!loading && !error && categories?.length === 0 && (
          <EmptyState title="No categories yet" hint="Check back soon." />
        )}

        {categories && categories.length > 0 && (
          <ul className="grid grid-cols-1 gap-4 min-[480px]:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {categories.map((category) => (
              <li key={category.id}>
                <Link
                  to={`/category/${category.id}`}
                  data-testid="category-tile"
                  className="group flex h-full flex-col justify-between gap-3 rounded-xl border bg-card p-5 shadow-sm transition-shadow hover:shadow-md"
                >
                  <div>
                    <h3 className="font-semibold group-hover:text-primary">{category.name}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">{category.description}</p>
                  </div>
                  <span className="flex items-center gap-1 text-sm font-medium text-accent">
                    Browse <ArrowRight className="size-4" aria-hidden="true" />
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
