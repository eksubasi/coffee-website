import { CircleAlert } from 'lucide-react'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <Alert variant="destructive">
      <CircleAlert />
      <AlertTitle>{message}</AlertTitle>
      {onRetry && (
        <AlertDescription>
          <Button variant="outline" size="sm" className="mt-2" onClick={onRetry}>
            Try again
          </Button>
        </AlertDescription>
      )}
    </Alert>
  )
}
