"""Optional visual QA with Kaleido; exports actual Plotly charts, not UI substitutes."""

# ruff: noqa: E402
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import plotly.io as pio

from analytics import load_dataset
from models import classify_profitability, cluster_transactions
from visuals import (
    classification_figure,
    cluster_figure,
    correlation_chart,
    map_chart,
    network_chart,
    parallel_chart,
    sankey_chart,
    sunburst_chart,
    treemap_chart,
    trend_chart,
    violin_chart,
)


def main():
    df, _ = load_dataset()
    pio.defaults.topojson = (ROOT / "static" / "geo").as_uri() + "/"
    folder = ROOT / "tmp" / "figures"
    folder.mkdir(parents=True, exist_ok=True)
    charts = [
        map_chart(df),
        treemap_chart(df),
        sunburst_chart(df),
        sankey_chart(df),
        parallel_chart(df),
        network_chart(df),
        violin_chart(df, True),
        correlation_chart(df),
        trend_chart(df),
    ]
    figures = [c.figure for c in charts] + [
        cluster_figure(cluster_transactions(df)),
        classification_figure(classify_profitability(df)),
    ]
    for i, fig in enumerate(figures, 1):
        fig.write_image(folder / f"{i:02d}.png", width=1100, height=fig.layout.height or 550, scale=1.4)
        print(f"Rendered figure {i}", flush=True)


if __name__ == "__main__":
    main()
