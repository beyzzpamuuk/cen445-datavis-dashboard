"""Nine distinct analytical perspectives. Each returns figure, accessible data and finding."""

from dataclasses import dataclass

import networkx as nx
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analytics import CATEGORIES, LABELS, NUMERIC, basket_pairs, hierarchy_nodes, summarize

INK = "#183247"
MUTED = "#526675"
TEAL = "#007F7A"
AMBER = "#B65319"
PALETTE = {"Furniture": "#9A4E1B", "Office Supplies": "#007F7A", "Technology": "#365EAD"}
SEGMENTS = {"Consumer": "#365EAD", "Corporate": "#007F7A", "Home Office": "#9A4E1B"}
# Semantic scale: amber = negative, neutral = zero, teal = positive. Numeric labels also carry sign.
DIVERGING = [[0, "#A84713"], [0.25, "#E8B18B"], [0.5, "#F5F3EE"], [0.75, "#8ACAC3"], [1, "#006C67"]]
SEQUENTIAL = [[0, "#E1EEED"], [0.35, "#8ECBC5"], [0.7, "#268D86"], [1, "#005B57"]]


@dataclass
class Chart:
    figure: go.Figure
    data: pd.DataFrame
    finding: str
    method: str


def money(x):
    return f"-${abs(x):,.0f}" if x < 0 else f"${x:,.0f}"


def theme(fig, height=490):
    fig.update_layout(
        template="plotly_white",
        height=height,
        font=dict(family="Segoe UI, Arial, sans-serif", size=14, color=INK),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=65, r=35, t=35, b=65),
        hoverlabel=dict(bgcolor="white", font_size=14, font_color=INK),
        legend=dict(title_text="", orientation="h", y=1.13, x=0),
        coloraxis_colorbar=dict(thickness=15, len=0.8, outlinewidth=0),
        separators=".,",
    )
    fig.update_xaxes(showgrid=False, automargin=True, linecolor="#CCD7DC", zeroline=False)
    fig.update_yaxes(gridcolor="#E7ECEF", automargin=True, zeroline=False)
    return fig


def map_chart(df, metric="sales"):
    table = summarize(df, ["country", "country_iso3"])
    signed = metric in ["profit", "margin"]
    bound = max(abs(table[metric]).max(), 0.01)
    kwargs = (
        dict(range_color=(-bound, bound), color_continuous_scale=DIVERGING)
        if signed
        else dict(color_continuous_scale=SEQUENTIAL)
    )
    fig = px.choropleth(
        table,
        locations="country_iso3",
        color=metric,
        hover_name="country",
        custom_data=["sales", "profit", "margin", "orders", "lines"],
        labels=LABELS,
        **kwargs,
    )
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>Sales: $%{customdata[0]:,.0f}<br>Profit: $%{customdata[1]:,.0f}<br>Margin: %{customdata[2]:.1f}%<br>Baskets: %{customdata[3]:,}<br>Order lines: %{customdata[4]:,}<extra></extra>",
        marker_line_color="white",
        marker_line_width=0.4,
    )
    theme(fig, 500)
    fig.update_geos(
        projection_type="natural earth",
        showframe=False,
        showcoastlines=False,
        showland=True,
        landcolor="#EEF2F3",
        bgcolor="white",
        showocean=False,
    )
    fig.update_layout(margin=dict(l=0, r=15, t=10, b=10))
    top = table.loc[table[metric].idxmax()]
    value = f"{top[metric]:.1f}%" if metric == "margin" else money(top[metric])
    finding = f"{top.country} leads the selected countries on {LABELS[metric]} ({value}). Country totals describe this dataset, not population-adjusted demand."
    return Chart(
        fig,
        table.sort_values(metric, ascending=False),
        finding,
        "Country totals use ISO 3166-1 alpha-3 codes. Profit margin = sum(profit) / sum(sales). Gray means no mapped observation, not zero. Six small territories (Singapore, Hong Kong, Bahrain, Barbados, Martinique, Guadeloupe; about 0.5% of full-data sales) are too small to draw at this 1:110m map resolution; they remain in the table and all totals. Currency is displayed as USD, following the supplied Superstore convention; no FX conversion is applied.",
    )


def treemap_chart(df):
    nodes = hierarchy_nodes(df, ["market", "category", "sub_category"])
    bound = max(nodes.margin.abs().max(), 1)
    fig = go.Figure(
        go.Treemap(
            ids=nodes.id,
            labels=nodes.label,
            parents=nodes.parent,
            values=nodes.sales,
            branchvalues="total",
            maxdepth=3,
            marker=dict(
                colors=nodes.margin,
                colorscale=DIVERGING,
                cmin=-bound,
                cmax=bound,
                cmid=0,
                colorbar=dict(title="Margin (%)", thickness=15),
                line=dict(width=1, color="white"),
            ),
            customdata=nodes[["profit", "margin", "lines"]].to_numpy(),
            texttemplate="%{label}",
            textfont=dict(size=15),
            hovertemplate="<b>%{label}</b><br>Sales: $%{value:,.0f}<br>Profit: $%{customdata[0]:,.0f}<br>Margin: %{customdata[1]:.1f}%<br>Order lines: %{customdata[2]:,}<extra></extra>",
            pathbar=dict(visible=True, textfont_size=14),
            tiling=dict(pad=3),
        )
    )
    theme(fig, 550)
    fig.update_layout(margin=dict(l=5, r=30, t=15, b=15), uniformtext=dict(minsize=12, mode="hide"))
    leaves = summarize(df, ["market", "category", "sub_category"])
    loss = leaves.loc[leaves.profit.lt(0)].sort_values("profit")
    if len(loss):
        row = loss.iloc[0]
        finding = f"{row.market} / {row.sub_category} has the largest aggregate loss: {money(row.profit)} on {money(row.sales)} sales ({row.margin:.1f}% margin)."
    else:
        finding = "Every selected market / category / sub-category group is profitable in aggregate. Individual order lines can still lose money."
    return Chart(
        fig,
        leaves,
        finding,
        "Area = sales; color = aggregate profit margin. Every parent and leaf is calculated from its own profit and sales totals. Initial depth is limited for readability; click a block to reveal the next level and use the path bar to return.",
    )


def sunburst_chart(df):
    nodes = hierarchy_nodes(df, ["segment", "category", "sub_category"])

    def node_color(row):
        if row.depth == 0:
            return "#F0F4F5"
        import json

        path = json.loads(row.id)
        return SEGMENTS.get(path[0], TEAL)

    colors = nodes.apply(node_color, axis=1)
    fig = go.Figure(
        go.Sunburst(
            ids=nodes.id,
            labels=nodes.label,
            parents=nodes.parent,
            values=nodes.sales,
            branchvalues="total",
            maxdepth=3,
            sort=False,
            marker=dict(colors=colors, line=dict(color="white", width=2)),
            customdata=nodes[["profit", "margin", "lines"]].to_numpy(),
            textinfo="label+percent parent",
            insidetextorientation="radial",
            hovertemplate="<b>%{label}</b><br>Sales: $%{value:,.0f}<br>Share of parent: %{percentParent:.1%}<br>Profit: $%{customdata[0]:,.0f}<br>Margin: %{customdata[1]:.1f}%<extra></extra>",
        )
    )
    theme(fig, 550)
    fig.update_layout(margin=dict(l=5, r=5, t=10, b=10), uniformtext=dict(minsize=12, mode="hide"))
    table = summarize(df, ["segment", "category", "sub_category"])
    table["segment_share"] = table.sales / table.groupby("segment").sales.transform("sum")
    mix = summarize(df, ["segment", "category"])
    mix["share"] = mix.sales / mix.groupby("segment").sales.transform("sum")
    leader = mix.loc[mix.share.idxmax()]
    return Chart(
        fig,
        table,
        f"{leader.segment} has its strongest category concentration in {leader.category}: {leader.share:.1%} of that segment's sales. Segment shares use each segment's own total.",
        "Angle/area = sales; hue identifies the customer segment, not profit. Percentages are relative to the immediate parent. Click a segment or category to explore its product mix. This answers a composition question rather than the treemap's profitability question.",
    )


def sankey_chart(df):
    stages = ["segment", "ship_mode", "category"]
    nodes = [(stage, str(v)) for stage in stages for v in sorted(df[stage].unique())]
    indices = {key: i for i, key in enumerate(nodes)}
    sources = []
    targets = []
    values = []
    profits = []
    rows = []
    colors = []
    stage_colors = {"segment": "#365EAD", "ship_mode": "#758996", "category": TEAL}
    for a, b in zip(stages[:-1], stages[1:]):
        agg = summarize(df, [a, b])
        for _, r in agg.iterrows():
            sources.append(indices[(a, str(r[a]))])
            targets.append(indices[(b, str(r[b]))])
            values.append(r.sales)
            profits.append([r.profit, r.sales / df.sales.sum() * 100])
            colors.append("rgba(54,94,173,0.25)" if a == "segment" else "rgba(0,127,122,0.25)")
            rows.append(
                {
                    "stage": f"{LABELS[a]} -> {LABELS[b]}",
                    "source": r[a],
                    "target": r[b],
                    "sales": r.sales,
                    "profit": r.profit,
                    "share": r.sales / df.sales.sum(),
                }
            )
    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            valueformat=",.0f",
            valuesuffix=" USD",
            node=dict(
                label=[v for _, v in nodes],
                pad=24,
                thickness=18,
                color=[stage_colors[s] for s, _ in nodes],
                line=dict(color="white", width=1),
                hovertemplate="%{label}<br>Sales through node: $%{value:,.0f}<extra></extra>",
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=colors,
                customdata=profits,
                hovertemplate="%{source.label} → %{target.label}<br>Sales: $%{value:,.0f}<br>Profit: $%{customdata[0]:,.0f}<br>Share of all selected sales: %{customdata[1]:.1f}%<extra></extra>",
            ),
        )
    )
    theme(fig, 510)
    fig.update_layout(margin=dict(l=15, r=20, t=45, b=20))
    for x, label in [(0, "CUSTOMER SEGMENT"), (0.5, "SHIPPING MODE"), (1, "PRODUCT CATEGORY")]:
        fig.add_annotation(
            x=x,
            y=1.08,
            xref="paper",
            yref="paper",
            text=label,
            showarrow=False,
            font=dict(size=12, color=MUTED),
        )
    ship = summarize(df, "ship_mode").sort_values("sales", ascending=False).iloc[0]
    return Chart(
        fig,
        pd.DataFrame(rows),
        f"{ship.ship_mode} carries {ship.sales / df.sales.sum():.1%} of selected sales ({money(ship.sales)}). Flow width measures dollars, not order count or delivery speed.",
        "Each link is summed sales (USD). At each shipping node incoming and outgoing sales are conserved. The two stages are marginal aggregates: a merged shipping node does not preserve a specific segment-to-category path. Drag nodes to rearrange; hover links for value, profit and share.",
    )


def parallel_chart(df, max_lines=800):
    sample = df.sample(min(max_lines, len(df)), random_state=42).copy()
    bound = max(float(sample.profit.abs().max()), 1)
    dims = []
    short = {
        "sales": "Sales ($)",
        "profit": "Profit ($)",
        "discount": "Discount (%)",
        "quantity": "Units",
        "shipping_cost": "Shipping ($)",
    }
    for col in NUMERIC:
        vals = sample[col] * 100 if col == "discount" else sample[col]
        dims.append(dict(label=short[col], values=vals))
    fig = go.Figure(
        go.Parcoords(
            dimensions=dims,
            labelangle=0,
            labelside="top",
            labelfont=dict(size=14, color=INK),
            tickfont=dict(size=12, color=MUTED),
            line=dict(
                color=sample.profit,
                colorscale=DIVERGING,
                cmin=-bound,
                cmax=bound,
                cmid=0,
                showscale=True,
                colorbar=dict(title="Profit ($)", thickness=14),
            ),
        )
    )
    theme(fig, 500)
    fig.update_layout(margin=dict(l=85, r=110, t=65, b=45))
    high = df.loc[df.discount.gt(0.3)]
    finding = (
        f"Among {len(high):,} selected order lines discounted more than 30%, {high.profit.lt(0).mean():.1%} make a loss. This is an association, not a causal estimate."
        if len(high)
        else "No selected order line has a discount greater than 30%; widen the filters to explore that trade-off."
    )
    return Chart(
        fig,
        sample[["sales", "profit", "discount", "quantity", "shipping_cost"]],
        finding,
        f"One polyline = one order line. Deterministic sample: {len(sample):,} of {len(df):,} records (seed 42). Axes use their own units, not a shared scale. Drag a range on an axis to brush this chart; double-click the axis to clear. Brushing is local, not a global dashboard filter. The finding uses all selected records.",
    )


def network_chart(df, top_n=20, min_baskets=1, ranking="Co-purchase count"):
    pairs, n_baskets = basket_pairs(df)
    eligible = pairs.loc[pairs.baskets.ge(min_baskets)].copy()
    sort_col = "lift" if ranking == "Lift" else "baskets"
    edges = eligible.sort_values([sort_col, "baskets"], ascending=False).head(top_n)
    if edges.empty:
        return None
    graph = nx.Graph()
    for r in edges.itertuples():
        graph.add_edge(r.source, r.target, weight=int(r.baskets))
    # An unweighted layout avoids squeezing frequent hubs into a dense central knot.
    pos = nx.spring_layout(graph, seed=42, k=1.5, iterations=200, weight=None)
    fig = go.Figure()
    max_count = edges.baskets.max()
    mid_x = []
    mid_y = []
    mid_data = []
    for r in edges.itertuples():
        x0, y0 = pos[r.source]
        x1, y1 = pos[r.target]
        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                showlegend=False,
                hoverinfo="skip",
                line=dict(color="rgba(100,126,141,.42)", width=0.7 + 4 * np.sqrt(r.baskets / max_count)),
            )
        )
        mid_x.append((x0 + x1) / 2)
        mid_y.append((y0 + y1) / 2)
        mid_data.append([r.source, r.target, r.baskets, r.support, r.lift])
    fig.add_trace(
        go.Scatter(
            x=mid_x,
            y=mid_y,
            mode="markers",
            showlegend=False,
            marker=dict(size=14, color="rgba(0,127,122,0.03)"),
            customdata=mid_data,
            hovertemplate="<b>%{customdata[0]} + %{customdata[1]}</b><br>Shared baskets: %{customdata[2]:,}<br>Support: %{customdata[3]:.2%}<br>Lift: %{customdata[4]:.2f}<extra></extra>",
        )
    )
    names = list(graph.nodes)
    degrees = [graph.degree(n) for n in names]
    weights = [graph.degree(n, weight="weight") for n in names]
    max_weight = max(weights)
    fig.add_trace(
        go.Scatter(
            x=[pos[n][0] for n in names],
            y=[pos[n][1] for n in names],
            mode="markers+text",
            text=names,
            textposition=["top center" if pos[n][1] >= 0 else "bottom center" for n in names],
            textfont=dict(size=14, color=INK),
            showlegend=False,
            marker=dict(
                size=[17 + 25 * np.sqrt(w / max_weight) for w in weights],
                color="#90CBC5",
                line=dict(color=TEAL, width=2),
            ),
            customdata=list(zip(degrees, weights)),
            hovertemplate="<b>%{text}</b><br>Displayed neighbours: %{customdata[0]}<br>Sum of displayed pair counts: %{customdata[1]:,}<extra></extra>",
        )
    )
    theme(fig, 580)
    fig.update_xaxes(visible=False, range=[-1.3, 1.3])
    fig.update_yaxes(visible=False, range=[-1.3, 1.3], scaleanchor="x", scaleratio=1)
    fig.update_layout(margin=dict(l=60, r=60, t=25, b=25), dragmode="pan")
    top = edges.iloc[0]
    return Chart(
        fig,
        edges,
        f"{top.source} + {top.target} leads the displayed pairs by {ranking.lower()}: {top.baskets:,} shared baskets, {top.support:.1%} support and {top.lift:.2f} lift.",
        f"Basket key = country + Order.ID + Customer.ID + Order.Date. Denominator: {n_baskets:,} selected baskets, including single-item baskets. Support = pair baskets / all baskets. Lift = observed co-occurrence / independent expectation; >1 indicates positive association. Thicker edges = more shared baskets; larger nodes = sum of displayed pair counts. Hover edge midpoints or nodes, pan and zoom. Category filters restrict basket contents; results do not describe excluded items. Only the top {len(edges)} eligible pairs are shown; layout position has no business meaning.",
    )


def violin_chart(df, central=False):
    low, high = df.profit.quantile([0.01, 0.99])
    shown = df.loc[df.profit.between(low, high)] if central else df
    fig = px.violin(
        shown,
        x="category",
        y="profit",
        color="category",
        color_discrete_map=PALETTE,
        category_orders={"category": CATEGORIES},
        box=True,
        points=False,
        labels=LABELS,
    )
    fig.update_traces(
        meanline_visible=True,
        spanmode="hard",
        opacity=0.75,
        hovertemplate="%{x}<br>Profit: $%{y:,.2f}<extra></extra>",
    )
    theme(fig, 490)
    fig.add_hline(y=0, line_color=INK, line_width=1, line_dash="dot")
    fig.update_layout(showlegend=False)
    table = (
        df.groupby("category")
        .agg(
            lines=("profit", "size"),
            median_profit=("profit", "median"),
            mean_profit=("profit", "mean"),
            min_profit=("profit", "min"),
            max_profit=("profit", "max"),
            loss_rate=("profit", lambda s: float(s.lt(0).mean())),
        )
        .reset_index()
    )
    worst = table.sort_values("loss_rate", ascending=False).iloc[0]
    note = (
        f" Display shows the pooled 1st–99th percentile ({money(low)} to {money(high)}); {len(df) - len(shown):,} tails are hidden from the density only."
        if central
        else " All valid profit values are shown; extreme values can compress the central density."
    )
    return Chart(
        fig,
        table,
        f"{worst.category} has the highest selected loss frequency ({worst.loss_rate:.1%}); its median order-line profit is {money(worst.median_profit)}. Summary statistics use all selected lines.",
        "Width approximates profit density; the inner box shows quartiles and median; the dashed horizontal reference is zero profit. Mean lines are also displayed. Small samples do not support stable density estimates."
        + note,
    )


def correlation_chart(df, method="Spearman"):
    corr = df[NUMERIC].corr(method=method.lower())
    pretty = [LABELS[c] for c in NUMERIC]
    fig = go.Figure(
        go.Heatmap(
            z=corr.to_numpy(),
            x=pretty,
            y=pretty,
            zmin=-1,
            zmax=1,
            zmid=0,
            colorscale=DIVERGING,
            text=corr.round(2).to_numpy(),
            texttemplate="%{text:.2f}",
            textfont=dict(size=16),
            xgap=3,
            ygap=3,
            colorbar=dict(title="Correlation", thickness=15),
            hovertemplate="%{x} × %{y}<br>Correlation: %{z:.3f}<extra></extra>",
        )
    )
    theme(fig, 490)
    fig.update_xaxes(side="bottom", tickangle=0)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    # Long category labels wrap inside the axes without rotation.
    short = ["Sales<br>(USD)", "Profit<br>(USD)", "Discount", "Units", "Shipping<br>cost (USD)"]
    fig.update_xaxes(tickvals=pretty, ticktext=short)
    fig.update_layout(margin=dict(l=160, r=60, t=10, b=85))
    r = corr.loc["discount", "profit"]
    finding = (
        (
            f"Discount and profit have {method} correlation {r:+.2f} in {len(df):,} selected lines. {method} measures "
            + (
                "rank association, reducing sensitivity to extreme magnitudes."
                if method == "Spearman"
                else "linear association and can be influenced by extreme transactions."
            )
        )
        if pd.notna(r)
        else "Discount or profit is constant in this selection; its correlation is undefined, not zero."
    )
    return Chart(
        fig,
        corr.rename(index=LABELS, columns=LABELS).reset_index(names="Variable"),
        finding,
        f"{method} correlation across all selected lines. Scale is fixed at [-1, +1]; cells include numeric labels. Blank cells indicate undefined correlation, usually from a constant variable. Association does not establish causation; omitted category and market effects can confound it.",
    )


def trend_chart(df, metric="sales"):
    table = summarize(df, ["month", "category"])
    months = pd.date_range(df.month.min(), df.month.max(), freq="MS")
    # Missing months stay missing: do not draw invented zero revenue or connect gaps.
    companion = "profit" if metric == "margin" else "margin"
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12, row_heights=[0.6, 0.4])
    for i, cat in enumerate(CATEGORIES):
        if cat not in table.category.values:
            continue
        values = table.loc[table.category.eq(cat)].set_index("month").reindex(months)
        fig.add_trace(
            go.Scatter(
                x=months,
                y=values[metric],
                name=cat,
                legendgroup=cat,
                mode="lines+markers",
                connectgaps=False,
                line=dict(color=PALETTE[cat], width=2.8),
                marker=dict(size=5, symbol=["circle", "square", "diamond"][i]),
                customdata=values[["sales", "profit", "margin", "lines"]].to_numpy(),
                hovertemplate=f"<b>{cat}</b><br>%{{x|%b %Y}}<br>Sales: $%{{customdata[0]:,.0f}}<br>Profit: $%{{customdata[1]:,.0f}}<br>Margin: %{{customdata[2]:.1f}}%<br>Order lines: %{{customdata[3]:,.0f}}<extra></extra>",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=months,
                y=values[companion],
                name=cat,
                legendgroup=cat,
                showlegend=False,
                mode="lines+markers",
                connectgaps=False,
                line=dict(color=PALETTE[cat], width=2.2),
                marker=dict(size=4, symbol=["circle", "square", "diamond"][i]),
                hovertemplate=f"<b>{cat}</b><br>%{{x|%b %Y}}<br>{LABELS[companion]}: %{{y:.2f}}<extra></extra>",
            ),
            row=2,
            col=1,
        )
    theme(fig, 660)
    fig.update_xaxes(type="date", tickformat="%b\n%Y", title=None)
    fig.update_xaxes(
        rangeslider=dict(visible=True, thickness=0.12),
        rangeselector=dict(
            buttons=[
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all", label="All"),
            ]
        ),
        row=2,
        col=1,
    )
    # Date shortcuts live above the first panel, away from margin observations.
    fig.update_xaxes(rangeselector=dict(visible=False), row=2, col=1)
    fig.update_xaxes(
        rangeselector=dict(
            visible=True,
            x=0,
            y=1.05,
            buttons=[
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all", label="All"),
            ],
        ),
        row=1,
        col=1,
    )
    fig.update_layout(margin=dict(l=75, r=30, t=75, b=65), legend=dict(y=1.18))
    fig.update_yaxes(
        title=LABELS[metric],
        tickprefix="" if metric == "margin" else "$",
        ticksuffix="%" if metric == "margin" else "",
        rangemode="tozero",
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title=LABELS[companion],
        tickprefix="" if companion == "margin" else "$",
        ticksuffix="%" if companion == "margin" else "",
        rangemode="tozero",
        row=2,
        col=1,
    )
    if metric in ["profit", "margin"]:
        fig.add_hline(y=0, line_color=INK, line_width=1, row=1, col=1)
    fig.add_hline(y=0, line_color=INK, line_width=1, row=2, col=1)
    totals = summarize(df, "month")
    peak = totals.loc[totals[metric].idxmax()]
    value = f"{peak[metric]:.1f}%" if metric == "margin" else money(peak[metric])
    return Chart(
        fig,
        table,
        f"Across the selected categories, {peak.month:%B %Y} has the highest monthly {LABELS[metric]} ({value}). This is the observed peak, not a forecast.",
        "Linked panels share calendar dates but use separate, labeled units; there is no dual-axis overlay. The upper panel shows the selected measure; the lower panel shows margin (or profit when margin is selected). Margin is calculated from monthly totals, not averaged line margins. Drag the bottom range handles or use 6m / 1y / All. Legend clicks control a category in both panels. Marker shapes reinforce category colors; missing months are gaps. This is historical observational data, not a forecast.",
    )


def cluster_figure(result):
    sample = result["sample"]
    profile_order = sorted(sample.cluster.unique())
    profile_colors = {
        name: AMBER if "Loss-making" in name else "#365EAD" if "High-value" in name else TEAL
        for name in profile_order
    }
    fig = px.scatter(
        sample,
        x="sales",
        y="profit",
        color="cluster",
        symbol="cluster",
        color_discrete_map=profile_colors,
        category_orders={"cluster": profile_order},
        hover_data={"discount": ":.1%", "quantity": True, "cluster": True},
        labels={**LABELS, "cluster": "Transaction profile"},
        opacity=0.7,
    )
    theme(fig, 530)
    fig.update_layout(legend=dict(orientation="h", y=-0.22, x=0), margin=dict(l=70, r=25, t=20, b=125))
    fig.add_hline(y=0, line_dash="dot", line_color=MUTED)
    fig.update_xaxes(tickprefix="$")
    fig.update_yaxes(tickprefix="$")
    return fig


def classification_figure(result):
    fig = make_subplots(
        rows=1,
        cols=2,
        horizontal_spacing=0.22,
        subplot_titles=["Held-out outcomes (counts)", "Held-out permutation importance"],
    )
    labels = ["Non-profitable<br>≤ $0", "Profitable<br>> $0"]
    fig.add_trace(
        go.Heatmap(
            z=result["matrix"],
            x=labels,
            y=labels,
            colorscale=SEQUENTIAL,
            text=result["matrix"],
            texttemplate="%{text:,}",
            textfont=dict(size=20),
            showscale=False,
            hovertemplate="Actual: %{y}<br>Predicted: %{x}<br>Lines: %{z:,}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    imp = result["importance"].copy()
    fig.add_trace(
        go.Scatter(
            x=imp.importance * 100,
            y=imp.feature.map(LABELS),
            mode="markers",
            marker=dict(color=TEAL, size=12),
            error_x=dict(type="data", array=imp["std"] * 100, color=TEAL),
            hovertemplate="%{y}<br>Balanced accuracy drop: %{x:.2f} pp<extra></extra>",
            showlegend=False,
        ),
        row=1,
        col=2,
    )
    theme(fig, 440)
    fig.update_xaxes(title="Predicted class", tickangle=0, row=1, col=1)
    fig.update_yaxes(title="Actual class", autorange="reversed", row=1, col=1)
    fig.update_xaxes(
        title="Balanced accuracy drop (percentage points)", zeroline=True, zerolinecolor=MUTED, row=1, col=2
    )
    fig.update_layout(margin=dict(l=125, r=40, t=60, b=90))
    return fig
