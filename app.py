"""CEN445 - Global Superstore. Run: python -m streamlit run app.py"""

from pathlib import Path

import pandas as pd
import streamlit as st

from analytics import DATA_PATH, LABELS, REPOSITORY_URL, SOURCE_URL, filter_data, load_dataset, summarize
from models import classify_profitability, cluster_transactions
from visuals import (
    classification_figure,
    cluster_figure,
    correlation_chart,
    map_chart,
    money,
    network_chart,
    parallel_chart,
    sankey_chart,
    sunburst_chart,
    treemap_chart,
    trend_chart,
    violin_chart,
)

st.set_page_config(
    page_title="Global Superstore | Sales & Profit Explorer", page_icon=":material/monitoring:", layout="wide"
)
ROOT = Path(__file__).resolve().parent
st.html((ROOT / "assets" / "style.css").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def cached_load(signature):
    return load_dataset()


cached_clusters = st.cache_data(show_spinner=False, max_entries=16)(cluster_transactions)
cached_classifier = st.cache_data(show_spinner=False, max_entries=12)(classify_profitability)
cached_network = st.cache_data(show_spinner=False, max_entries=16)(network_chart)

try:
    df, audit = cached_load(DATA_PATH.stat().st_mtime_ns)
except (OSError, ValueError) as exc:
    st.error(f"Dataset could not be loaded. {exc}")
    st.caption("Restore the supplied superstore.csv file next to app.py and run the app again.")
    st.stop()

all_markets = sorted(df.market.unique().tolist())
all_categories = sorted(df.category.unique().tolist())
year_bounds = (int(df.year.min()), int(df.year.max()))
for key, value in {
    "markets": all_markets,
    "categories": all_categories,
    "years": year_bounds,
    "exclude_outliers": False,
}.items():
    st.session_state.setdefault(key, value)


def reset_filters():
    st.session_state["markets"] = all_markets
    st.session_state["categories"] = all_categories
    st.session_state["years"] = year_bounds
    st.session_state["exclude_outliers"] = False


with st.sidebar:
    st.markdown(
        "<div class='sidebar-brand'>GLOBAL SUPERSTORE<span>EXPLORATORY ANALYTICS</span></div>",
        unsafe_allow_html=True,
    )
    st.subheader("Shape your view")
    st.caption("Filters apply to every chart and model. Clear selections to see the empty state.")
    markets = st.multiselect("Markets", all_markets, key="markets")
    years = st.slider("Order years", *year_bounds, key="years")
    categories = st.multiselect("Product categories", all_categories, key="categories")
    exclude = st.checkbox(
        "Exclude extreme sales (IQR)",
        key="exclude_outliers",
        help="Statistical extremes are valid observations, not proven errors. The cutoff is calculated once on the complete cleaned dataset.",
    )
    st.button("Reset filters", on_click=reset_filters, width="stretch", icon=":material/restart_alt:")
    st.divider()
    st.markdown("**Dataset at a glance**")
    st.caption(
        f"{audit['clean_rows']:,} order lines · {audit['raw_columns']} source columns\n\n2011–2014 · {df.country.nunique()} countries"
    )
    with st.expander("Source & definitions"):
        st.markdown(f"[Global Superstore / Kaggle]({SOURCE_URL})")
        st.write(
            "A historical retail teaching dataset. One row is one order line; a basket may contain multiple lines. Results describe this file, not current global retail."
        )
        st.write(
            "Profit margin = total profit / total sales. Currency is displayed as USD following the supplied dataset convention; no FX conversion is applied."
        )
        st.write(
            "Basket identity combines country, Order.ID, Customer.ID and Order.Date because raw order identifiers repeat."
        )
    report = ROOT / "output" / "pdf" / "project_report.pdf"
    if report.exists():
        st.download_button(
            "Download one-page report",
            report.read_bytes(),
            file_name="CEN445_Project_Report.pdf",
            mime="application/pdf",
            width="stretch",
        )
    st.markdown(f"[Project repository]({REPOSITORY_URL})")

selected = filter_data(df, markets, categories, years, exclude)
st.markdown("<div class='eyebrow'>CEN445 / DATA VISUALIZATION</div>", unsafe_allow_html=True)
st.title("Global Superstore")
st.markdown(
    "<div class='deck'>Explore where sales grow, where margins disappear, and what order patterns reveal.</div>",
    unsafe_allow_html=True,
)

if selected.empty:
    st.warning(
        "No order lines match this selection. Select at least one market and category, widen the years, or reset the filters."
    )
    st.button("Restore all data", on_click=reset_filters, type="primary")
    st.stop()

context = f"{selected.order_date.min():%d %b %Y} – {selected.order_date.max():%d %b %Y} · {selected.country.nunique():,} countries · {len(markets)} markets · {len(categories)} categories"
st.caption(context)
sales, profit = selected.sales.sum(), selected.profit.sum()
with st.container(key="kpi_strip"):
    k1, k2, k3, k4, k5 = st.columns([1.5, 1.5, 1.2, 1.2, 1.2])
    k1.metric("Sales (USD)", money(sales))
    k2.metric("Profit (USD)", money(profit))
    k3.metric("Profit margin", f"{profit / sales:.1%}")
    k4.metric("Order lines", f"{len(selected):,}")
    k5.metric("Distinct baskets", f"{selected.basket_id.nunique():,}")

if exclude:
    included = filter_data(df, markets, categories, years, False)
    removed = included.loc[included.is_outlier]
    st.warning(
        f"Extreme-sales exclusion is active: {len(removed):,} order lines and {removed.sales.sum() / included.sales.sum():.1%} of sales in your selection are omitted. These are not necessarily data errors."
    )

category = summarize(selected, "category").sort_values("profit", ascending=False).iloc[0]
st.markdown(
    f"**In this selection:** {category.category} contributes the largest total profit ({money(category.profit)}). "
    f"{selected.profit.lt(0).mean():.1%} of order lines lose money; the mean line discount is {selected.discount.mean():.1%}."
)

views = ["Markets & mix", "Orders & relationships", "Profit & performance", "Machine learning"]
view = st.radio(
    "Choose an analysis chapter", views, horizontal=True, key="chapter", label_visibility="collapsed"
)


def render_chart(number, title, kind, chart, interaction):
    with st.container(border=True, key=f"chart_{number}"):
        st.caption(f"FIGURE {number:02d} / {kind.upper()}")
        st.subheader(title)
        st.caption(f"{context}. {interaction}")
        st.plotly_chart(
            chart.figure,
            width="stretch",
            key=f"figure_{number}",
            theme=None,
            alt=f"Figure {number}. {title} {chart.finding}",
            config={
                "displaylogo": False,
                "scrollZoom": False,
                "responsive": True,
                "topojsonURL": "/app/static/geo/",
                "toImageButtonOptions": {"format": "png", "scale": 2},
            },
        )
        st.markdown(f"**Answer (computed for the current selection)**  \n{chart.finding}")
        with st.expander("Read the chart, inspect data & download"):
            st.write(chart.method)
            st.caption(
                "The table is a keyboard-accessible alternative. Downloads reflect this chart's current filters and settings."
            )
            st.dataframe(chart.data.rename(columns=LABELS), hide_index=True, width="stretch")
            st.download_button(
                "Download chart data (CSV)",
                chart.data.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"figure_{number:02d}_data.csv",
                mime="text/csv",
                key=f"download_{number}",
            )


if view == views[0]:
    st.header("Markets & product mix")
    st.write("Start with geography, then separate revenue scale from profitability and customer composition.")
    metric = st.selectbox(
        "Color the map by", ["sales", "profit", "margin"], format_func=lambda x: LABELS[x], key="map_metric"
    )
    render_chart(
        1,
        "Where is business concentrated?",
        "Advanced · Choropleth map",
        map_chart(selected, metric),
        "Color shows the selected metric; hover for sales, profit, margin and basket counts.",
    )
    render_chart(
        2,
        "Which product groups sell well but lose money?",
        "Advanced · Treemap",
        treemap_chart(selected),
        "Rectangle area = sales; amber = negative margin, teal = positive margin. Click to drill down.",
    )
    render_chart(
        3,
        "How does product mix differ across customer segments?",
        "Advanced · Sunburst",
        sunburst_chart(selected),
        "Sector size = sales; color = customer segment. Percentages compare each slice with its parent.",
    )

elif view == views[1]:
    st.header("Orders & relationships")
    st.write(
        "Follow the sales flow, inspect transaction trade-offs, and explore products found in the same basket."
    )
    render_chart(
        4,
        "How do sales flow through shipping modes?",
        "Advanced · Sankey",
        sankey_chart(selected),
        "Link width = sales in USD. Drag nodes or hover a link to inspect its value and share.",
    )
    lines = st.select_slider(
        "Parallel-coordinate sample size", [300, 600, 800, 1200, 1500], value=800, key="parallel_n"
    )
    render_chart(
        5,
        "What distinguishes discounted, loss-making transactions?",
        "Advanced · Parallel coordinates",
        parallel_chart(selected, lines),
        "Each line is one order line. Drag along an axis to select a range locally.",
    )
    c1, c2, c3 = st.columns([1, 1, 1])
    count = c1.slider("Maximum displayed pairs", 5, 35, 20, key="network_top")
    minimum = c2.number_input("Minimum shared baskets", min_value=1, value=5, step=1, key="network_min")
    ranking = c3.selectbox("Rank product pairs by", ["Co-purchase count", "Lift"], key="network_rank")
    graph = cached_network(selected, count, minimum, ranking)
    if graph is None:
        st.info(
            "Figure 06 / Co-purchase network: no product pair meets this threshold. Lower the minimum, select more categories or widen the period."
        )
    else:
        render_chart(
            6,
            "Which product groups are bought together?",
            "Advanced · Network",
            graph,
            "Thicker links = more shared baskets. Hover nodes or link midpoints; use the toolbar to zoom.",
        )

elif view == views[2]:
    st.header("Profit & performance")
    st.write(
        "Compare profit risk, check associations and explore whether revenue growth translates into profit."
    )
    central = st.checkbox(
        "Focus violin density on the central 98%",
        value=True,
        key="violin_central",
        help="Tail observations are excluded from the plotted violin, including its density, inner box plot and mean line. The summary table and finding use all selected lines. Exact bounds and omitted counts appear below the chart.",
    )
    if central:
        lo, hi = selected.profit.quantile([0.01, 0.99])
        omitted = int((~selected.profit.between(lo, hi)).sum())
        st.caption(
            f"Plot shows {money(lo)} to {money(hi)} only (pooled 1st–99th percentiles); {omitted:,} tail observations are excluded from the violin density, inner box plot and mean line. The finding and summary table still use every selected line. Uncheck to plot the complete distribution."
        )
    render_chart(
        7,
        "How often do categories lose money?",
        "Violin with embedded box plot",
        violin_chart(selected, central),
        "Width = estimated density; inner boxes = quartiles and median; dotted reference = zero profit.",
    )
    method = st.selectbox(
        "Correlation method",
        ["Spearman", "Pearson"],
        key="correlation_method",
        help="Spearman compares ranks; Pearson measures a linear relationship and is more sensitive to extreme values.",
    )
    render_chart(
        8,
        "Which measures move together?",
        "Correlation heatmap",
        correlation_chart(selected, method),
        f"{method} correlation, fixed scale −1 to +1. Each cell includes a numeric value.",
    )
    metric = st.selectbox(
        "Measure over time",
        ["sales", "profit", "margin"],
        format_func=lambda x: LABELS[x],
        key="trend_metric",
    )
    render_chart(
        9,
        "Does sales growth translate into profitable growth?",
        "Linked time-series panels with range selector",
        trend_chart(selected, metric),
        "Top = selected metric; bottom = profit margin (or profit). Shared calendar dates; use range handles to zoom both panels.",
    )

else:
    st.header("Machine learning, with context")
    st.write(
        "Two complementary models: explain transaction profiles, then evaluate profitability on held-out observations."
    )
    st.info(
        "These models describe or classify order lines using recorded transaction information. They are not customer segments, causal estimates or a live forecasting service."
    )
    with st.container(border=True):
        st.caption("MODEL 01 / K-MEANS")
        st.subheader("Which transaction profiles emerge?")
        k = st.slider("Number of transaction clusters", 2, 6, 3, key="cluster_k")
        with st.spinner("Computing transaction profiles…"):
            clusters = cached_clusters(selected, k)
        if not clusters["available"]:
            st.warning(clusters["reason"])
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Sampled order lines", f"{len(clusters['sample']):,}")
            c2.metric("Actual clusters", clusters["k"])
            c3.metric(
                "Silhouette (approx.)",
                f"{clusters['silhouette']:.3f}" if clusters["silhouette"] is not None else "Undefined",
            )
            st.plotly_chart(
                cluster_figure(clusters),
                theme=None,
                width="stretch",
                key="cluster_plot",
                alt="K-Means transaction profiles on sales and profit. A detailed profile table follows.",
                config={"displaylogo": False},
            )
            st.dataframe(
                clusters["profiles"],
                hide_index=True,
                width="stretch",
                column_config={
                    "mean_discount": st.column_config.NumberColumn("Mean discount", format="percent"),
                    "loss_rate": st.column_config.NumberColumn("Loss frequency", format="percent"),
                    "share": st.column_config.NumberColumn("Sample share", format="percent"),
                },
            )
            st.caption(
                f"Sales, profit and discount are standardized (z-scores) on a deterministic sample of up to 3,000 lines. k={clusters['k']}; seed 42; 20 initializations. Silhouette uses up to {clusters['silhouette_n']:,} sampled observations: −1 to +1, higher indicates better separation. It does not measure predictive accuracy. Profiles are calculated from the current fit; cluster identity can change after filtering."
            )
            st.download_button(
                "Download cluster profiles",
                clusters["profiles"].to_csv(index=False).encode(),
                file_name="cluster_profiles.csv",
            )
    with st.container(border=True):
        st.caption("MODEL 02 / RANDOM FOREST")
        st.subheader("Can recorded transaction attributes identify non-profitable lines?")
        split = st.selectbox(
            "Evaluation design",
            ["Unseen baskets", "Future period"],
            key="model_split",
            help="Unseen baskets prevents basket overlap. Future period trains on earlier dates and evaluates later dates.",
        )
        with st.spinner("Evaluating the classifier on held-out records…"):
            result = cached_classifier(selected, split)
        if not result["available"]:
            st.warning(result["reason"])
        else:
            a, b, c, d = st.columns(4)
            a.metric(
                "Test accuracy",
                f"{result['accuracy']:.1%}",
                delta=f"{(result['accuracy'] - result['baseline']) * 100:+.1f} pp vs baseline",
            )
            b.metric("Majority baseline", f"{result['baseline']:.1%}")
            c.metric("Balanced accuracy", f"{result['balanced_accuracy']:.1%}")
            d.metric("Non-profitable recall", f"{result['loss_recall']:.1%}")
            st.caption(
                f"{result['split_note']} Fitted: {result['train_n']:,} lines / {result['train_baskets']:,} baskets. Evaluated: {result['test_n']:,} lines / {result['test_baskets']:,} baskets. Basket overlap: {result['basket_overlap']}."
            )
            st.plotly_chart(
                classification_figure(result),
                theme=None,
                width="stretch",
                key="classifier_plot",
                alt="Held-out confusion matrix and permutation importance. Numeric outcomes are available in the evaluation tables below.",
                config={"displaylogo": False},
            )
            missed = int(result["matrix"][0, 1])
            total_nonprofitable = int(result["matrix"][0].sum())
            st.markdown(
                f"**What the evaluation says**  \nThe classifier misses **{missed:,} of {total_nonprofitable:,} non-profitable test lines** by predicting positive profit. Accuracy alone hides this error; non-profitable recall measures the ability to detect the class of interest."
            )
            with st.expander("Evaluation tables, assumptions & limitations"):
                st.dataframe(
                    pd.DataFrame(
                        result["matrix"],
                        index=["Actual non-profitable", "Actual profitable"],
                        columns=["Predicted non-profitable", "Predicted profitable"],
                    ),
                    width="stretch",
                )
                st.dataframe(
                    result["importance"].rename(
                        columns={
                            "importance": "Balanced accuracy decrease",
                            "std": "Repeat standard deviation",
                        }
                    ),
                    hide_index=True,
                    width="stretch",
                )
                distribution = pd.DataFrame(
                    {
                        "Training lines": result["train_class_counts"],
                        "Test lines": result["test_class_counts"],
                    }
                ).rename(index={0: "Non-profitable (profit ≤ 0)", 1: "Profitable (profit > 0)"})
                st.dataframe(distribution, width="stretch")
                st.write(
                    f"Train dates: {result['train_start']:%d %b %Y} to {result['train_end']:%d %b %Y}; test dates: {result['test_start']:%d %b %Y} to {result['test_end']:%d %b %Y}. Macro F1: {result['macro_f1']:.3f}."
                )
                st.write(
                    "Predictors: sales, discount, quantity and shipping cost; target: profit > 0. The actual profit is never a predictor. Recorded shipping cost may only be available after fulfilment, so this is retrospective classification, not a pre-order prediction claim. Zero-profit lines are explicitly non-profitable."
                )
                st.write(
                    "Random Forest: 160 trees, maximum depth 10, minimum leaf size 5, seed 42. Whole baskets/dates are split before limiting fitting to 18,000 training and 6,000 test lines. Majority baseline is fitted on the training labels. No model tuning uses the test set. A single split is an illustrative estimate, not a guarantee of generalization."
                )
                st.write(
                    "Permutation importance is the decrease in held-out balanced accuracy after shuffling one feature (4 repeats). Error bars show repeat standard deviation, not a confidence interval. Importance and correlations do not establish causation."
                )
                st.download_button(
                    "Download held-out feature importance",
                    result["importance"].to_csv(index=False).encode(),
                    file_name="permutation_importance.csv",
                )

st.divider()
with st.expander("Data quality, provenance & reproducibility"):
    a, b, c, d = st.columns(4)
    a.metric("Source rows", f"{audit['raw_rows']:,}")
    b.metric("Duplicate rows removed", f"{audit['duplicate_rows']:,}")
    c.metric("Invalid rows removed", f"{audit['invalid_rows']:,}")
    d.metric("Sales extremes flagged", f"{audit['outlier_count']:,}")
    st.write(
        f"Source file: {audit['raw_columns']} columns; {audit['missing_cells']} initially missing cells. "
        f"{audit['filled_category_cells']} optional categorical cells filled with 'Unknown'. {audit['zero_sales_rows']} zero-sales line(s) retained; a zero denominator gives an undefined margin. No numeric target values are imputed. "
        f"{audit['year_disagreements']} source-year disagreements; {audit['invalid_shipping_dates']} invalid/missing shipping dates. "
        f"{len(audit['unmapped_countries'])} unmapped country codes."
    )
    st.write(
        f"IQR sales bounds are ${audit['iqr_lower']:,.2f} to ${audit['iqr_upper']:,.2f}, fixed on the full cleaned file. "
        f"Flagged extremes account for {audit['outlier_sales_share']:.1%} of full-data sales and are retained by default."
    )
    st.write(
        f"{audit['ambiguous_order_ids']} raw Order.ID groups contain different customer/date/country identities. "
        "Validated composite keys are used for basket counts, networks and model splits. Basket counts under category filters mean baskets containing the selected lines, not complete unfiltered orders."
    )
    st.caption(f"Dataset SHA-256: {audit['sha256']}")
    st.markdown(f"[Dataset source]({SOURCE_URL}) · [Code and methodology]({REPOSITORY_URL})")
st.caption(
    "CEN445 · Global Superstore · Historical data, 2011–2014 · Nine visualization methods + two explanatory ML models"
)
