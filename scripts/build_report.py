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
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        ),
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
    raise FileNotFoundError(
        "Install Segoe UI, Arial (macOS) or DejaVu Sans to regenerate the report with Turkish names."
    )


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
            "title", fontName="BodyBold", fontSize=17, leading=20, textColor=INK, spaceAfter=2
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName="Body", fontSize=9.5, leading=12, textColor=MUTED, spaceAfter=6
        ),
        "h": ParagraphStyle(
            "h", fontName="BodyBold", fontSize=9.6, leading=12, textColor=TEAL, spaceBefore=5, spaceAfter=2
        ),
        "body": ParagraphStyle(
            "body", fontName="Body", fontSize=8.3, leading=10.6, textColor=INK, alignment=TA_LEFT
        ),
        "small": ParagraphStyle("small", fontName="Body", fontSize=8.2, leading=11, textColor=MUTED),
        "cell": ParagraphStyle("cell", fontName="Body", fontSize=7.8, leading=9.1, textColor=INK),
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
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend(
        [
            metrics,
            p("Dataset, context and preparation", "h"),
            p(
                f"The bundled Global Superstore teaching dataset contains <b>{audit['raw_rows']:,} order lines and {audit['raw_columns']} source columns</b>, covering 147 countries in 2011-2014. Source: Kaggle / Fatih Ilhan. Validation found no missing cells or exact duplicates; all lines, including one zero-sales line, are retained. We standardize fields, validate dates and numeric domains, and flag {audit['outlier_count']:,} sales extremes using IQR. These carry {audit['outlier_sales_share']:.1%} of sales and remain included by default. Composite keys give {audit['baskets']:,} baskets."
            ),
            p("Analytical goals and visualization design", "h"),
            p(
                "Goal: explain where revenue is earned, where margin is lost, and why. <b>Nine methods</b> (six advanced): choropleth, treemap, sunburst, Sankey, parallel coordinates and co-purchase network; plus violin/box plot, correlation heatmap and linked time-series panels. No pie charts. Global filters (markets, categories, years, IQR outlier exclusion) and chart controls (map/time metric, correlation method, network thresholds, k, evaluation design) drive every view; charts add hover, drill-down, drag, brushing and zoom. Each chart states its question and a recomputed answer."
            ),
            p("Research questions and answers (complete dataset)", "h"),
        ]
    )
    rows = [[p("<b>Figure / owner</b>", "cell"), p("<b>Question</b>", "cell"), p("<b>Answer</b>", "cell")]]
    rows += [
        [
            p(f"<b>{q['figure']}</b><br/>{q['owner']}", "cell"),
            p(q["question"], "cell"),
            p(q["answer"], "cell"),
        ]
        for q in data["questions"]
    ]
    table = Table(rows, colWidths=[92, 150, 262], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF5F4")),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#DCE5E8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    team_rows = [
        [
            p("<b>Member</b>", "cell"),
            p("<b>Own visualizations (3 each)</b>", "cell"),
            p("<b>Other tasks</b>", "cell"),
        ],
        [
            p("<b>Beyza Pamuk</b>", "cell"),
            p("Fig 1 Choropleth, Fig 2 Treemap, Fig 7 Violin", "cell"),
            p("Preprocessing (IQR outliers, date parsing); sidebar filter layout", "cell"),
        ],
        [
            p("<b>Sultan Kayı</b>", "cell"),
            p("Fig 3 Sunburst, Fig 4 Sankey, Fig 8 Correlation heatmap", "cell"),
            p("Data cleaning and validation; interactive cross-filtering", "cell"),
        ],
        [
            p("<b>Nasibe Gül Çetin</b>", "cell"),
            p("Fig 5 Parallel coordinates, Fig 6 Network, Fig 9 Time series", "cell"),
            p("UI consistency and color palette; graph data transformations", "cell"),
        ],
        [
            p("<b>Team (all members)</b>", "cell"),
            p("ML: K-Means clustering, Random Forest classifier", "cell"),
            p("One-page report; individual presentations", "cell"),
        ],
    ]
    team = Table(team_rows, colWidths=[92, 190, 222])
    team.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF5F4")),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#DCE5E8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.extend(
        [
            table,
            p("Machine learning and limits", "h"),
            p(
                f"<b>K-Means</b> clusters standardized sales, profit and discount (k=2-6). <b>Random Forest</b> classifies profit &gt; 0 from sales, discount, quantity and shipping cost, evaluated on held-out baskets (balanced accuracy {rf['balanced_accuracy']:.1%}, {rf['test_n']:,} test lines) or a later time period. Findings are associations in historical data, not causal effects or forecasts."
            ),
            p("Team contributions / task distribution", "h"),
            team,
            Spacer(1, 3),
            p(
                "All members jointly implemented both ML models, co-wrote this report, and each presents their own three charts.",
                "small",
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
            44, 18, "CEN445 | One-page project report | Full-dataset snapshot | 15 November 2026"
        )
        canvas.drawRightString(A4[0] - 44, 18, str(doc.page))

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=44,
        rightMargin=44,
        topMargin=26,
        bottomMargin=36,
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
