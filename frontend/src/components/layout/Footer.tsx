import { Container } from '@/components/layout/Container'
import { ApiStatus } from '@/components/ApiStatus'

export function Footer() {
  return (
    <footer className="border-t bg-muted/50 py-6 text-sm text-muted-foreground">
      <Container className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
        <p>© {new Date().getFullYear()} Brewnook. Specialty coffee and brewing gear.</p>
        <ApiStatus />
      </Container>
    </footer>
  )
}
