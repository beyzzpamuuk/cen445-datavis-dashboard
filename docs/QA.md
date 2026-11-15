# Verification record

Test date: **14 November 2026**. Host: Windows; Python 3.13.3. Runtime dependency versions are pinned in `requirements.txt`. Results apply to the bundled dataset checksum recorded in the README.

## Executed automated checks

`python -m unittest discover -s tests -v`: **10 tests passed** in the final analytical/UI test run.

- Source reconciliation: 51,290 retained lines, 27 source columns, correct sales/profit totals, one zero-sales line retained, 5,655 IQR flags, 25,754 baskets, all country names mapped.
- Distinct basket identity and co-purchase regression: Binders/Storage = 899, not 944. Total pair occurrences = 37,997.
- Every hierarchy parent reconciles with children; each node's color is its own aggregate margin. APAC/Furniture/Tables remains negative.
- Empty market/category selections are empty; extreme-sales exclusion removes the expected records and revenue share.
- Insufficient and single-class ML subsets display explanations; the old Canada/Furniture/2011/k=6 path does not crash or advertise a meaningless 100% result.
- Critical invalid target/date/discount records are rejected in a corrupted-data fixture; target profit is not median-imputed.
- All nine methods construct successfully with alternate map/correlation/time/network settings.
- Sankey incoming/outgoing sales reconcile at every shipping node.
- Both classifier designs have zero basket overlap; chronological train dates precede test dates; confusion counts reconcile with evaluated sample size.
- Streamlit AppTest journeys cover all four chapters, alternate metrics/ranking, a no-network-pairs state, full/central violin mode, both model evaluations, k=6, narrow filters, clearing selections, reset recovery and IQR exclusion.

`python -m ruff check .`: passed. `python -m ruff format --check .`: passed after formatting. A bare-mode AppTest context warning is expected from the test harness and is not an app exception.

## Executed visual/artifact checks

- All **nine main figures plus two model figures** were rendered with Plotly/Kaleido at 1,100px width and inspected. Intermediate images are in ignored `tmp/figures/` and are not application screenshots.
- Corrections made after visual inspection: date shortcuts moved away from time-series observations; model profile order/color made semantically consistent; violin central density made legible with explicit display-only bounds/counts.
- PDF rebuilt from `docs/analysis_summary.json`, reopened and confirmed to have exactly **one A4 page**. Rendered with PyMuPDF and visually inspected for clipped text, glyph errors, spacing and legibility. Turkish member names render correctly; repository and dataset links are present.
- Measured white-background contrast ratios: primary ink **13.24:1**, secondary ink **5.97:1**, teal **4.86:1**, Furniture label color **6.04:1**, Technology label color **6.25:1**. This checks those pairs, not every possible continuous chart color.
- The world TopoJSON is bundled with upstream attribution and MIT license; no external map request is needed when the configured static route is used.

## Scope limits

Automated Streamlit tests validate execution, widgets, outputs and recovery, not browser hover fidelity or visual reflow. Figure PNGs validate real plots, not complete application layout. Native browser verification, if available, is recorded separately below. No full screen-reader, physical mobile-device or cross-browser certification is claimed. Complex Plotly gestures are not all keyboard equivalent; each figure includes textual findings and accessible data tables as alternatives.

Actual student contribution/individual understanding, official submission, attendance and public-repository publication are human/external delivery checks. The code does not claim to have performed them.
