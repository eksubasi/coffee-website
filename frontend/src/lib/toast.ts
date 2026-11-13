import { create } from 'zustand'

/**
 * Tiny toast system (KAN-30). Call from anywhere — components, stores, API helpers:
 *
 *   toast.success('Added to cart')
 *   toast.error('Could not reach the server.')
 *   toast('Signed out')
 *
 * Toasts are shown by <Toaster />, which is mounted once in the Layout.
 */
export type ToastVariant = 'default' | 'success' | 'error'

export interface Toast {
  id: number
  message: string
  variant: ToastVariant
}

/** How long a toast stays on screen. Errors stay longer so they can be read. */
const DURATION_MS: Record<ToastVariant, number> = { default: 4000, success: 4000, error: 7000 }
/** Older toasts are dropped beyond this, so rapid clicks don't fill the screen. */
const MAX_TOASTS = 3

interface ToastStore {
  toasts: Toast[]
  dismiss: (id: number) => void
}

let nextId = 1

export const useToasts = create<ToastStore>((set) => ({
  toasts: [],
  dismiss: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}))

function show(message: string, variant: ToastVariant): number {
  const id = nextId++
  useToasts.setState((state) => ({ toasts: [...state.toasts, { id, message, variant }].slice(-MAX_TOASTS) }))
  setTimeout(() => useToasts.getState().dismiss(id), DURATION_MS[variant])
  return id
}

export const toast = Object.assign((message: string) => show(message, 'default'), {
  success: (message: string) => show(message, 'success'),
  error: (message: string) => show(message, 'error'),
  dismiss: (id: number) => useToasts.getState().dismiss(id),
})
