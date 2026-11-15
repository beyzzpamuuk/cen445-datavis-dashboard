# Global Superstore - Sales & Profit Explorer

An interactive **Python / Streamlit / Plotly** dashboard for CEN445. Explore where sales concentrate, where margins disappear, how products co-occur, and what recorded transaction attributes reveal about profitability.

**Team:** Beyza Pamuk, Sultan Kayı, Nasibe Gül Çetin.

**Repository:** https://github.com/beyzzpamuuk/cen445-datavis-dashboard

**Submission report:** [One-page English PDF](output/pdf/project_report.pdf).

## Run locally

Tested with **Python 3.13** on Windows, macOS and Linux using the exact versions in `requirements.txt`. Use Python 3.13; other versions are not tested. No API keys, external database or deployment are required.

```powershell
git clone https://github.com/beyzzpamuuk/cen445-datavis-dashboard.git
cd cen445-datavis-dashboard
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

On macOS/Linux, create the environment with `python3.13 -m venv .venv`, then use `.venv/bin/python` for the last two commands. Run from the repository directory so Streamlit loads `.streamlit/config.toml` and serves the bundled map correctly. Open the localhost address printed by Streamlit. Stop the server with Ctrl+C. Hosting the app is optional for this assignment.

The CSV and world map are bundled. After dependencies are installed, the dashboard works locally without fetching live data, fonts or a map CDN. Source/repository links naturally need internet if opened. If the default port is busy, append `--server.port 8502`.

## Dataset and observation unit

The source attribution supplied with the original team project is [Global Superstore / Fatih Ilhan / Kaggle](https://www.kaggle.com/datasets/fatihilhan/global-superstore-dataset). The **bundled file is the authoritative snapshot for this submission**, rather than an automatically downloaded replacement. See the source platform for its dataset license.

| Property | Bundled snapshot |
|---|---|
| Source shape | **51,290 rows x 27 columns** |
| Dates | 1 January 2011 - 31 December 2014 |
| Geography | 147 countries, 7 markets |
| Categories / sub-categories | 3 / 17 |
| Validated baskets | **25,754** |
| Observation unit | One **order line**, not one complete order or one customer |
| Types | Monetary/continuous measures, units, discounts, identifiers, dates and categorical hierarchies |
| Main variables | Sales, Profit, Discount, Quantity, Shipping.Cost, Country, Market, Category, Sub.Category, Segment, Order.Date, Ship.Mode |
| SHA-256 | `7203f16d9e44430c7cd4c92e401df3381141b0b9b8bdec44b6d8e8ecb298b8db` |

Amounts are displayed as USD following the supplied Superstore convention; no currency conversion or inflation adjustment is applied. This is a historical teaching dataset; it does not establish current global retail behavior. Sales values in this particular file are stored as integers. Identifiers, the constant record-count column, Market2 and week number are source metadata and are not treated as independent numeric predictors.

### Validation and preprocessing

`analytics.py` normalizes column names and whitespace, removes exact duplicates, parses dates/numbers, validates required fields and domains, derives calendar months, maps ISO3 countries, and records an explicit audit. Invalid critical records are removed rather than silently replacing target profit. Optional missing categories become `Unknown`. Negative profit is valid; discounts must be 0-1, quantity a positive integer, and sales/shipping cost non-negative. A zero denominator yields undefined margin.

For the supplied snapshot: **0 missing cells, 0 exact duplicates, 0 invalid rows removed, 1 zero-sales line retained, 0 year disagreements and 0 unmapped country codes**. No missing-value imputation was necessary. The app reports these actual results instead of claiming cleaning that did not occur.

**Basket identity matters.** There are 660 raw Order.ID groups with different customer/date/country identities. Grouping only by Order.ID invents co-purchases. Country alone is also insufficient. We establish `(country, order_id, customer_id, order_date)` before filtering; the resulting key is used for counts, networks and model partitions. Under a category filter, the contents of a basket mean its **selected** lines; unselected products are outside the analysis.

**Outliers are sensitivity analysis, not automatic errors.** The full-file sales IQR bounds are -299 to 581. The 5,655 flagged lines carry **56.08% of sales** and remain included by default. The optional exclusion uses this fixed full-data cutoff and displays the omitted records and revenue share. Profits are never winsorized or imputed.

## Nine visualization methods and their questions

The first six are advanced spatial, hierarchical, flow, multivariate and network techniques. Each figure includes a clear question, period/context, encoding explanation, a **filter-dependent computed finding**, interaction instructions, method notes, an accessible data table and a CSV download. A chapter selector computes only the active chapter; expensive model/network results are cached.

| Figure | Method | Analytical question | Interactivity |
|---|---|---|---|
| 1 | **Choropleth (advanced)** | Where do sales, total profit and margin concentrate? | Metric dropdown; hover; map pan/zoom; global filters |
| 2 | **Treemap (advanced)** | Which product-market groups sell well but lose money? | Hierarchical drill-down/path bar; hover; global filters |
| 3 | **Sunburst (advanced)** | How does product mix differ within customer segments? | Segment/category drill-down; parent shares; hover |
| 4 | **Sankey (advanced)** | How do sales flow through customer segment, shipping mode and category? | Draggable nodes; link value/profit/share tooltips |
| 5 | **Parallel coordinates (advanced)** | What attributes accompany discounted loss-making transactions? | Axis range brushing/reordering; sample-size selector |
| 6 | **Co-purchase network (advanced)** | Which sub-categories share baskets; is association stronger than chance? | Count/lift ranking; minimum count; top-pair limit; node/edge-midpoint hover; pan/zoom |
| 7 | Violin with embedded box plot | How do profit distributions and loss frequencies differ by category? | Hover; full distribution / central-98% density toggle; zoom |
| 8 | Correlation heatmap | Which numeric measures move together? | Spearman/Pearson selector; numeric cell labels; hover |
| 9 | Linked calendar time-series panels | Does sales growth translate into profitable growth? | Metric selector; synchronized date axes; range slider and 6m/1y/all controls; grouped legend; hover |

There are **no pie charts**. Additional model figures support the analysis; they are not substituted for the required nine.

### Important analytical definitions

- **Profit margin:** `sum(profit) / sum(sales) * 100`, independently computed at every country, hierarchy and monthly level. We never color an aggregate with a sales-weighted average of raw line profits.
- **Treemap:** sales area, zero-centered aggregate margin color. All parent totals equal their children's totals. Initial depth limits visual crowding; click to reveal sub-categories.
- **Sunburst:** segment identity and within-parent sales share, rather than a second profitability chart. Segment colors have a different, explicitly labeled meaning from the product-category palette.
- **Sankey:** width means **USD sales**, not number of orders or delivery time. Incoming/outgoing sales balance at shipping nodes. Merging at shipping nodes shows adjacent-stage marginal flows; it does not preserve a specific end-to-end segment/category path.
- **Network:** each product pair is counted at most once per basket. Support = shared baskets / all selected baskets, including singleton baskets. Lift = support(A,B) / (support(A) x support(B)); values above 1 indicate positive association. Popularity alone does not prove affinity. Thick edges show count; size shows a node's sum of **displayed pair counts**, not unique orders. Top-N selection changes the visible graph. Positions have no business meaning.
- **Parallel coordinates:** deterministic sample up to 1,500 lines, seed 42. Original units are labeled. Brushing affects this chart only; the finding uses all globally selected lines.
- **Violin:** by default the pooled 1st-99th percentile is shown to make density readable; exact bounds and omitted count are visible. This display-only restriction never changes findings or summary tables. Uncheck the control to show all tails. Density estimates are unreliable in tiny subsets.
- **Heatmap:** Spearman is the default for skewed data; Pearson is available for linear association. Fixed [-1,+1] scale; undefined constant-variable correlations remain blank, not zero. Neither implies causation.
- **Time panels:** actual dates and missing-month gaps; no invented zeros and no dual-axis overlay. The lower panel shows margin (or profit if margin is selected above). Margin comes from monthly totals.

## Research questions and answers

Each figure and model answers one analytical question. The answers below are computed from the complete bundled file by `scripts/export_analysis.py` (stored in `docs/analysis_summary.json`); in the app, each chart's title states its question and the **Answer** block recomputes it for the current filters.

| Figure / model | Owner | Question | Answer (complete dataset) |
|---|---|---|---|
| 1 Choropleth | Beyza Pamuk | Where are sales and losses concentrated geographically? | United States has the most sales ($2,297,354, 18.2% of total); Turkey has the largest country loss (-$98,447, -90.7% margin). |
| 2 Treemap | Beyza Pamuk | Which market-product groups sell but lose money? | EU / Tables has the largest loss: -$20,998 on $105,380 sales (-19.9% margin). |
| 3 Sunburst | Sultan Kayı | How does product mix differ across customer segments? | Mix is similar across segments; the highest share is Technology in Home Office (39.0% of that segment's sales). |
| 4 Sankey | Sultan Kayı | How do sales flow from segment through shipping mode to category? | Standard Class carries 59.9% of sales ($7,578,889). |
| 5 Parallel coordinates | Nasibe Gül Çetin | What accompanies loss-making transactions? | 92.5% of the 10,361 lines discounted above 30% lose money. |
| 6 Network | Nasibe Gül Çetin | Which sub-categories are bought together? | Binders + Storage share the most baskets (899), but lift 0.93 shows this reflects popularity, not special affinity. |
| 7 Violin | Beyza Pamuk | Which category loses money most often? | Furniture: 31.6% of its order lines lose money (overall 24.5%). |
| 8 Heatmap | Sultan Kayı | Which numeric measures move together? | Discount and profit are negatively associated: Spearman -0.60, Pearson -0.32. |
| 9 Time series | Nasibe Gül Çetin | Does sales growth translate into profitable growth? | Sales grew 90% from 2011 to 2014, while annual margin stayed between 11.0% and 11.9%; peak month Nov 2014. |
| ML K-Means | Team | Which transaction profiles emerge? | k=3 (silhouette 0.62); 'Loss-making / high discount' lines average 52% discount and 93% lose money. |
| ML Random Forest | Team | Can recorded attributes identify non-profitable lines? | 92.2% accuracy vs 74.2% baseline, 77.1% non-profitable recall; discount is the most important feature. |

## Machine learning

### K-Means transaction profiles

Features are sales, profit and discount. Z-score scaling gives features comparable units. A deterministic sample of up to 3,000 lines is fitted with k=2-6, seed 42 and 20 initializations. The app shows actual cluster count, profile size/share, mean sales/profit/discount, loss frequency and approximate silhouette (at most 1,200 observations). Semantic names follow the fitted means; cluster labels are not stable customer identities. The plot uses both color and marker shape. Small/degenerate subsets produce guidance instead of a crash. Extreme records remain relevant and can affect centroids; use the outlier sensitivity control to inspect this.

### Random Forest retrospective profitability classification

Target: **profit > 0**. Zero and negative profit belong to the non-profitable class. Predictors: recorded sales, discount, quantity and shipping cost. Actual profit is excluded from predictors. Shipping cost may be known only after fulfillment, so we make **no pre-order prediction or causal claim**.

Two evaluation designs are available:

1. **Unseen baskets:** hold out 25% of composite baskets using GroupShuffleSplit, seed 42. No basket appears in both partitions; dates can overlap.
2. **Future period:** train before the 75%-of-distinct-dates cutoff and evaluate on later dates, with no shared date/basket. This tests temporal transfer using recorded features, not an ex-ante sales forecast.

Full baskets/dates are split **before** deterministic caps of 18,000 training and 6,000 test lines. The model uses 160 trees, depth 10, minimum leaf size 5 and seed 42. Test data is not used to tune hyperparameters. The majority-class baseline is fitted on training labels, then evaluated on the same test set. Guardrails require sufficient data and both classes in each partition.

The app includes accuracy, baseline accuracy, balanced accuracy, non-profitable recall, macro F1, a confusion matrix, class distributions, date ranges, partition sizes and basket overlap. **Permutation importance** measures the held-out balanced-accuracy drop over four shuffles per feature; error bars are repeat standard deviations, not confidence intervals. Correlated predictors and single-split variability limit interpretation.

Full-data grouped holdout (tested stack, seed 42): **92.17% accuracy**, **74.17% baseline**, **87.26% balanced accuracy**, **77.10% non-profitable recall**. In 6,000 test lines, the model misses 355 of 1,550 non-profitable lines. Metrics change under filters/evaluation settings. Recompute, do not copy the numbers into dynamic UI text.

## Findings worth presenting

- Technology earns **$663,779** profit at **13.99% margin**; Furniture produces **$4.11M** sales but only **6.94% margin**. Revenue scale and profitability are different questions.
- **EU / Tables loses $20,998** on $105,380 sales (**-19.93% margin**), the largest market/sub-category loss; APAC / Tables follows (-$20,129 on $225,096). A sales-only hierarchy conceals this.
- **92.45%** of selected-full-file lines with discounts above 30% lose money. This observed association does not establish a causal discount effect.
- Binders and Storage share **899 validated baskets**. The previous raw-order grouping counted 944; correct observation identity changes the result.
- Removing statistical sales extremes discards **56.08% of sales**. Removing them automatically would change the business question substantially.

All values above describe the complete supplied file. `scripts/export_analysis.py` regenerates [the numerical snapshot](docs/analysis_summary.json), used by the PDF generator.

## Visual design and researched principles

See [design rationale and primary sources](docs/DESIGN_STANDARDS.md). Implementation uses a restrained light canvas, dark navy text, readable system fonts, full-width complex charts, fixed category identities, amber/teal signed scales, explicit zero references, direct labels/numeric cells and consistent units. Details are progressively disclosed instead of crowding the plot.

Every chart has a textual finding and table alternative; point shapes supplement color where applicable. Controls retain native Streamlit keyboard semantics. CSS adds visible focus and reduced-motion behavior. These measures improve access but **do not constitute a screen-reader or full WCAG certification**. Drag-only chart actions have globally filtered/table alternatives; not all Plotly gestures are fully keyboard equivalent.

## Team Contributions / Task Distribution

The assignment requires 3 visualizations per member (9 in total). Each member designed and built their own three charts and presents them individually in English. Each member's other tasks are listed alongside, as in the original team README. The same distribution appears in the one-page report.

| Member | Own visualizations | Shared work |
|---|---|---|
| Beyza Pamuk | Fig 1 Choropleth map (advanced), Fig 2 Treemap (advanced), Fig 7 Violin + box plot | Co-designed preprocessing (IQR outlier detection, date parsing) and the sidebar filter layout; co-implemented K-Means clustering; technical documentation |
| Sultan Kayı | Fig 3 Sunburst (advanced), Fig 4 Sankey diagram (advanced), Fig 8 Correlation heatmap | Co-designed data cleaning/validation and interactive cross-filtering; co-implemented the Random Forest classifier and feature-importance analysis |
| Nasibe Gül Çetin | Fig 5 Parallel coordinates (advanced), Fig 6 Co-purchase network (advanced), Fig 9 Linked time-series panels | Co-designed UI consistency, color palette and graph data transformations; co-authored the one-page report and presentation insights |

## Project structure

```text
app.py                      Streamlit layout, filters, lazy chapter rendering
analytics.py                Data validation, identity and aggregate calculations
visuals.py                  Nine figure builders and model figures
models.py                   K-Means and held-out Random Forest evaluation
superstore.csv              Original bundled data, unchanged
assets/style.css             Shared visual tokens and layout
.streamlit/config.toml       Theme, static map serving, telemetry disabled
static/geo/                 Offline world map and upstream attribution/license
docs/                       Design standards, QA notes and the analysis snapshot
output/pdf/project_report.pdf  One-page English submission
scripts/                    Reproducible analysis, PDF and optional figure exports
tests/                      Analytical regression and Streamlit journey checks
```

## Verification and report generation

Runtime tests need only `requirements.txt`:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The checks reconcile the source totals, preserve zero-sales rows, verify composite baskets, reject the original false network count, check every hierarchy parent/leaf ratio, verify Sankey conservation, construct all nine methods, test disjoint/temporal holdouts and exercise every chapter, alternate metrics, empty/reset filters, extreme exclusions and the old Canada/Furniture/2011/k=6 failure. See [QA notes](docs/QA.md) for observed coverage and limits.

Optional development/report tools:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
.venv\Scripts\python.exe scripts/export_analysis.py
.venv\Scripts\python.exe scripts/build_report.py
```

The PDF script requires Segoe UI (Windows) or DejaVu Sans (Linux) for Turkish names. It refuses a report longer than one page. Optional `scripts/export_figures.py` uses Kaleido plus an installed Chrome/Chromium to render real figure previews into `tmp/figures/`; it is not needed to run the dashboard. PDF rendering can use `pdftoppm` or PyMuPDF. Do not regenerate published numbers without regenerating and visually checking the PDF.

## Submission and live demonstration

Commit/push the final code, data, assets and PDF to the public repository; verify the updated files from a signed-out browser. The PDF contains the repository link. Every team member uploads the **same final PDF** via the course Microsoft Form, and each must deliver their own English presentation. The assignment's official LMS deadline controls submission; a local running app does not replace uploading the files.

Before class: install dependencies, open the app once to warm model caches, confirm the map renders locally, test one filtered story, and keep the PDF plus screenshots as a backup. Do not fabricate live results if a presentation computer is offline or a model is unavailable.
