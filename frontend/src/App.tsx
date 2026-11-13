import type { ReactElement } from 'react'
import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom'

import { ProtectedRoute, RoleRoute } from '@/components/auth/ProtectedRoute'
import { StaffRoute } from '@/components/auth/StaffRoute'
import { Layout } from '@/components/layout/Layout'
import { ManageLayout } from '@/components/manage/ManageLayout'
import { TooltipProvider } from '@/components/ui/tooltip'
import { AuthProvider } from '@/context/AuthProvider'
import { MANAGE_SECTIONS } from '@/lib/manage-nav'
import { CartPage } from '@/pages/CartPage'
import { CategoryPage } from '@/pages/CategoryPage'
import { CheckoutPage } from '@/pages/CheckoutPage'
import { HomePage } from '@/pages/HomePage'
import { LoginPage } from '@/pages/LoginPage'
import { ComingSoonPage } from '@/pages/manage/ComingSoonPage'
import { ManageHomePage } from '@/pages/manage/ManageHomePage'
import { ManageProductsPage } from '@/pages/manage/ManageProductsPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { OrderConfirmationPage } from '@/pages/OrderConfirmationPage'
import { OrderDetailPage } from '@/pages/OrderDetailPage'
import { OrdersPage } from '@/pages/OrdersPage'
import { ProductPage } from '@/pages/ProductPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { SearchPage } from '@/pages/SearchPage'
import { StyleGuidePage } from '@/pages/StyleGuidePage'

/** Manager pages that exist so far; every other section in MANAGE_SECTIONS shows a placeholder. */
const MANAGE_PAGES: Partial<Record<string, ReactElement>> = {
  products: <ManageProductsPage />,
}

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'category/:id', element: <CategoryPage /> },
      { path: 'product/:id', element: <ProductPage /> },
      { path: 'search', element: <SearchPage /> },
      { path: 'cart', element: <CartPage /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
      {
        // Logged in AND a customer: checkout and order history are customer features.
        element: <ProtectedRoute />,
        children: [
          {
            element: <RoleRoute roles={['customer']} />,
            children: [
              { path: 'checkout', element: <CheckoutPage /> },
              { path: 'checkout/success/:id', element: <OrderConfirmationPage /> },
              { path: 'orders', element: <OrdersPage /> },
              { path: 'orders/:id', element: <OrderDetailPage /> },
            ],
          },
        ],
      },
      // Dev-only design system reference (KAN-30); not part of the production build's routes.
      ...(import.meta.env.DEV ? [{ path: 'styleguide', element: <StyleGuidePage /> }] : []),
      { path: '*', element: <NotFoundPage /> },
    ],
  },
  {
    // Manager area (KAN-49): staff only, own layout with a role-based sidebar.
    path: '/manage',
    element: <StaffRoute />,
    children: [
      {
        element: <ManageLayout />,
        children: [
          { index: true, element: <ManageHomePage /> },
          ...MANAGE_SECTIONS.map((section) => ({
            path: section.path,
            element: <StaffRoute roles={section.roles} />,
            children: [{ index: true, element: MANAGE_PAGES[section.path] ?? <ComingSoonPage section={section} /> }],
          })),
          { path: '*', element: <Navigate to="/manage" replace /> },
        ],
      },
    ],
  },
])

export default function App() {
  return (
    <TooltipProvider delayDuration={150}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </TooltipProvider>
  )
}
