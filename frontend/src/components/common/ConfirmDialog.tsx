import { useState, type ReactNode } from 'react'

import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'

interface ConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: ReactNode
  confirmLabel?: string
  cancelLabel?: string
  /** Red confirm button, for deleting and other actions that can't be undone. */
  destructive?: boolean
  /**
   * Runs when the user confirms. If it returns a promise, the dialog stays open with a busy
   * button until it settles, and closes only on success (so a failed delete can be retried).
   */
  onConfirm: () => void | Promise<unknown>
}

/**
 * "Are you sure?" dialog for the manager area (KAN-49): deleting products and categories,
 * cancelling orders, approving refunds... Focus is trapped inside and Escape cancels.
 *
 *   const [target, setTarget] = useState<Product>()
 *   <ConfirmDialog
 *     open={!!target} onOpenChange={(open) => !open && setTarget(undefined)}
 *     title={`Delete ${target?.name}?`} description="This cannot be undone."
 *     confirmLabel="Delete" destructive onConfirm={() => deleteProduct(target!.id)}
 *   />
 */
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  destructive = false,
  onConfirm,
}: ConfirmDialogProps) {
  const [busy, setBusy] = useState(false)

  async function handleConfirm() {
    setBusy(true)
    try {
      await onConfirm()
      onOpenChange(false)
    } catch {
      // The caller shows the error (e.g. with toast.error); keep the dialog open so they can retry.
    } finally {
      setBusy(false)
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={(next) => !busy && onOpenChange(next)}>
      <AlertDialogContent data-testid="confirm-dialog">
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          {description && <AlertDialogDescription>{description}</AlertDialogDescription>}
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={busy}>{cancelLabel}</AlertDialogCancel>
          {/* A plain Button (not AlertDialogAction), so the dialog doesn't close before onConfirm finishes. */}
          <Button variant={destructive ? 'destructive' : 'default'} onClick={() => void handleConfirm()} disabled={busy}>
            {busy ? 'Working…' : confirmLabel}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
