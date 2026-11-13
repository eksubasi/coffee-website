import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react'
import { useState, type ReactNode } from 'react'

import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

type SortValue = string | number | boolean | Date | null | undefined

export interface Column<T> {
  /** Unique id for the column (also used as the sort key). */
  id: string
  header: string
  /** What to show in the cell. Defaults to `sortValue`. */
  cell?: (row: T) => ReactNode
  /** Value used for sorting; give it to make the column sortable. */
  sortValue?: (row: T) => SortValue
  align?: 'left' | 'right' | 'center'
  /** Extra classes for the column's cells, e.g. a width. */
  className?: string
}

export interface SortState {
  columnId: string
  direction: 'asc' | 'desc'
}

interface DataTableProps<T> {
  columns: Column<T>[]
  rows: T[]
  rowKey: (row: T) => string | number
  /** Describes the table for screen readers, e.g. "Products". */
  caption: string
  pageSize?: number
  initialSort?: SortState
  loading?: boolean
  /** Shown instead of the table body when there are no rows. */
  empty?: ReactNode
}

const collator = new Intl.Collator('tr', { numeric: true, sensitivity: 'base' })

const isEmpty = (v: SortValue) => v === null || v === undefined || v === ''

function compare(a: SortValue, b: SortValue): number {
  if (a instanceof Date && b instanceof Date) return a.getTime() - b.getTime()
  if (typeof a === 'number' && typeof b === 'number') return a - b
  if (typeof a === 'boolean' && typeof b === 'boolean') return Number(a) - Number(b)
  return collator.compare(String(a), String(b))
}

/** Sorts a copy of `rows`. Empty values always go last, whatever the direction. */
function sortRows<T>(rows: T[], getValue: (row: T) => SortValue, direction: SortState['direction']): T[] {
  return [...rows].sort((rowA, rowB) => {
    const a = getValue(rowA)
    const b = getValue(rowB)
    if (isEmpty(a) || isEmpty(b)) return Number(isEmpty(a)) - Number(isEmpty(b))
    return direction === 'asc' ? compare(a, b) : compare(b, a)
  })
}

const alignClass = { left: 'text-left', right: 'text-right', center: 'text-center' }

/**
 * Table for the manager area (KAN-49): click a header to sort, pages of `pageSize` rows.
 * Sorting and paging happen in the browser, which suits our data sizes (tens to hundreds of rows).
 */
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  caption,
  pageSize = 10,
  initialSort,
  loading = false,
  empty,
}: DataTableProps<T>) {
  const [sort, setSort] = useState<SortState | undefined>(initialSort)
  const [page, setPage] = useState(0)

  const sortColumn = sort && columns.find((c) => c.id === sort.columnId)
  const sorted = sort && sortColumn?.sortValue ? sortRows(rows, sortColumn.sortValue, sort.direction) : rows

  const pageCount = Math.max(1, Math.ceil(sorted.length / pageSize))
  const currentPage = Math.min(page, pageCount - 1) // rows can shrink (filter, delete) under us
  const start = currentPage * pageSize
  const visible = sorted.slice(start, start + pageSize)

  function toggleSort(columnId: string) {
    setSort((current) =>
      current?.columnId === columnId
        ? { columnId, direction: current.direction === 'asc' ? 'desc' : 'asc' }
        : { columnId, direction: 'asc' },
    )
    setPage(0)
  }

  return (
    <div className="overflow-hidden rounded-xl border bg-card" data-testid="data-table">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <caption className="sr-only">{caption}</caption>
          <thead className="border-b bg-muted/60">
            <tr>
              {columns.map((column) => {
                const direction = sort?.columnId === column.id ? sort.direction : undefined
                const active = direction !== undefined
                const ariaSort = direction === 'asc' ? 'ascending' : direction === 'desc' ? 'descending' : 'none'
                const SortIcon = direction === 'asc' ? ArrowUp : direction === 'desc' ? ArrowDown : ArrowUpDown
                return (
                  <th
                    key={column.id}
                    scope="col"
                    aria-sort={column.sortValue ? ariaSort : undefined}
                    className={cn(
                      'whitespace-nowrap px-4 py-3 font-medium text-muted-foreground',
                      alignClass[column.align ?? 'left'],
                      column.className,
                    )}
                  >
                    {column.sortValue ? (
                      <button
                        type="button"
                        onClick={() => toggleSort(column.id)}
                        className={cn(
                          '-mx-1 inline-flex items-center gap-1 rounded px-1 hover:text-foreground',
                          active && 'text-foreground',
                        )}
                      >
                        {column.header}
                        <SortIcon className={cn('size-3.5', !active && 'opacity-50')} aria-hidden="true" />
                      </button>
                    ) : (
                      column.header
                    )}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading &&
              Array.from({ length: Math.min(pageSize, 5) }, (_, i) => (
                <tr key={`loading-${i}`} aria-hidden="true">
                  {columns.map((column) => (
                    <td key={column.id} className="px-4 py-3">
                      <Skeleton className="h-4 w-full max-w-32" />
                    </td>
                  ))}
                </tr>
              ))}
            {!loading &&
              visible.map((row) => (
                <tr key={rowKey(row)} className="hover:bg-muted/40">
                  {columns.map((column) => (
                    <td
                      key={column.id}
                      className={cn('px-4 py-3 align-middle', alignClass[column.align ?? 'left'], column.className)}
                    >
                      {column.cell ? column.cell(row) : String(column.sortValue?.(row) ?? '')}
                    </td>
                  ))}
                </tr>
              ))}
            {!loading && rows.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="p-4">
                  {empty ?? <p className="py-6 text-center text-muted-foreground">Nothing to show yet.</p>}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {!loading && rows.length > pageSize && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-t px-4 py-3 text-sm">
          <p className="text-muted-foreground" aria-live="polite">
            Showing {start + 1}–{Math.min(start + pageSize, sorted.length)} of {sorted.length}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(currentPage - 1)}
              disabled={currentPage === 0}
              aria-label="Previous page"
            >
              <ChevronLeft aria-hidden="true" />
            </Button>
            <span className="tabular-nums">
              Page {currentPage + 1} of {pageCount}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(currentPage + 1)}
              disabled={currentPage >= pageCount - 1}
              aria-label="Next page"
            >
              <ChevronRight aria-hidden="true" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
