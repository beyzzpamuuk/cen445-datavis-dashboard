"""Exercise all chapters, interactive alternatives, empty recovery and the old k=6 crash."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class DashboardTests(unittest.TestCase):
    def test_complete_user_journey(self):
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180).run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.get("plotly_chart")), 3)
        self.assertEqual(next(m.value for m in at.metric if m.label == "Distinct baskets"), "25,754")
        at.selectbox(key="map_metric").set_value("margin").run()
        self.assertFalse(at.exception)
        at.radio(key="chapter").set_value("Orders & relationships").run()
        self.assertEqual(len(at.get("plotly_chart")), 3)
        at.selectbox(key="network_rank").set_value("Lift").run()
        self.assertFalse(at.exception)
        at.number_input(key="network_min").set_value(999999).run()
        self.assertTrue(any("no product pair" in x.value for x in at.info))
        at.radio(key="chapter").set_value("Profit & performance").run()
        self.assertEqual(len(at.get("plotly_chart")), 3)
        at.checkbox(key="violin_central").check()
        at.selectbox(key="correlation_method").set_value("Pearson")
        at.selectbox(key="trend_metric").set_value("margin").run()
        self.assertFalse(at.exception)
        at.radio(key="chapter").set_value("Machine learning").run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.get("plotly_chart")), 2)
        at.selectbox(key="model_split").set_value("Future period").run()
        self.assertFalse(at.exception)
        at.slider(key="cluster_k").set_value(6)
        at.multiselect(key="markets").set_value(["Canada"])
        at.multiselect(key="categories").set_value(["Furniture"])
        at.slider(key="years").set_value((2011, 2011)).run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.get("plotly_chart")), 0)
        self.assertTrue(any("at least 20" in w.value for w in at.warning))
        at.multiselect(key="markets").set_value([]).run()
        self.assertFalse(at.exception)
        self.assertTrue(any("No order lines" in w.value for w in at.warning))
        next(b for b in at.button if b.label == "Restore all data").click().run()
        self.assertEqual(len(at.multiselect(key="markets").value), 7)
        self.assertFalse(at.exception)
        at.multiselect(key="categories").set_value([]).run()
        self.assertTrue(any("No order lines" in w.value for w in at.warning))
        next(b for b in at.button if b.label == "Reset filters").click().run()
        at.checkbox(key="exclude_outliers").check().run()
        self.assertFalse(at.exception)
        self.assertEqual(next(m.value for m in at.metric if m.label == "Order lines"), "45,635")


if __name__ == "__main__":
    unittest.main()
