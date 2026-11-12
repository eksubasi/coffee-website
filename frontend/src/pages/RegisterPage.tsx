import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { FormField } from '@/components/FormField'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/context/auth-context'
import { ApiError } from '@/lib/api'

type Errors = Partial<Record<'fullName' | 'email' | 'taxId' | 'homeAddress' | 'password', string>>

/** Maps DRF field names to our form field names. */
const FIELD_MAP: Record<string, keyof Errors> = {
  full_name: 'fullName',
  email: 'email',
  tax_id: 'taxId',
  home_address: 'homeAddress',
  password: 'password',
}

export function RegisterPage() {
  const { status, register } = useAuth()
  const navigate = useNavigate()
  const from = (useLocation().state as { from?: string } | null)?.from ?? '/'
  const [form, setForm] = useState({ fullName: '', email: '', taxId: '', homeAddress: '', password: '' })
  const [errors, setErrors] = useState<Errors>({})
  const [formError, setFormError] = useState<string>()
  const [busy, setBusy] = useState(false)

  if (status === 'authenticated') return <Navigate to={from} replace />

  const set = (key: keyof typeof form) => (e: { target: { value: string } }) => setForm((f) => ({ ...f, [key]: e.target.value }))

  function validate(): Errors {
    const next: Errors = {}
    if (!form.fullName.trim()) next.fullName = 'Enter your name.'
    if (!/^\S+@\S+\.\S+$/.test(form.email.trim())) next.email = 'Enter a valid email address.'
    if (!/^\d{10,11}$/.test(form.taxId.trim())) next.taxId = 'Tax ID must be 10 or 11 digits.'
    if (!form.homeAddress.trim()) next.homeAddress = 'Enter your address.'
    if (form.password.length < 8) next.password = 'Password must be at least 8 characters.'
    return next
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(undefined)
    const found = validate()
    setErrors(found)
    if (Object.keys(found).length > 0) return

    setBusy(true)
    try {
      await register({ ...form, email: form.email.trim(), fullName: form.fullName.trim(), taxId: form.taxId.trim(), homeAddress: form.homeAddress.trim() })
      navigate(from, { replace: true })
    } catch (e) {
      if (e instanceof ApiError && e.status === 400 && e.data && typeof e.data === 'object') {
        // Show the backend's field errors (e.g. "A user with this email already exists.") next to the field.
        const fieldErrors: Errors = {}
        for (const [key, value] of Object.entries(e.data as Record<string, unknown>)) {
          const field = FIELD_MAP[key]
          const message = Array.isArray(value) ? value.join(' ') : String(value)
          if (field) fieldErrors[field] = message
        }
        setErrors(fieldErrors)
        if (Object.keys(fieldErrors).length === 0) setFormError(e.message)
      } else {
        setFormError(e instanceof ApiError && e.status !== 0 ? e.message : 'Could not reach the server. Try again.')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card className="mx-auto max-w-md">
      <CardHeader>
        <CardTitle className="text-2xl">Create your account</CardTitle>
        <CardDescription>You need an account to check out. Your guest cart is kept.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          {formError && (
            <Alert variant="destructive" data-testid="auth-error">
              <AlertDescription>{formError}</AlertDescription>
            </Alert>
          )}
          <FormField id="fullName" label="Full name" autoComplete="name" required value={form.fullName} onChange={set('fullName')} error={errors.fullName} />
          <FormField id="email" label="Email" type="email" autoComplete="email" required value={form.email} onChange={set('email')} error={errors.email} />
          <FormField
            id="taxId"
            label="Tax ID"
            inputMode="numeric"
            maxLength={11}
            required
            value={form.taxId}
            onChange={set('taxId')}
            error={errors.taxId}
            hint="Used on your invoices."
          />
          <div className="space-y-1.5">
            <Label htmlFor="homeAddress">Address</Label>
            <textarea
              id="homeAddress"
              rows={3}
              autoComplete="street-address"
              required
              value={form.homeAddress}
              onChange={set('homeAddress')}
              aria-invalid={errors.homeAddress ? true : undefined}
              aria-describedby={errors.homeAddress ? 'homeAddress-error' : undefined}
              className="w-full min-w-0 rounded-md border border-input bg-transparent px-3 py-2 text-base shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 aria-invalid:border-destructive md:text-sm"
            />
            {errors.homeAddress && (
              <p id="homeAddress-error" className="text-xs text-destructive">
                {errors.homeAddress}
              </p>
            )}
          </div>
          <FormField
            id="password"
            label="Password"
            type="password"
            autoComplete="new-password"
            required
            value={form.password}
            onChange={set('password')}
            error={errors.password}
            hint="At least 8 characters."
          />
          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? 'Creating account…' : 'Create account'}
          </Button>
          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link to="/login" state={{ from }} className="font-medium text-primary underline-offset-4 hover:underline">
              Log in
            </Link>
          </p>
        </form>
      </CardContent>
    </Card>
  )
}
