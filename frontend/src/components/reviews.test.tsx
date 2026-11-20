import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ProductReviews, RatingSummary } from '@/components/ProductReviews'
import { StarInput } from '@/components/StarRating'
import { AuthContext, type AuthState } from '@/context/auth-context'

vi.mock('@/lib/reviews', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/reviews')>()),
  getComments: vi.fn(),
  getMyRating: vi.fn(),
  getMyComments: vi.fn(),
  postComment: vi.fn(),
  putRating: vi.fn(),
}))
import * as reviews from '@/lib/reviews'

const auth = (user: AuthState['user']): AuthState => ({
  status: user ? 'authenticated' : 'anonymous',
  user,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
})
const customer = { id: 1, email: 'c@x.dev', fullName: 'C', role: 'customer' } as unknown as AuthState['user']
const manager = { id: 2, email: 'm@x.dev', fullName: 'M', role: 'product_manager' } as unknown as AuthState['user']

function renderReviews(user: AuthState['user']) {
  vi.mocked(reviews.getComments).mockResolvedValue({ comments: [], count: 0, hasNext: false })
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={auth(user)}>
        <ProductReviews productId="3" summary={{ average: null, count: 0 }} onRated={vi.fn()} />
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

afterEach(() => vi.clearAllMocks())

describe('RatingSummary', () => {
  it('says there are no ratings yet', () => {
    render(<RatingSummary average={null} count={0} />)
    expect(screen.getByText('No ratings yet')).toBeInTheDocument()
  })

  it('shows the average and a singular/plural count', () => {
    const { rerender } = render(<RatingSummary average={4} count={1} />)
    expect(screen.getByText('(1 rating)')).toBeInTheDocument()
    rerender(<RatingSummary average={4.5} count={2} />)
    expect(screen.getByText('4.5')).toBeInTheDocument()
    expect(screen.getByText('(2 ratings)')).toBeInTheDocument()
  })
})

describe('StarInput', () => {
  it('reports the clicked score and marks it checked', async () => {
    const onChange = vi.fn()
    render(<StarInput value={2} onChange={onChange} label="Your rating" />)
    expect(screen.getByRole('radio', { name: '2 stars' })).toBeChecked()
    await userEvent.click(screen.getByRole('radio', { name: '5 stars' }))
    expect(onChange).toHaveBeenCalledWith(5)
  })

  it('cannot be clicked while disabled', async () => {
    const onChange = vi.fn()
    render(<StarInput value={null} onChange={onChange} disabled label="Your rating" />)
    await userEvent.click(screen.getByRole('radio', { name: '3 stars' }))
    expect(onChange).not.toHaveBeenCalled()
  })
})

describe('ProductReviews gating', () => {
  it('asks guests to log in and shows no form', async () => {
    renderReviews(null)
    expect(await screen.findByRole('link', { name: 'Log in' })).toBeInTheDocument()
    expect(screen.queryByLabelText('Your comment')).not.toBeInTheDocument()
  })

  it('tells staff that only customers can comment', async () => {
    renderReviews(manager)
    expect(await screen.findByText(/Only customers can rate and comment/)).toBeInTheDocument()
  })

  it('hides the form from a customer whose order was not delivered', async () => {
    vi.mocked(reviews.getMyRating).mockResolvedValue({ score: null, canRate: false })
    vi.mocked(reviews.getMyComments).mockResolvedValue([])
    renderReviews(customer)
    expect(await screen.findByTestId('not-delivered-note')).toBeInTheDocument()
    expect(screen.queryByLabelText('Your comment')).not.toBeInTheDocument()
  })

  it('lets a customer with a delivered order send a comment and shows the pending notice', async () => {
    vi.mocked(reviews.getMyRating).mockResolvedValue({ score: null, canRate: true })
    vi.mocked(reviews.getMyComments).mockResolvedValue([])
    vi.mocked(reviews.postComment).mockResolvedValue({ id: 1, text: 'Lovely', status: 'pending', createdAt: '2026-11-20T10:00:00Z' })
    renderReviews(customer)
    await userEvent.type(await screen.findByLabelText('Your comment'), 'Lovely')
    await userEvent.click(screen.getByTestId('send-comment'))
    await waitFor(() => expect(reviews.postComment).toHaveBeenCalledWith('3', 'Lovely'))
    expect(await screen.findByTestId('pending-notice')).toHaveTextContent(/waiting for approval/)
  })

  it('does not send an empty comment', async () => {
    vi.mocked(reviews.getMyRating).mockResolvedValue({ score: null, canRate: true })
    vi.mocked(reviews.getMyComments).mockResolvedValue([])
    renderReviews(customer)
    await userEvent.click(await screen.findByTestId('send-comment'))
    expect(screen.getByText('Write a comment first.')).toBeInTheDocument()
    expect(reviews.postComment).not.toHaveBeenCalled()
  })
})
