# Design and analytical standards

This is an exploratory retail dashboard, not a decorative gallery. Complexity is justified by the question: geography, hierarchy, part-to-whole composition, flow, multidimensional trade-offs, associations, distributions and time each need a different view.

## Primary guidance and its application

| Source | Applied decisions |
|---|---|
| [UK Government Analysis Function: charts](https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/) | A question/headline, statistical context and units outside the figure; uncluttered gridlines; few series; figure numbers; readable labels; text/table alternatives |
| [W3C WCAG 2.2: use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) | Signs, numeric labels, category names, marker shapes and data tables supplement hue; no red/green-only profit encoding |
| [W3C WCAG 2.2: contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) | Dark text on a light surface; body-text contrast target 4.5:1. Tests measure the actual ink, muted, accent and category-label colors used on white. Chart continuous scales need numeric/table alternatives and are not claimed individually to meet a text threshold |
| [Plotly: hierarchical color aggregation](https://plotly.com/python/treemaps/) | Explicit parent/leaf totals and margin ratios; a raw line-profit average must not be described as aggregate profit or margin |
| [scikit-learn: grouped holdouts](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html) | Composite baskets cannot cross train/test partitions; chronological evaluation is a separate design |
| [scikit-learn: model evaluation](https://scikit-learn.org/stable/modules/model_evaluation.html) | Training-majority baseline, balanced accuracy, class recall, macro F1 and a confusion matrix accompany accuracy |
| [scikit-learn: permutation importance](https://scikit-learn.org/stable/modules/permutation_importance.html) | Importance is measured on held-out data, has repeat variability, and is not causal influence |
| [scikit-learn: silhouette coefficient](https://scikit-learn.org/stable/modules/clustering.html#silhouette-coefficient) | Cluster separation is evaluated in standardized feature space; silhouette is not classification accuracy |
| [Streamlit: caching](https://docs.streamlit.io/develop/concepts/architecture/caching) | Immutable cached data/model outputs with deterministic seeds; only the selected chapter executes |

Guidance consulted on 14 November 2026. These are design and evaluation references, not claims that every guidance item or WCAG criterion has been certified.

## Visual system

- Canvas `#F5F7F8`, chart surface white, primary ink `#183247`, secondary ink `#526675`, action `#007F7A`, border `#DCE5E8`.
- Product categories always use Furniture `#9A4E1B`, Office Supplies `#007F7A`, Technology `#365EAD` when the encoding represents category identity.
- Signed measures use amber for negative, pale neutral for zero, teal for positive. Map/profit/heatmap scales are zero-centered and symmetric within the selected view; the heatmap domain remains [-1,1]. Numeric signs and tooltips prevent color-only interpretation.
- Segment hue is explicitly a separate identity encoding in the sunburst. K-Means loss profiles use amber, core profitable profiles teal and high-value profitable profiles blue; markers provide another distinction.
- Dense charts use the full content width. H1 is compact; headings express analytical questions rather than library names. Detailed computation notes live with chart-specific data tables.
- Monthly measures occupy separate synchronized panels instead of a misleading dual-axis overlay. Dollar axes include units; margin axes include percent signs. Blank correlation means undefined, not zero.

## Interaction and interpretation

Overview -> global filters -> chart controls -> local chart gestures -> details/data. Empty selections are genuinely empty and have an immediate reset path. Network thresholds can produce a meaningful no-pairs state. ML guardrails explain insufficient observations/classes and never replace an unavailable evaluation with a success percentage.

Local brushing and legend toggles are labeled as local chart actions; they do not silently claim linked global filtering. The selected period and scope appear with every numbered chart. The network's truncated graph, parallel sampling and violin display trimming are disclosed with denominators and limits.

## Accessibility boundaries

Native Streamlit controls retain names and keyboard behavior. Chart findings and data tables provide a non-visual/nondrag route to the evidence. Focus styling and reduced-motion CSS are included. Complex figures remain intrinsically two-dimensional; a narrow viewport cannot reproduce the desktop density. A complete screen-reader, mobile-device and cross-browser audit remains separate from automated validation and figure rendering. See QA notes for the actual executed checks.
