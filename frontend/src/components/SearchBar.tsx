import { Search, X } from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'

import { cn } from '@/lib/utils'

/** How long to wait after the last keystroke before searching. */
const SEARCH_DEBOUNCE_MS = 300

/**
 * Navbar search box. Typing searches after a short pause (debounced); Enter searches at once.
 * The query lives in the URL as /search?q=..., so results survive reloads and the back button.
 */
export function SearchBar({ className }: { className?: string }) {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const [params] = useSearchParams()

  const onSearchPage = pathname === '/search'
  const urlQuery = onSearchPage ? (params.get('q') ?? '') : ''

  const [text, setText] = useState(urlQuery)
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined)

  // Keep the box in step with the URL when it changes from outside (back/forward, links,
  // leaving the search page). Done during render, React's recommended way to adjust state
  // when a value it depends on changes.
  const [seenUrlQuery, setSeenUrlQuery] = useState(urlQuery)
  if (urlQuery !== seenUrlQuery) {
    setSeenUrlQuery(urlQuery)
    if (urlQuery.trim() !== text.trim()) setText(urlQuery)
  }

  // A pending search must not fire after the user has navigated somewhere else.
  useEffect(() => () => clearTimeout(timer.current), [pathname])

  function search(value: string) {
    clearTimeout(timer.current)
    const q = value.trim()
    if (q === urlQuery.trim()) return

    if (!q) {
      // Cleared the box: stay on the search page but drop the query.
      if (onSearchPage) navigate({ pathname: '/search', search: withQuery(params, '') }, { replace: true })
      return
    }

    // On the search page, refine in place (replace) and keep the chosen sort.
    // From any other page, open the search page as a new history entry.
    navigate(
      { pathname: '/search', search: withQuery(onSearchPage ? params : new URLSearchParams(), q) },
      { replace: onSearchPage },
    )
  }

  function handleChange(value: string) {
    setText(value)
    clearTimeout(timer.current)
    timer.current = setTimeout(() => search(value), SEARCH_DEBOUNCE_MS)
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (text.trim()) search(text)
  }

  return (
    <form role="search" onSubmit={handleSubmit} className={cn('relative', className)}>
      <label htmlFor="site-search" className="sr-only">
        Search products
      </label>
      <Search
        className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
        aria-hidden="true"
      />
      <input
        id="site-search"
        type="search"
        value={text}
        onChange={(event) => handleChange(event.target.value)}
        placeholder="Search coffee, machines…"
        autoComplete="off"
        className="h-9 w-full rounded-md border bg-background pl-9 pr-9 text-sm shadow-xs outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 [&::-webkit-search-cancel-button]:hidden"
      />
      {text && (
        <button
          type="button"
          onClick={() => handleChange('')}
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-muted-foreground hover:text-foreground"
          aria-label="Clear search"
        >
          <X className="size-4" aria-hidden="true" />
        </button>
      )}
    </form>
  )
}

function withQuery(params: URLSearchParams, q: string): string {
  const next = new URLSearchParams(params)
  if (q) next.set('q', q)
  else next.delete('q')
  const query = next.toString()
  return query ? `?${query}` : ''
}
