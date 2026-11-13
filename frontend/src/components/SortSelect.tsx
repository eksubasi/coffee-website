import { useId } from 'react'
import { useSearchParams } from 'react-router-dom'

import { parseSort, SORT_OPTIONS } from '@/lib/catalog'

/**
 * Sort dropdown whose state lives in the URL (`?sort=`), so a sorted page can be
 * reloaded, bookmarked or shared. Other params (e.g. `?q=`) are kept.
 */
export function SortSelect() {
  const id = useId()
  const [params, setParams] = useSearchParams()
  const sort = parseSort(params.get('sort'))

  function handleChange(value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set('sort', value)
    else next.delete('sort')
    // replace: changing the sort should not add a history entry per click
    setParams(next, { replace: true })
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <label htmlFor={id} className="text-muted-foreground">
        Sort by
      </label>
      <select
        id={id}
        value={sort}
        onChange={(event) => handleChange(event.target.value)}
        className="h-9 rounded-md border bg-background px-3 shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
      >
        {SORT_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}
