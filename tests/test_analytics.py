"""Regression checks for analytical correctness, not screenshots of implementation."""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from analytics import BASKET_COLUMNS, DATA_PATH, basket_pairs, filter_data, hierarchy_nodes, load_dataset
from models import classify_profitability, cluster_transactions
from visuals import (
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


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df, cls.audit = load_dataset()

    def test_source_reconciliation_and_extremes(self):
        self.assertEqual(self.audit["raw_columns"], 27)
        self.assertEqual(len(self.df), 51290)
        self.assertEqual(self.audit["removed_rows"], 0)
        self.assertEqual(self.audit["outlier_count"], 5655)
        self.assertEqual(self.audit["zero_sales_rows"], 1)
        self.assertEqual(self.df.basket_id.nunique(), 25754)
        self.assertEqual(self.audit["unmapped_countries"], [])
        self.assertAlmostEqual(self.df.sales.sum(), 12642905)
        self.assertAlmostEqual(self.df.profit.sum(), 1467457.29128)

    def test_basket_identity_keeps_different_customer_dates_separate(self):
        self.assertEqual(self.audit["ambiguous_order_ids"], 660)
        self.assertTrue((self.df.groupby("basket_id")[BASKET_COLUMNS].nunique().max().eq(1)).all())
        pairs, _ = basket_pairs(self.df)
        pair = pairs.loc[pairs.source.eq("Binders") & pairs.target.eq("Storage")].iloc[0]
        self.assertEqual(pair.baskets, 899)
        self.assertEqual(int(pairs.baskets.sum()), 37997)

    def test_parent_totals_and_loss_color_sign(self):
        nodes = hierarchy_nodes(self.df, ["market", "category", "sub_category"])
        for node in nodes.itertuples():
            children = nodes.loc[nodes.parent.eq(node.id)]
            if len(children):
                self.assertAlmostEqual(children.sales.sum(), node.sales, places=6)
                self.assertAlmostEqual(children.profit.sum(), node.profit, places=6)
            if node.sales:
                self.assertAlmostEqual(node.margin, node.profit / node.sales * 100)
        target = nodes.loc[nodes.id.eq(json.dumps(["APAC", "Furniture", "Tables"]))].iloc[0]
        self.assertAlmostEqual(target.profit, -20128.7481)
        self.assertLess(target.margin, 0)
        fig = treemap_chart(self.df).figure
        index = list(fig.data[0].ids).index(target.id)
        self.assertLess(fig.data[0].marker.colors[index], 0)

    def test_empty_filters_and_outlier_sensitivity(self):
        markets = self.df.market.unique()
        cats = self.df.category.unique()
        self.assertTrue(filter_data(self.df, [], cats, (2011, 2014)).empty)
        self.assertTrue(filter_data(self.df, markets, [], (2011, 2014)).empty)
        trimmed = filter_data(self.df, markets, cats, (2011, 2014), True)
        self.assertEqual(len(trimmed), 51290 - 5655)
        self.assertAlmostEqual(1 - trimmed.sales.sum() / self.df.sales.sum(), 0.5608366906)

    def test_small_and_single_class_models_are_not_reported_as_success(self):
        tiny = filter_data(self.df, ["Canada"], ["Furniture"], (2011, 2011))
        self.assertEqual(len(tiny), 5)
        self.assertFalse(cluster_transactions(tiny, 6)["available"])
        self.assertFalse(classify_profitability(tiny)["available"])
        self.assertFalse(classify_profitability(self.df.loc[self.df.profit.gt(0)])["available"])

    def test_validation_handles_invalid_profit_and_dates_without_imputing_target(self):
        raw = pd.read_csv(DATA_PATH).head(5).copy()
        raw.loc[0, "Profit"] = np.nan
        raw.loc[1, "Order.Date"] = "not-a-date"
        raw.loc[2, "Discount"] = 2
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.csv"
            raw.to_csv(path, index=False)
            valid, audit = load_dataset(path)
        self.assertEqual(audit["invalid_rows"], 3)
        self.assertEqual(len(valid), 2)

    def test_all_nine_figures_construct_with_alternative_metrics(self):
        charts = [
            map_chart(self.df, "margin"),
            treemap_chart(self.df),
            sunburst_chart(self.df),
            sankey_chart(self.df),
            parallel_chart(self.df, 300),
            network_chart(self.df, 20, 5, "Lift"),
            violin_chart(self.df, True),
            correlation_chart(self.df, "Pearson"),
            trend_chart(self.df, "profit"),
        ]
        for chart in charts:
            self.assertIsNotNone(chart)
            self.assertTrue(len(chart.figure.to_json()) > 100)
            self.assertFalse(chart.data.empty)
            self.assertTrue(chart.finding)

    def test_sankey_conserves_sales_at_each_shipping_node(self):
        fig = sankey_chart(self.df).figure.data[0]
        ship_nodes = [i for i, n in enumerate(fig.node.label) if n in set(self.df.ship_mode)]
        for node in ship_nodes:
            incoming = sum(v for t, v in zip(fig.link.target, fig.link.value) if t == node)
            outgoing = sum(v for s, v in zip(fig.link.source, fig.link.value) if s == node)
            self.assertAlmostEqual(incoming, outgoing)

    def test_held_out_models_have_disjoint_baskets_and_temporal_order(self):
        for split in ["Unseen baskets", "Future period"]:
            result = classify_profitability(self.df, split)
            self.assertTrue(result["available"])
            self.assertEqual(result["basket_overlap"], 0)
            self.assertEqual(result["matrix"].sum(), result["test_n"])
            self.assertTrue(0 <= result["balanced_accuracy"] <= 1)
            if split == "Future period":
                self.assertLess(result["train_end"], result["test_start"])


if __name__ == "__main__":
    unittest.main()
