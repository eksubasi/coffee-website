import { Outlet, ScrollRestoration } from 'react-router-dom'

import { Toaster } from '@/components/common/Toaster'
import { Container } from '@/components/layout/Container'
import { Footer } from '@/components/layout/Footer'
import { Navbar } from '@/components/layout/Navbar'

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-foreground"
      >
        Skip to content
      </a>
      <Navbar />
      <main id="main" className="flex-1 py-8">
        <Container>
          <Outlet />
        </Container>
      </main>
      <Footer />
      <Toaster />
      <ScrollRestoration />
    </div>
  )
}
