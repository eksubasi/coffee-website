import { api, setAccessToken } from '@/lib/api'

export type Role = 'customer' | 'sales_manager' | 'product_manager' | 'support_agent'

export interface User {
  id: number
  email: string
  fullName: string
  taxId: string
  homeAddress: string
  role: Role
}

interface ApiUser {
  id: number
  email: string
  full_name: string
  tax_id: string
  home_address: string
  role: Role
}

function toUser(u: ApiUser): User {
  return { id: u.id, email: u.email, fullName: u.full_name, taxId: u.tax_id, homeAddress: u.home_address, role: u.role }
}

export interface RegisterInput {
  email: string
  password: string
  fullName: string
  taxId: string
  homeAddress: string
}

export async function register(input: RegisterInput): Promise<void> {
  await api('/api/auth/register', {
    method: 'POST',
    json: {
      email: input.email,
      password: input.password,
      full_name: input.fullName,
      tax_id: input.taxId,
      home_address: input.homeAddress,
    },
  })
}

export async function login(email: string, password: string): Promise<User> {
  const data = await api<{ access: string; user: ApiUser }>('/api/auth/login', { method: 'POST', json: { email, password } })
  setAccessToken(data.access)
  return toUser(data.user)
}

export async function logout(): Promise<void> {
  try {
    await api('/api/auth/logout', { method: 'POST' })
  } finally {
    setAccessToken(null)
  }
}

export async function fetchMe(): Promise<User> {
  return toUser(await api<ApiUser>('/api/auth/me'))
}
