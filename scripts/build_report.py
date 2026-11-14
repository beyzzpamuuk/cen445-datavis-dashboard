"""Generate the one-page English submission from verified analysis_summary.json."""

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
INK = colors.HexColor("#183247")
MUTED = colors.HexColor("#526675")
TEAL = colors.HexColor("#007F7A")


def fonts():
    options = [
        (Path("C:/Windows/Fonts/segoeui.ttf"), Path("C:/Windows/Fonts/segoeuib.ttf")),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
    ]
    for regular, bold in options:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont("Body", str(regular)))
            pdfmetrics.registerFont(TTFont("BodyBold", str(bold)))
            pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyBold")
            return
    raise FileNotFoundError("Install Segoe UI or DejaVu Sans to regenerate the report with Turkish names.")


def main():
    fonts()
    data = json.loads((ROOT / "docs" / "analysis_summary.json").read_text(encoding="utf-8"))
    rf = data["rf_unseen_baskets"]
    audit = data["dataset"]
    output = ROOT / "output" / "pdf"
    output.mkdir(parents=True, exist_ok=True)
    path = output / "project_report.pdf"
    styles = {
        "eyebrow": ParagraphStyle(
            "eyebrow", fontName="BodyBold", fontSize=8, leading=11, textColor=TEAL, spaceAfter=6
        ),
        "title": ParagraphStyle(
            "title", fontName="BodyBold", fontSize=23, leading=27, textColor=INK, spaceAfter=5
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName="Body", fontSize=10, leading=14, textColor=MUTED, spaceAfter=10
        ),
        "h": ParagraphStyle(
            "h", fontName="BodyBold", fontSize=10.1, leading=13, textColor=TEAL, spaceBefore=9, spaceAfter=4
        ),
        "body": ParagraphStyle(
            "body", fontName="Body", fontSize=9.2, leading=13, textColor=INK, alignment=TA_LEFT
        ),
        "small": ParagraphStyle("small", fontName="Body", fontSize=8.2, leading=11, textColor=MUTED),
    }

    def p(text, style="body"):
        return Paragraph(text, styles[style])

    story = [
        p("CEN445 / EXPLORATORY DATA VISUALIZATION", "eyebrow"),
        p("Global Superstore", "title"),
        p("Revenue, profitability and order relationships - an interactive Streamlit dashboard", "subtitle"),
    ]
    metrics = Table(
        [
            [
                p(f"<b>${data['sales'] / 1e6:.2f}M</b><br/>Total sales"),
                p(f"<b>${data['profit'] / 1e6:.2f}M</b><br/>Total profit"),
                p(f"<b>{data['margin']:.2%}</b><br/>Profit margin"),
            ]
        ],
        colWidths=[168, 168, 168],
    )
    metrics.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF5F4")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#DCE5E8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.extend(
        [
            metrics,
            p("Dataset, context and preparation", "h"),
            p(
                f"The bundled Global Superstore teaching dataset contains <b>{audit['raw_rows']:,} order lines and {audit['raw_columns']} source columns</b>, covering 147 countries in 2011-2014. Source: Kaggle / Fatih Ilhan. Numeric, geographical, categorical and calendar dimensions support multivariate analysis. Validation found no missing cells or exact duplicates; all lines, including one zero-sales line, are retained. We standardize fields, validate dates and numeric domains, and flag {audit['outlier_count']:,} sales extremes using IQR. These carry {audit['outlier_sales_share']:.1%} of sales and remain included by default. Composite country/order/customer/date keys resolve 660 ambiguous raw order IDs into {audit['baskets']:,} baskets."
            ),
            p("Analytical goals and visualization design", "h"),
            p(
                "We ask where revenue is concentrated, which product-market groups lose money, how customer product mix and shipping flows differ, which products co-occur, and whether growth translates into profit. <b>Nine methods:</b> (1) choropleth, (2) treemap, (3) sunburst, (4) Sankey, (5) parallel coordinates, (6) co-purchase network, (7) violin with box plot, (8) correlation heatmap and (9) linked time-series panels. The first six provide advanced spatial, hierarchical, flow and multivariate views. Controls include market/category selection, year and outlier filters, map/time metrics, correlation method and network thresholds. Each chart has hover/drill/brush/zoom interaction, a computed finding, method notes and downloadable data. Stable category colors, explicit units and zero-centered signed scales support interpretation."
            ),
            p("Key findings from the complete dataset", "h"),
        ]
    )
    cat = {r["category"]: r for r in data["categories"]}
    findings = [
        (
            "Scale is not margin",
            f"Technology generates ${cat['Technology']['profit']:,.0f} profit at {cat['Technology']['margin']:.1f}% margin; Furniture earns {cat['Furniture']['margin']:.1f}% despite ${cat['Furniture']['sales'] / 1e6:.2f}M in sales.",
        ),
        (
            "Losses hide in aggregates",
            "APAC / Tables loses $20,129 on $225,096 sales (-8.9% margin). Hierarchy colors use each node's total profit divided by total sales.",
        ),
        (
            "Discount and basket patterns",
            f"{data['high_discount_loss_rate']:.1%} of lines discounted above 30% lose money. Binders and Storage share {data['top_pairs'][0]['baskets']:,} validated baskets. Both are associations, not causal findings.",
        ),
    ]
    table = Table([[p(f"<b>{a}</b>"), p(b)] for a, b in findings], colWidths=[126, 378])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#DCE5E8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend(
        [
            table,
            p("Machine learning and limits", "h"),
            p(
                f"<b>K-Means</b> uses standardized sales, profit and discount (up to 3,000 lines, k=2-6), with profile summaries and an approximate silhouette score. <b>Random Forest</b> classifies profit &gt; 0 using recorded sales, discount, quantity and shipping cost. In the default basket-disjoint evaluation, accuracy is {rf['accuracy']:.1%} versus a {rf['baseline']:.1%} training-majority baseline; balanced accuracy is {rf['balanced_accuracy']:.1%}, and non-profitable recall is {rf['loss_recall']:.1%} ({rf['test_n']:,} test lines). A second chronological split is available. Confusion matrices and held-out permutation importance expose limitations. This is retrospective classification, not a pre-order forecast; observed correlations and feature importance do not establish causes."
            ),
            p("Chart responsibility and reproducibility", "h"),
            p(
                "<b>Beyza Pamuk:</b> figures 1, 2, 7. <b>Sultan Kayı:</b> figures 3, 4, 8. <b>Nasibe Gül Çetin:</b> figures 5, 6, 9. This records chart responsibility retained from the original team README; actual individual work is verified through the contribution log and presentation. The revised implementation, validation and documentation were developed with AI assistance, disclosed in the README."
            ),
            Spacer(1, 8),
            p(
                '<b>Repository:</b> <link href="https://github.com/beyzzpamuuk/cen445-datavis-dashboard" color="#007F7A">github.com/beyzzpamuuk/cen445-datavis-dashboard</link><br/><b>Dataset:</b> <link href="https://www.kaggle.com/datasets/fatihilhan/global-superstore-dataset" color="#007F7A">kaggle.com/datasets/fatihilhan/global-superstore-dataset</link>',
                "small",
            ),
        ]
    )

    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor("#DCE5E8"))
        canvas.line(44, 30, A4[0] - 44, 30)
        canvas.setFont("Body", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(
            44, 18, "CEN445 | One-page project report | Full-dataset snapshot | 14 November 2026"
        )
        canvas.drawRightString(A4[0] - 44, 18, str(doc.page))

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=44,
        rightMargin=44,
        topMargin=32,
        bottomMargin=40,
        title="Global Superstore - CEN445 Project Report",
        author="Beyza Pamuk; Sultan Kayı; Nasibe Gül Çetin",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    from pypdf import PdfReader

    pages = len(PdfReader(str(path)).pages)
    if pages != 1:
        raise RuntimeError(f"Report must be one page; rendered {pages}. Adjust layout before submitting.")
    print(f"Created one-page report: {path}")


if __name__ == "__main__":
    main()
