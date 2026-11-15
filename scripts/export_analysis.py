"""Recompute all report numbers from the bundled dataset (no hand-entered findings)."""

# ruff: noqa: E402
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analytics import basket_pairs, load_dataset, summarize
from models import classify_profitability, cluster_transactions


def money(value):
    return f"-${abs(value):,.0f}" if value < 0 else f"${value:,.0f}"


def research_questions(df, categories, leaves, high, pairs, model, km):
    """One analytical question per figure/model, answered from the full bundled dataset."""
    countries = summarize(df, "country").sort_values("sales", ascending=False)
    top, loss = countries.iloc[0], countries.sort_values("profit").iloc[0]
    worst = leaves.sort_values("profit").iloc[0]
    mix = summarize(df, ["segment", "category"])
    mix["share"] = mix.sales / mix.groupby("segment").sales.transform("sum")
    lead = mix.loc[mix.share.idxmax()]
    ship = summarize(df, "ship_mode").sort_values("sales", ascending=False).iloc[0]
    top_pair = pairs.iloc[0]
    loss_freq = df.groupby("category").profit.agg(lambda x: x.lt(0).mean())
    risky = loss_freq.idxmax()
    spearman = df.discount.corr(df.profit, method="spearman")
    pearson = df.discount.corr(df.profit)
    years = summarize(df, "year").set_index("year")
    first, last = years.index.min(), years.index.max()
    months = summarize(df, "month")
    peak = months.loc[months.sales.idxmax()]
    loss_cluster = min(km["profiles"].to_dict("records"), key=lambda r: r["mean_profit"])
    best_feature = model["importance"].sort_values("importance", ascending=False).iloc[0]
    sales_total = df.sales.sum()
    return [
        {
            "figure": "1 Choropleth",
            "owner": "Beyza Pamuk",
            "question": "Where are sales and losses concentrated geographically?",
            "answer": f"{top.country} has the most sales ({money(top.sales)}, {top.sales / sales_total:.1%} of total); "
            f"{loss.country} has the largest country loss ({money(loss.profit)}, {loss.margin:.1f}% margin).",
        },
        {
            "figure": "2 Treemap",
            "owner": "Beyza Pamuk",
            "question": "Which market-product groups sell but lose money?",
            "answer": f"{worst.market} / {worst.sub_category} has the largest loss: {money(worst.profit)} on "
            f"{money(worst.sales)} sales ({worst.margin:.1f}% margin).",
        },
        {
            "figure": "3 Sunburst",
            "owner": "Sultan Kayı",
            "question": "How does product mix differ across customer segments?",
            "answer": f"Mix is similar across segments; the highest share is {lead.category} in {lead.segment} "
            f"({lead.share:.1%} of that segment's sales).",
        },
        {
            "figure": "4 Sankey",
            "owner": "Sultan Kayı",
            "question": "How do sales flow from segment through shipping mode to category?",
            "answer": f"{ship.ship_mode} carries {ship.sales / sales_total:.1%} of sales ({money(ship.sales)}).",
        },
        {
            "figure": "5 Parallel coordinates",
            "owner": "Nasibe Gül Çetin",
            "question": "What accompanies loss-making transactions?",
            "answer": f"{high.profit.lt(0).mean():.1%} of the {len(high):,} lines discounted above 30% lose money.",
        },
        {
            "figure": "6 Network",
            "owner": "Nasibe Gül Çetin",
            "question": "Which sub-categories are bought together?",
            "answer": f"{top_pair.source} + {top_pair.target} share the most baskets ({top_pair.baskets:,}), "
            f"but lift {top_pair.lift:.2f} shows this reflects popularity, not special affinity.",
        },
        {
            "figure": "7 Violin",
            "owner": "Beyza Pamuk",
            "question": "Which category loses money most often?",
            "answer": f"{risky}: {loss_freq[risky]:.1%} of its order lines lose money "
            f"(overall {df.profit.lt(0).mean():.1%}).",
        },
        {
            "figure": "8 Heatmap",
            "owner": "Sultan Kayı",
            "question": "Which numeric measures move together?",
            "answer": f"Discount and profit are negatively associated: Spearman {spearman:+.2f}, Pearson {pearson:+.2f}.",
        },
        {
            "figure": "9 Time series",
            "owner": "Nasibe Gül Çetin",
            "question": "Does sales growth translate into profitable growth?",
            "answer": f"Sales grew {years.sales[last] / years.sales[first] - 1:.0%} from {first} to {last}, "
            f"while annual margin stayed between {years.margin.min():.1f}% and {years.margin.max():.1f}%; "
            f"peak month {peak.month:%b %Y}.",
        },
        {
            "figure": "ML K-Means",
            "owner": "Team",
            "question": "Which transaction profiles emerge?",
            "answer": f"k={km['k']} (silhouette {km['silhouette']:.2f}); '{loss_cluster['cluster'].split('. ', 1)[-1]}' "
            f"lines average {loss_cluster['mean_discount']:.0%} discount and {loss_cluster['loss_rate']:.0%} lose money.",
        },
        {
            "figure": "ML Random Forest",
            "owner": "Team",
            "question": "Can recorded attributes identify non-profitable lines?",
            "answer": f"{model['accuracy']:.1%} accuracy vs {model['baseline']:.1%} baseline, "
            f"{model['loss_recall']:.1%} non-profitable recall; {best_feature.feature} is the most important feature.",
        },
    ]


def main():
    df, audit = load_dataset()
    pairs, _ = basket_pairs(df)
    categories = summarize(df, "category")
    leaves = summarize(df, ["market", "category", "sub_category"])
    high = df.loc[df.discount.gt(0.3)]
    model = classify_profitability(df)
    future = classify_profitability(df, "Future period")
    km = cluster_transactions(df)
    questions = research_questions(df, categories, leaves, high, pairs, model, km)

    def model_summary(result):
        return {key: value for key, value in result.items() if key != "importance"} | {
            "importance": result["importance"].to_dict("records")
        }

    result = {
        "dataset": audit,
        "sales": float(df.sales.sum()),
        "profit": float(df.profit.sum()),
        "margin": float(df.profit.sum() / df.sales.sum()),
        "loss_rate": float(df.profit.lt(0).mean()),
        "countries": int(df.country.nunique()),
        "categories": categories.to_dict("records"),
        "high_discount_lines": len(high),
        "high_discount_loss_rate": float(high.profit.lt(0).mean()),
        "worst_groups": leaves.sort_values("profit").head(5).to_dict("records"),
        "top_pairs": pairs.head(5).to_dict("records"),
        "rf_unseen_baskets": model_summary(model),
        "rf_future_period": model_summary(future),
        "questions": questions,
        "kmeans": {
            "k": km["k"],
            "silhouette": km["silhouette"],
            "sample_size": len(km["sample"]),
            "profiles": km["profiles"].to_dict("records"),
        },
    }
    folder = ROOT / "docs"
    folder.mkdir(exist_ok=True)

    def serial(value):
        if hasattr(value, "tolist"):
            return value.tolist()
        return str(value)

    path = folder / "analysis_summary.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=serial), encoding="utf-8")
    print(f"Saved {path}")
    for q in questions:
        print(f"[{q['figure']}] {q['question']} -> {q['answer']}")
    print(
        f"RF grouped accuracy {model['accuracy']:.4f}; baseline {model['baseline']:.4f}; balanced {model['balanced_accuracy']:.4f}; non-profitable recall {model['loss_recall']:.4f}"
    )


if __name__ == "__main__":
    main()
