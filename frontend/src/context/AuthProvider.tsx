import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'

import { AuthContext, type AuthState } from '@/context/auth-context'
import { refreshAccessToken } from '@/lib/api'
import * as authApi from '@/lib/auth'
import { isApplyingServerCart, loadServerCart, mergeGuestCartIntoServer, pushCartToServer } from '@/lib/cart-sync'
import { useCart } from '@/store/cart'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<Pick<AuthState, 'status' | 'user'>>({ status: 'loading', user: null })
  const user = state.user
  const usesServerCart = user?.role === 'customer'

  // Restore the session on page load: the refresh cookie gives us a new access token.
  useEffect(() => {
    let cancelled = false
    void (async () => {
      const token = await refreshAccessToken()
      if (!token) return !cancelled && setState({ status: 'anonymous', user: null })
      try {
        const me = await authApi.fetchMe()
        if (me.role === 'customer') await loadServerCart().catch(() => undefined)
        if (!cancelled) setState({ status: 'authenticated', user: me })
      } catch {
        if (!cancelled) setState({ status: 'anonymous', user: null })
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  // While a customer is logged in, every cart change is saved to the server cart (debounced).
  const timer = useRef<number>(undefined)
  useEffect(() => {
    if (!usesServerCart) return
    const unsubscribe = useCart.subscribe((cart, previous) => {
      if (isApplyingServerCart() || cart.items === previous.items) return
      window.clearTimeout(timer.current)
      timer.current = window.setTimeout(() => void pushCartToServer(useCart.getState().items).catch(() => undefined), 300)
    })
    return () => {
      unsubscribe()
      window.clearTimeout(timer.current)
    }
  }, [usesServerCart])

  const login = useCallback(async (email: string, password: string) => {
    const me = await authApi.login(email, password)
    // Guest cart -> server cart (Req 4: the item added before login is still there after login).
    if (me.role === 'customer') await mergeGuestCartIntoServer().catch(() => undefined)
    setState({ status: 'authenticated', user: me })
    return me
  }, [])

  const register = useCallback(
    async (input: authApi.RegisterInput) => {
      await authApi.register(input)
      return login(input.email, input.password)
    },
    [login],
  )

  const logout = useCallback(async () => {
    await authApi.logout().catch(() => undefined)
    useCart.setState({ items: [] }) // the server keeps the cart; the next visitor must not see it
    setState({ status: 'anonymous', user: null })
  }, [])

  const value = useMemo<AuthState>(() => ({ ...state, login, register, logout }), [state, login, register, logout])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
