# English presentation and demonstration guide

Use the actual app to tell an analytical story. Adapt the wording to your own understanding; do not read a library-name list. The instructor's allocated time takes precedence over this suggested 8-10 minute rehearsal.

## Opening (about 40 seconds)

“We explore 51,290 order lines from Global Superstore, covering 147 countries from 2011 to 2014. Our main question is whether revenue growth also produces healthy profit. A row is an order line, so we distinguish line counts from composite baskets. The dashboard combines nine visualization methods with two machine learning algorithms.”

Show the source/definitions panel, period, sales, profit and margin. Explain that filters apply globally, while chart brushing is local. Keep sales extremes included initially.

## Beyza Pamuk - figures 1, 2 and 7

- **Map:** “The map shows where recorded sales concentrate; it is not adjusted for population or market size.” Change sales to margin and explain why the leading country can change. Show a country tooltip and its basket count.
- **Treemap:** “Area measures sales, while the signed color measures aggregate margin.” Click APAC, Furniture and Tables; verify approximately -$20,129 profit and -8.9% margin. Explain why averaging raw profits would be incorrect. Use the path bar to return.
- **Violin:** “The density and box show the distribution of order-line profit; the loss frequency and median summarize all lines.” Explain the clearly labeled central-98% display and restore the full tails. Do not infer a stable density from five records.

## Sultan Kayı - figures 3, 4 and 8

- **Sunburst:** “Here we ask a different question: which categories make up each customer segment?” Drill into a segment and read the share of its parent. Hue indicates segment identity, not profit.
- **Sankey:** “The widths are sales dollars, not orders or shipping speed.” Hover a link; explain conservation at a shipping node and that merged nodes show adjacent-stage aggregates rather than exact end-to-end paths.
- **Heatmap:** Compare Spearman and Pearson. “Ranks and magnitudes answer different association questions, especially with skewed transaction values. Correlation does not show that changing one variable causes a change in another.” Read the actual filtered coefficient; never memorize a fixed +0.77.

## Nasibe Gül Çetin - figures 5, 6 and 9

- **Parallel coordinates:** “Each line is one sampled order line; each axis has its own units.” Brush discounts above 30%, explain the pattern, and note that the finding uses all globally selected records. Clear the brush.
- **Network:** Hover Binders/Storage. “899 composite baskets contain this pair in the complete dataset. Raw order identifiers repeated across identities; using them alone overcounted the pair.” Explain support versus lift and change the ranking/threshold. Position has no business meaning.
- **Time panels:** “The panels share time but keep sales dollars and profit margin on separate labeled axes.” Zoom with the bottom handles, switch the main measure to profit, and use the legend. Explain the observed peak rather than claiming a forecast.

## Two machine learning models (shared discussion, about 90 seconds)

1. **K-Means:** “Standardized sales, profit and discount reveal transaction profiles. We show sample size, profile averages and an approximate silhouette score. This clusters transactions, not customers.” Try k=3 then k=4 and explain why cluster identity changes.
2. **Random Forest:** “We classify recorded non-profitable versus profitable lines. Our default evaluation holds out whole baskets; a second option holds out later dates.” Show the majority baseline, balanced accuracy and non-profitable recall, then the confusion matrix. In the full-data grouped result the model misses 355 of 1,550 non-profitable test lines despite 92.2% overall accuracy. Shipping cost may be post-fulfillment; this is retrospective classification.

## Robustness demonstration (about 30 seconds)

Select Canada, Furniture and 2011. Show that the app explains insufficient model data rather than claiming 100% success or crashing at k=6. Clear all markets to demonstrate the empty-state message, then reset. Enable extreme-sales exclusion once and explain the revenue removed; restore it before finishing.

## Likely questions

| Question | Point to explain |
|---|---|
| Why not remove all outliers? | They carry 56.1% of sales and are not necessarily errors. We provide sensitivity analysis. |
| Why 25,754 baskets rather than raw unique Order.ID? | Composite identity separates repeated identifiers across countries/customers/dates. |
| What makes the first six advanced? | Spatial geometry, multilevel hierarchies, flow conservation, multivariate brushing and graph relationships. |
| Are discount and low profit causally related? | We observe association; omitted product/market effects can confound it. |
| Why report more than accuracy? | Majority classes hide missed non-profitable lines; baseline and class recall expose that. |
| What is each member's actual contribution? | Explain your own three charts and your actual changes/validations, supported by the contribution log. |

## Final rehearsal

- Each member independently starts the app, explains their own three charts and reproduces one number.
- Install the locked requirements on the presentation machine before class; the map asset is local.
- Keep the final one-page PDF and actual app screenshots as backup, and ensure the public repository contains the revision.
- Verify the official LMS deadline and upload the same final PDF for every member if instructed.
- Give the presentation in English. A functioning dashboard or uploaded file does not replace attendance or individual understanding.
