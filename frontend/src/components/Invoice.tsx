import { Printer } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/auth-context'
import { invoiceNumber, type Order } from '@/lib/orders'
import { formatPrice } from '@/lib/utils'

/**
 * On-screen invoice built from the order. The backend has no invoice/PDF endpoint yet, so
 * "Download PDF" opens the browser's print dialog (choose "Save as PDF"); print styles in index.css
 * hide everything except `.invoice`.
 */
export function Invoice({ order }: { order: Order }) {
  const { user } = useAuth()
  const date = new Date(order.createdAt).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })

  return (
    <section className="space-y-4" aria-label="Invoice">
      <div className="flex justify-end print:hidden">
        <Button variant="outline" onClick={() => window.print()} data-testid="download-pdf">
          <Printer /> Download PDF
        </Button>
      </div>

      <article className="invoice space-y-6 rounded-xl border bg-card p-6" data-testid="invoice">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xl font-bold text-primary">Brewnook</p>
            <p className="text-sm text-muted-foreground">Invoice</p>
          </div>
          <dl className="text-right text-sm">
            <dt className="text-muted-foreground">Invoice number</dt>
            <dd className="font-semibold" data-testid="invoice-number">
              {invoiceNumber(order)}
            </dd>
            <dt className="mt-2 text-muted-foreground">Date</dt>
            <dd>{date}</dd>
          </dl>
        </header>

        <div className="grid gap-4 text-sm sm:grid-cols-2">
          <div>
            <p className="text-muted-foreground">Billed to</p>
            <p className="font-medium">{user?.fullName || user?.email}</p>
            {user?.taxId && <p>Tax ID: {user.taxId}</p>}
          </div>
          <div>
            <p className="text-muted-foreground">Delivery address</p>
            <p className="whitespace-pre-line">{order.address}</p>
          </div>
        </div>

        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-muted-foreground">
              <th className="py-2 font-medium">Item</th>
              <th className="py-2 text-right font-medium">Qty</th>
              <th className="py-2 text-right font-medium">Unit price</th>
              <th className="py-2 text-right font-medium">Total</th>
            </tr>
          </thead>
          <tbody>
            {order.items.map((item) => (
              <tr key={item.id} className="border-b" data-testid="invoice-line">
                <td className="py-2 pr-2">{item.productName}</td>
                <td className="py-2 text-right tabular-nums">{item.quantity}</td>
                <td className="py-2 text-right tabular-nums">{formatPrice(item.unitPrice)}</td>
                <td className="py-2 text-right tabular-nums">{formatPrice(item.total)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={3} className="pt-3 text-right font-semibold">
                Total
              </td>
              <td className="pt-3 text-right text-base font-bold tabular-nums" data-testid="invoice-total">
                {formatPrice(order.total)}
              </td>
            </tr>
          </tfoot>
        </table>
      </article>
    </section>
  )
}
