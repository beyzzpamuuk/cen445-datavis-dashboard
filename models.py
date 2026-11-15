"""Exploratory transaction segmentation and honest held-out profitability evaluation."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    recall_score,
    silhouette_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler

CLUSTER_FEATURES = ["sales", "profit", "discount"]
PREDICTORS = ["sales", "discount", "quantity", "shipping_cost"]
SEED = 42


def cluster_transactions(df, k=3):
    sample = df.sample(min(3000, len(df)), random_state=SEED).copy()
    distinct = len(sample[CLUSTER_FEATURES].drop_duplicates())
    if len(sample) < 20 or distinct < 3:
        return {
            "available": False,
            "reason": "Clustering needs at least 20 order lines and 3 distinct feature vectors. Widen the filters.",
        }
    k = max(2, min(int(k), 6, distinct, len(sample) - 1))
    scaler = StandardScaler()
    scaled = scaler.fit_transform(sample[CLUSTER_FEATURES])
    km = KMeans(n_clusters=k, random_state=SEED, n_init=20).fit(scaled)
    # Order labels by mean profit to make profiles easier to compare within a fit.
    sample["original_cluster"] = km.labels_
    ordered = sample.groupby("original_cluster").profit.mean().sort_values().index
    names = {}
    for i, original in enumerate(ordered):
        part = sample.loc[sample.original_cluster.eq(original)]
        if part.profit.mean() <= 0:
            desc = "Loss-making / high discount" if part.discount.mean() >= 0.3 else "Loss-making"
        elif part.sales.mean() > sample.sales.mean() * 1.5:
            desc = "High-value / profitable"
        else:
            desc = "Core / profitable"
        names[original] = f"{i + 1}. {desc}"
    sample["cluster"] = sample.original_cluster.map(names)
    profiles = (
        sample.groupby("cluster")
        .agg(
            lines=("sales", "size"),
            mean_sales=("sales", "mean"),
            mean_profit=("profit", "mean"),
            mean_discount=("discount", "mean"),
            loss_rate=("profit", lambda s: float((s < 0).mean())),
        )
        .reset_index()
    )
    profiles["share"] = profiles.lines / len(sample)
    # A deterministic SUBSAMPLE approximates silhouette; it is not a forecast score.
    idx = np.random.default_rng(SEED).choice(len(sample), min(1200, len(sample)), replace=False)
    labels = km.labels_[idx]
    score = silhouette_score(scaled[idx], labels) if 1 < len(set(labels)) < len(idx) else None
    return {
        "available": True,
        "sample": sample,
        "profiles": profiles,
        "k": k,
        "silhouette": float(score) if score is not None else None,
        "silhouette_n": len(idx),
    }


def classify_profitability(df, split="Unseen baskets"):
    if len(df) < 100 or df.basket_id.nunique() < 30:
        return {
            "available": False,
            "reason": "Classification needs at least 100 order lines and 30 baskets. Widen the filters.",
        }
    data = df.copy()
    target = data.profit.gt(0).astype(int)
    if target.nunique() != 2 or target.value_counts().min() < 20:
        return {
            "available": False,
            "reason": "Both classes need at least 20 order lines for a useful evaluation. Zero profit belongs to the non-profitable class.",
        }
    if split == "Future period":
        dates = np.sort(data.order_date.unique())
        if len(dates) < 20:
            return {"available": False, "reason": "Time evaluation needs at least 20 distinct order dates."}
        cutoff = dates[min(int(len(dates) * 0.75), len(dates) - 1)]
        train = data.loc[data.order_date.lt(cutoff)].copy()
        test = data.loc[data.order_date.ge(cutoff)].copy()
        split_note = (
            f"Earlier dates train the model; dates from {pd.Timestamp(cutoff):%d %b %Y} are held out."
        )
    else:
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=SEED)
        train_idx, test_idx = next(splitter.split(data, target, groups=data.basket_id))
        train, test = data.iloc[train_idx].copy(), data.iloc[test_idx].copy()
        split_note = (
            "25% of distinct baskets are held out. No basket appears in both sets; dates can overlap."
        )
    # Split full baskets first, then sample ONLY to limit fitting cost, keeping disjoint sets.
    train = train.sample(min(18000, len(train)), random_state=SEED)
    test = test.sample(min(6000, len(test)), random_state=SEED)
    y_train, y_test = train.profit.gt(0).astype(int), test.profit.gt(0).astype(int)
    if min(len(train), len(test)) < 30 or min(y_train.nunique(), y_test.nunique()) != 2:
        return {
            "available": False,
            "reason": "This split lacks enough records or both classes. Widen the filters or change the evaluation split.",
        }
    if min(y_train.value_counts().min(), y_test.value_counts().min()) < 5:
        return {
            "available": False,
            "reason": "Each class needs at least 5 records in both train and test partitions. Widen the filters.",
        }
    model = RandomForestClassifier(
        n_estimators=160, max_depth=10, min_samples_leaf=5, random_state=SEED, n_jobs=-1
    )
    model.fit(train[PREDICTORS], y_train)
    pred = model.predict(test[PREDICTORS])
    dummy = DummyClassifier(strategy="most_frequent").fit(train[PREDICTORS], y_train)
    baseline = accuracy_score(y_test, dummy.predict(test[PREDICTORS]))
    # Measured on held-out examples rather than training impurity importance.
    importance = permutation_importance(
        model, test[PREDICTORS], y_test, scoring="balanced_accuracy", n_repeats=4, random_state=SEED, n_jobs=1
    )
    imp = pd.DataFrame(
        {"feature": PREDICTORS, "importance": importance.importances_mean, "std": importance.importances_std}
    ).sort_values("importance")
    return {
        "available": True,
        "accuracy": float(accuracy_score(y_test, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, pred)),
        "baseline": float(baseline),
        "loss_recall": float(recall_score(y_test, pred, pos_label=0, zero_division=0)),
        "macro_f1": float(f1_score(y_test, pred, average="macro", zero_division=0)),
        "matrix": confusion_matrix(y_test, pred, labels=[0, 1]),
        "importance": imp,
        "train_n": len(train),
        "test_n": len(test),
        "train_baskets": int(train.basket_id.nunique()),
        "test_baskets": int(test.basket_id.nunique()),
        "basket_overlap": len(set(train.basket_id) & set(test.basket_id)),
        "train_start": train.order_date.min(),
        "train_end": train.order_date.max(),
        "test_start": test.order_date.min(),
        "test_end": test.order_date.max(),
        "split_note": split_note,
        "train_class_counts": y_train.value_counts().sort_index().to_dict(),
        "test_class_counts": y_test.value_counts().sort_index().to_dict(),
    }
