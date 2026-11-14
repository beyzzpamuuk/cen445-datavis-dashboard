\# 📊 Global Superstore Exploratory Data Visualization Dashboard



\*\*Course:\*\* CEN445 – Introduction to Data Visualization  

\*\*Team Members:\*\* Beyza Pamuk, Sultan Kayı, Nasibe Gül Çetin  



\## 📌 Project Overview

This project presents an interactive exploratory data visualization and machine learning dashboard built with \*\*Python\*\*, \*\*Streamlit\*\*, and \*\*Plotly\*\*. It analyzes the \*\*Global Superstore Dataset\*\* (51,290 transactions and 24 attributes) to uncover actionable insights regarding global sales distribution, product hierarchy performance, shipping flows, cross-selling networks, discount-profit trade-offs, and predictive order profitability.



\## 📂 Dataset Details \& Preprocessing

\* \*\*Dataset Source:\*\* \[Kaggle Global Superstore Dataset](https://www.kaggle.com/datasets/fatihilhan/global-superstore-dataset)

\* \*\*Volume \& Structure:\*\* 51,290 rows and 24 columns (exceeding the minimum requirement of 2,000 rows and 7 columns), combining geographical, hierarchical categorical, temporal, and continuous numerical variables.

\* \*\*Data Cleaning \& Preprocessing:\*\*

&#x20; \* Standardized column naming conventions and parsed temporal attributes (`order\_date` into `year` and `year\_month`).

&#x20; \* Removed duplicate records and handled missing values across critical attributes (`sales`, `profit`, `category`, `country`) and imputed numerical medians where needed.

&#x20; \* Detected \*\*5,655 statistical sales outliers\*\* using the \*\*Interquartile Range (IQR)\*\* method ($Q\_1 - 1.5 \\times IQR$ and $Q\_3 + 1.5 \\times IQR$), providing an interactive toggle on the sidebar to include or exclude extreme values dynamically.



\## 📈 Dashboard Features \& 9 Visualization Methods

The dashboard features \*\*4 interactive sidebar controls\*\* (Market multiselect dropdown, Order Year range slider, IQR Outlier checkbox, and Category multiselect) and \*\*9 distinct interactive visualizations\*\* (6 Advanced + 3 Analytical):



1\. \*\*Global Choropleth Map (Advanced):\*\* Country-level spatial revenue distribution with hover tooltips for profit and order counts.

2\. \*\*Hierarchical Treemap (Advanced):\*\* Drill-down across `Market → Category → Sub-Category` sized by sales and colored by profit margin.

3\. \*\*Segment-to-Product Sunburst Chart (Advanced):\*\* Radial multi-level hierarchy of `Segment → Category → Sub-Category`.

4\. \*\*Order Flow Sankey Diagram (Advanced):\*\* Multi-stage volume flow connecting `Customer Segment → Shipping Mode → Product Category`.

5\. \*\*Multidimensional Parallel Coordinates Plot (Advanced):\*\* Interactive axis-brushing across `Sales`, `Profit`, `Discount`, `Quantity`, and `Shipping Cost`.

6\. \*\*Product Co-Occurrence Network Diagram (Advanced):\*\* Graph theory network (`networkx`) mapping top co-purchased sub-categories within multi-item orders.

7\. \*\*Category Profit Violin \& Box Plot (Analytical):\*\* Probability density and interquartile spread of profits across categories.

8\. \*\*Pearson Correlation Heatmap (Analytical):\*\* Annotated correlation matrix highlighting relationships among numerical metrics.

9\. \*\*Monthly Sales \& Profit Time-Series Trajectory (Analytical):\*\* Interactive multi-line trend chart equipped with a temporal range slider.



\## 🤖 Machine Learning Integration

\* \*\*Model 1 – K-Means Transaction Clustering:\*\* Unsupervised clustering on standardized `Sales`, `Profit`, and `Discount` with an interactive slider ($k = 2 \\dots 6$) to segment high-value profitable orders from discount-driven loss clusters.

\* \*\*Model 2 – Random Forest Profitability Classifier:\*\* Supervised classification predicting whether an order yields positive profit (`Profit > 0`), displaying real-time test accuracy (\~83%+) and an interactive \*\*Feature Importance\*\* bar chart demonstrating that `Discount` is the primary driver of margin erosion.



\## 👥 Team Contributions

All team members collaborated closely across dataset selection, exploratory analysis, dashboard integration, and documentation. Individual primary responsibilities and chart ownership (3 visualizations per member: 2 Advanced + 1 Analytical) are structured as follows:



\* \*\*Beyza Pamuk:\*\*

&#x20; \* Co-designed data preprocessing pipeline (IQR outlier detection, date parsing) and Streamlit layout/sidebar filter architecture.

&#x20; \* \*\*Visualizations (3):\*\* 1. Global Sales \& Profit Choropleth Map (Advanced), 2. Hierarchical Treemap (Advanced), 7. Profit Distribution Violin Plot (Analytical).

&#x20; \* Co-implemented K-Means Clustering integration and authored technical documentation.

\* \*\*Sultan Kayı:\*\*

&#x20; \* Co-designed data cleaning, missing value imputation, and interactive cross-filtering logic.

&#x20; \* \*\*Visualizations (3):\*\* 3. Segment-to-Product Sunburst Chart (Advanced), 4. Order Flow Sankey Diagram (Advanced), 8. Numerical Correlation Heatmap (Analytical).

&#x20; \* Co-implemented Random Forest Classification model and feature importance analysis.

\* \*\*Nasibe Gül Çetin:\*\*

&#x20; \* Co-designed multi-tab UI consistency, color palettes, and graph data transformations.

&#x20; \* \*\*Visualizations (3):\*\* 5. Multidimensional Parallel Coordinates Plot (Advanced), 6. Product Co-Occurrence Network Diagram (Advanced), 9. Monthly Sales \& Profit Trajectory with Range Slider (Analytical).

&#x20; \* Co-authored the one-page summary report and prepared presentation insights.



\## 🚀 Setup \& Execution Instructions

1\. Clone this repository and navigate to the project directory:

&#x20;  ```bash

&#x20;  git clone \[https://github.com/YOUR\_USERNAME/cen445-datavis-dashboard.git](https://github.com/YOUR\_USERNAME/cen445-datavis-dashboard.git)

&#x20;  cd cen445-datavis-dashboard

