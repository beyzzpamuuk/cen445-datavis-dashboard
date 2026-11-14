"""Recompute all report numbers from the bundled dataset (no hand-entered findings)."""

# ruff: noqa: E402
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from analytics import basket_pairs, load_dataset, summarize
from models import classify_profitability, cluster_transactions


def main():
    df, audit = load_dataset()
    pairs, _ = basket_pairs(df)
    categories = summarize(df, "category")
    leaves = summarize(df, ["market", "category", "sub_category"])
    high = df.loc[df.discount.gt(0.3)]
    model = classify_profitability(df)
    future = classify_profitability(df, "Future period")
    km = cluster_transactions(df)

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
    print(
        f"RF grouped accuracy {model['accuracy']:.4f}; baseline {model['baseline']:.4f}; balanced {model['balanced_accuracy']:.4f}; non-profitable recall {model['loss_recall']:.4f}"
    )


if __name__ == "__main__":
    main()
