import { createContext, useContext } from 'react'

import type { RegisterInput, User } from '@/lib/auth'

export interface AuthState {
  /** `loading` while we try to restore a session from the refresh cookie on page load. */
  status: 'loading' | 'authenticated' | 'anonymous'
  user: User | null
  login: (email: string, password: string) => Promise<User>
  register: (input: RegisterInput) => Promise<User>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthState | null>(null)

export function useAuth(): AuthState {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside <AuthProvider>')
  return value
}
