import { useState } from 'react'
import { Printer } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { fetchInvoicePdf, type Order } from '@/lib/orders'
import { toast } from '@/lib/toast'
import { formatPrice } from '@/lib/utils'

export function Invoice({ order }: { order: Order }) {
  const [downloading, setDownloading] = useState(false)
  const invoice = order.invoice

  async function handleDownload() {
    if (!order.invoiceId || downloading) return

    setDownloading(true)

    try {
      const blob = await fetchInvoicePdf(order.invoiceId)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')

      link.href = url
      link.download = `${invoice?.number ?? 'invoice'}.pdf`

      document.body.appendChild(link)
      link.click()
      link.remove()

      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : 'Could not download your invoice.',
      )
    } finally {
      setDownloading(false)
    }
  }

  if (!invoice) {
    return (
      <p className="text-sm text-muted-foreground">
        No invoice is available for this order.
      </p>
    )
  }

  const date = new Date(invoice.issued_at).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
  return (
    <section className="space-y-4" aria-label="Invoice">
      <div className="flex justify-end print:hidden">
        <Button
          variant="outline"
          onClick={handleDownload}
          disabled={downloading || !order.invoiceId}
          data-testid="download-pdf"
        >
          <Printer /> {downloading ? 'Downloading…' : 'Download PDF'}
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
              {invoice.number}
            </dd>
            <dt className="mt-2 text-muted-foreground">Date</dt>
            <dd>{date}</dd>
          </dl>
        </header>

        <div className="grid gap-4 text-sm sm:grid-cols-2">
          <div>
            <p className="text-muted-foreground">Billed to</p>
            <p className="font-medium">{invoice.customer_name || invoice.customer_email}</p>
            {invoice.tax_id && <p>Tax ID: {invoice.tax_id}</p>}
          </div>
          <div>
            <p className="text-muted-foreground">Delivery address</p>
            <p className="whitespace-pre-line">{invoice.billing_address}</p>
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
            {invoice.line_items.map((item) => (
              <tr key={item.product_id} className="border-b" data-testid="invoice-line">
                <td className="py-2 pr-2">{item.name}</td>
                <td className="py-2 text-right tabular-nums">{item.quantity}</td>
                <td className="py-2 text-right tabular-nums">{formatPrice(Number(item.unit_price))}</td>
                <td className="py-2 text-right tabular-nums">{formatPrice(Number(item.line_total))}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={3} className="pt-3 text-right font-semibold">
                Total
              </td>
              <td className="pt-3 text-right text-base font-bold tabular-nums" data-testid="invoice-total">
                {formatPrice(Number(invoice.total))}
              </td>
            </tr>
          </tfoot>
        </table>
      </article>
    </section>
  )
}
