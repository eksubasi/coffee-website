from functools import lru_cache
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


@lru_cache(maxsize=1)
def register_fonts():
    fonts = Path(reportlab.__file__).resolve().parent / "fonts"

    pdfmetrics.registerFont(
        TTFont("BrewnookVera", str(fonts / "Vera.ttf"))
    )
    pdfmetrics.registerFont(
        TTFont("BrewnookVeraBold", str(fonts / "VeraBd.ttf"))
    )


def render_invoice_pdf(invoice):
    register_fonts()

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Brewnook invoice {invoice.number}",
    )

    body = ParagraphStyle(
        "InvoiceBody",
        fontName="BrewnookVera",
        fontSize=9,
        leading=13,
    )
    heading = ParagraphStyle(
        "InvoiceHeading",
        parent=body,
        fontName="BrewnookVeraBold",
        fontSize=20,
        leading=25,
        textColor=colors.HexColor("#493428"),
    )
    bold = ParagraphStyle(
        "InvoiceBold",
        parent=body,
        fontName="BrewnookVeraBold",
    )
    right = ParagraphStyle(
        "InvoiceRight",
        parent=body,
        alignment=TA_RIGHT,
    )

    def paragraph(value, style=body):
        text = escape(str(value)).replace("\n", "<br/>")
        return Paragraph(text, style)

    story = [
        paragraph("BREWNOOK", heading),
        Spacer(1, 4 * mm),
        paragraph("INVOICE", bold),
        paragraph(f"Invoice number: {invoice.number}"),
        paragraph(f"Order: #{invoice.order_id}"),
        paragraph(f"Issued: {invoice.issued_at:%Y-%m-%d %H:%M} UTC"),
        Spacer(1, 5 * mm),
        paragraph("Bill to", bold),
        paragraph(invoice.customer_name or invoice.customer_email),
        paragraph(invoice.customer_email),
        paragraph(f"Tax ID: {invoice.tax_id or '-'}"),
        paragraph(invoice.billing_address),
        Spacer(1, 7 * mm),
    ]

    rows = [
        [
            paragraph("Product", bold),
            paragraph("Qty", bold),
            paragraph("Unit price", bold),
            paragraph("Total", bold),
        ]
    ]

    for item in invoice.line_items:
        rows.append(
            [
                paragraph(f"{item['name']}\n{item['model']}"),
                paragraph(item["quantity"], right),
                paragraph(item["unit_price"], right),
                paragraph(item["line_total"], right),
            ]
        )

    table = Table(
        rows,
        colWidths=[85 * mm, 15 * mm, 35 * mm, 39 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEE7DF")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                (
                    "LINEBELOW",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.HexColor("#D8CEC3"),
                ),
            ]
        )
    )

    story.extend(
        [
            table,
            Spacer(1, 6 * mm),
            paragraph(f"TOTAL: {invoice.total:.2f} {invoice.currency}", right),
            Spacer(1, 5 * mm),
            paragraph("Unit prices are the amounts paid after any discount."),
            paragraph("Course-project invoice. Payment is simulated."),
        ]
    )

    document.build(story)
    return buffer.getvalue()