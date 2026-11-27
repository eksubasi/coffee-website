import { useEffect, useState, type FormEvent } from 'react'
import { MessageSquare } from 'lucide-react'
import { Link } from 'react-router-dom'

import { StarDisplay, StarInput } from '@/components/StarRating'
import { EmptyState } from '@/components/common/EmptyState'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { useAuth } from '@/context/auth-context'
import { ApiError } from '@/lib/api'
import {
  COMMENT_MAX_LENGTH,
  commentProblem,
  formatAverage,
  getComments,
  getMyComments,
  getMyRating,
  postComment,
  putRating,
  type MyComment,
  type MyRating,
  type PublicComment,
} from '@/lib/reviews'
import { toast } from '@/lib/toast'
import type { RatingSummaryData } from '@/lib/use-rating-summary'

const dateFormat = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
const formatDate = (iso: string) => (iso ? dateFormat.format(new Date(iso)) : '')

/** Approved comments and (for customers) the rate / comment forms. KAN-58, Req 5. */
export function ProductReviews({
  productId,
  summary,
  onRated,
}: {
  productId: string
  summary: RatingSummaryData
  onRated: () => void
}) {
  return (
    <section className="space-y-6 border-t pt-8" aria-labelledby="reviews-heading" data-testid="reviews">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="reviews-heading" className="text-2xl font-bold">
          Ratings &amp; comments
        </h2>
        <RatingSummary average={summary.average} count={summary.count} />
      </div>

      <div className="grid gap-8 lg:grid-cols-[2fr_1fr]">
        <CommentList productId={productId} />
        <CustomerPanel productId={productId} onRated={onRated} />
      </div>
    </section>
  )
}

export function RatingSummary({ average, count }: { average: number | null; count: number }) {
  if (average === null || count === 0) {
    return (
      <p className="text-sm text-muted-foreground" data-testid="rating-summary">
        No ratings yet
      </p>
    )
  }
  return (
    <p className="flex items-center gap-2 text-sm" data-testid="rating-summary">
      <StarDisplay value={average} />
      <span className="font-semibold">{formatAverage(average)}</span>
      <span className="text-muted-foreground">
        ({count} {count === 1 ? 'rating' : 'ratings'})
      </span>
      <span className="sr-only">out of 5</span>
    </p>
  )
}

function CommentList({ productId }: { productId: string }) {
  const [comments, setComments] = useState<PublicComment[]>([])
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading')
  const [loadingMore, setLoadingMore] = useState(false)

  useEffect(() => {
    let cancelled = false
    getComments(productId, 1)
      .then((result) => {
        if (cancelled) return
        setComments(result.comments)
        setHasNext(result.hasNext)
        setState('ready')
      })
      .catch(() => {
        if (!cancelled) setState('error')
      })
    return () => {
      cancelled = true
    }
  }, [productId])

  const loadMore = async () => {
    setLoadingMore(true)
    try {
      const result = await getComments(productId, page + 1)
      setComments((current) => [...current, ...result.comments])
      setHasNext(result.hasNext)
      setPage(page + 1)
    } catch {
      toast.error('Could not load more comments.')
    } finally {
      setLoadingMore(false)
    }
  }

  if (state === 'loading') {
    return (
      <div className="space-y-3" aria-busy="true" aria-label="Loading comments">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    )
  }
  if (state === 'error') {
    return (
      <Alert variant="destructive">
        <AlertDescription>We couldn’t load the comments. Please try again later.</AlertDescription>
      </Alert>
    )
  }
  if (comments.length === 0) {
    return <EmptyState title="No comments yet" hint="Comments appear here after a product manager approves them." />
  }

  return (
    <div className="space-y-4">
      <ul className="space-y-3" data-testid="comment-list">
        {comments.map((comment) => (
          <li key={comment.id} className="rounded-xl border bg-card p-4" data-testid="comment">
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className="font-medium">{comment.author}</span>
              <time className="text-xs text-muted-foreground" dateTime={comment.createdAt}>
                {formatDate(comment.createdAt)}
              </time>
            </div>
            {/* Rendered as text, never as HTML, so a comment can't inject markup. */}
            <p className="mt-2 whitespace-pre-line break-words text-sm">{comment.text}</p>
          </li>
        ))}
      </ul>
      {hasNext && (
        <Button variant="outline" onClick={loadMore} disabled={loadingMore}>
          {loadingMore ? 'Loading…' : 'Show more comments'}
        </Button>
      )}
    </div>
  )
}

function CustomerPanel({ productId, onRated }: { productId: string; onRated: () => void }) {
  const { status, user } = useAuth()

  if (status === 'loading') return <Skeleton className="h-40 w-full" />

  if (!user) {
    return (
      <Panel>
        <p className="text-sm text-muted-foreground">Bought this product? Log in to rate it and leave a comment.</p>
        <Button asChild variant="outline" size="sm">
          <Link to="/login" state={{ from: `/product/${productId}` }}>
            Log in
          </Link>
        </Button>
      </Panel>
    )
  }
  if (user.role !== 'customer') {
    return (
      <Panel>
        <p className="text-sm text-muted-foreground">Only customers can rate and comment on products.</p>
      </Panel>
    )
  }
  return <CustomerForms productId={productId} onRated={onRated} />
}

function Panel({ children }: { children: React.ReactNode }) {
  return <aside className="h-fit space-y-4 rounded-xl border bg-card p-4">{children}</aside>
}

function CustomerForms({ productId, onRated }: { productId: string; onRated: () => void }) {
  const [rating, setRating] = useState<MyRating>()
  const [mine, setMine] = useState<MyComment[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [text, setText] = useState('')
  const [problem, setProblem] = useState<string>()
  const [posting, setPosting] = useState(false)

  useEffect(() => {
    let cancelled = false
    Promise.all([getMyRating(productId), getMyComments(productId)])
      .then(([r, c]) => {
        if (cancelled) return
        setRating(r)
        setMine(c)
      })
      .catch(() => toast.error('Could not load your rating.'))
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [productId])

  const rate = async (score: number) => {
    setSaving(true)
    try {
      setRating(await putRating(productId, score))
      toast.success('Thanks, your rating was saved.')
      onRated()
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : 'Could not save your rating.')
    } finally {
      setSaving(false)
    }
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const found = commentProblem(text)
    setProblem(found)
    if (found) return
    setPosting(true)
    try {
      const created = await postComment(productId, text.trim())
      setMine((current) => [created, ...current])
      setText('')
      toast.success('Comment sent. It will appear after a product manager approves it.')
    } catch (err) {
      setProblem(err instanceof ApiError ? err.message : 'Could not send your comment.')
    } finally {
      setPosting(false)
    }
  }

  if (loading || !rating) return <Skeleton className="h-40 w-full" />

  if (!rating.canRate) {
    return (
      <Panel>
        <p className="flex items-start gap-2 text-sm text-muted-foreground" data-testid="not-delivered-note">
          <MessageSquare className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          You can rate and comment once this product has been delivered to you.
        </p>
        <OwnComments comments={mine} />
      </Panel>
    )
  }

  const pending = mine.filter((c) => c.status === 'pending')
  const rejected = mine.filter((c) => c.status === 'rejected')

  return (
    <Panel>
      <div className="space-y-2">
        <p className="text-sm font-medium">{rating.score ? 'Your rating' : 'Rate this product'}</p>
        <StarInput value={rating.score} onChange={rate} disabled={saving} label="Your rating" />
      </div>

      <form onSubmit={submit} className="space-y-2" noValidate>
        <Label htmlFor="comment-text">Your comment</Label>
        <Textarea
          id="comment-text"
          value={text}
          maxLength={COMMENT_MAX_LENGTH}
          rows={4}
          onChange={(e) => {
            setText(e.target.value)
            if (problem) setProblem(undefined)
          }}
          aria-invalid={problem ? true : undefined}
          aria-describedby={problem ? 'comment-error' : undefined}
          placeholder="What did you think of it?"
        />
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            {text.length}/{COMMENT_MAX_LENGTH}
          </span>
        </div>
        {problem && (
          <p id="comment-error" className="text-xs text-destructive">
            {problem}
          </p>
        )}
        <Button type="submit" disabled={posting} data-testid="send-comment">
          {posting ? 'Sending…' : 'Send comment'}
        </Button>
      </form>

      {pending.length > 0 && (
        <Alert data-testid="pending-notice">
          <AlertDescription>
            {pending.length === 1 ? 'Your comment is' : `${pending.length} of your comments are`} waiting for approval. Only
            you can see {pending.length === 1 ? 'it' : 'them'} until then.
          </AlertDescription>
        </Alert>
      )}
      {rejected.length > 0 && (
        <Alert variant="destructive">
          <AlertDescription>
            {rejected.length === 1 ? 'One of your comments was' : `${rejected.length} of your comments were`} not approved.
          </AlertDescription>
        </Alert>
      )}
    </Panel>
  )
}

/** Shown when the customer can't comment yet but still has older comments (e.g. after a refund). */
function OwnComments({ comments }: { comments: MyComment[] }) {
  if (comments.length === 0) return null
  return (
    <ul className="space-y-2 text-sm">
      {comments.map((c) => (
        <li key={c.id} className="rounded-md border p-2">
          <p className="break-words">{c.text}</p>
          <p className="mt-1 text-xs text-muted-foreground">{c.status}</p>
        </li>
      ))}
    </ul>
  )
}
