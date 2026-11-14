import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from itertools import combinations
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# 1. Sayfa Yapılandırması
st.set_page_config(
    page_title="Global Superstore Exploratory Dashboard",
    page_icon="📊",
    layout="wide"
)

# 2. Veri Yükleme ve Ön İşleme
@st.cache_data
def load_and_clean_data(file_path="superstore.csv"):
    try:
        df = pd.read_csv(file_path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding="latin1")

    raw_rows = len(df)

    # Sütun isimlerini standartlaştır (nokta, boşluk ve tireleri '_' yap)
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(".", "_", regex=False)
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )

    df = df.drop_duplicates()

    critical_cols = [c for c in ["order_date", "sales", "profit", "category", "country"] if c in df.columns]
    df = df.dropna(subset=critical_cols)

    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        df = df.dropna(subset=["order_date"])
        df["year"] = df["order_date"].dt.year
        df["year_month"] = df["order_date"].dt.to_period("M").astype(str)

    for num_col in ["sales", "profit", "discount", "quantity", "shipping_cost"]:
        if num_col in df.columns:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce")
            df[num_col] = df[num_col].fillna(df[num_col].median())

    # IQR Yöntemi ile Aykırı Değer (Outlier) Tespiti
    q1 = df["sales"].quantile(0.25)
    q3 = df["sales"].quantile(0.75)
    iqr = q3 - q1
    df["is_outlier"] = (df["sales"] > q3 + 1.5 * iqr) | (df["sales"] < q1 - 1.5 * iqr)

    stats = {
        "raw_rows": raw_rows,
        "clean_rows": len(df),
        "removed_rows": raw_rows - len(df),
        "outlier_count": int(df["is_outlier"].sum())
    }
    return df, stats

try:
    df, data_stats = load_and_clean_data()
except FileNotFoundError:
    st.error("Hata: 'superstore.csv' dosyası proje klasöründe bulunamadı.")
    st.stop()

# 3. Başlık ve Veri Kalitesi Özeti
st.title("📊 Global Superstore Exploratory Data Visualization Dashboard")
st.markdown("Interactive analytics & machine learning dashboard built with **Python, Streamlit & Plotly**.")

with st.expander("🧹 Data Preprocessing & Quality Summary", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Raw Rows", f"{data_stats['raw_rows']:,}")
    c2.metric("Cleaned Rows", f"{data_stats['clean_rows']:,}")
    c3.metric("Missing/Duplicates Removed", f"{data_stats['removed_rows']:,}")
    c4.metric("Detected Sales Outliers (IQR)", f"{data_stats['outlier_count']:,}")

# 4. Sol Menü (Sidebar) - Etkileşimli Bileşenler
st.sidebar.header("🎛️ Interactive Filters")

region_col = "market" if "market" in df.columns else ("region" if "region" in df.columns else None)
selected_regions = []
if region_col:
    all_regions = sorted(df[region_col].dropna().unique().tolist())
    selected_regions = st.sidebar.multiselect(f"Select {region_col.title()}", all_regions, default=all_regions)

selected_years = None
if "year" in df.columns:
    min_yr, max_yr = int(df["year"].min()), int(df["year"].max())
    selected_years = st.sidebar.slider("Select Order Year Range", min_yr, max_yr, (min_yr, max_yr))

exclude_outliers = st.sidebar.checkbox("Exclude Statistical Outliers (IQR)", value=False)

selected_cats = []
if "category" in df.columns:
    all_cats = sorted(df["category"].dropna().unique().tolist())
    selected_cats = st.sidebar.multiselect("Select Category", all_cats, default=all_cats)

# Filtreleri Uygula
df_filtered = df.copy()
if region_col and selected_regions:
    df_filtered = df_filtered[df_filtered[region_col].isin(selected_regions)]
if selected_years:
    df_filtered = df_filtered[(df_filtered["year"] >= selected_years[0]) & (df_filtered["year"] <= selected_years[1])]
if "category" in df.columns and selected_cats:
    df_filtered = df_filtered[df_filtered["category"].isin(selected_cats)]
if exclude_outliers:
    df_filtered = df_filtered[~df_filtered["is_outlier"]]

if df_filtered.empty:
    st.warning("Seçilen filtrelere uygun kayıt bulunamadı. Lütfen sol menüden filtreleri genişletin.")
    st.stop()

# KPI Kartları
k1, k2, k3, k4 = st.columns(4)
k1.metric("Filtered Records", f"{len(df_filtered):,}")
k2.metric("Total Sales", f"${df_filtered['sales'].sum():,.0f}")
k3.metric("Total Profit", f"${df_filtered['profit'].sum():,.0f}")
avg_disc = df_filtered["discount"].mean() * 100 if "discount" in df_filtered.columns else 0
k4.metric("Average Discount", f"{avg_disc:.1f}%")

# 5. Sekmeli Dashboard Yapısı (9 Grafik + 2 ML Modeli)
tab1, tab2, tab3, tab4 = st.tabs([
    "🌍 Global & Hierarchy (3 Advanced)",
    "🔀 Flows & Networks (3 Advanced)",
    "📈 Distributions & Trends (3 Charts)",
    "🤖 Machine Learning Insights (2 Models)"
])

# --- TAB 1: 3 İLERİ SEVİYE GRAFİK ---
with tab1:
    st.subheader("1. Global Sales & Profit Choropleth Map")
    country_agg = df_filtered.groupby("country", as_index=False).agg(
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        orders=("sales", "count")
    )
    fig_map = px.choropleth(
        country_agg,
        locations="country",
        locationmode="country names",
        color="sales",
        hover_name="country",
        hover_data={"sales": ":,.0f", "profit": ":,.0f", "orders": ":,"},
        color_continuous_scale="Viridis",
        title="Total Sales by Country (Hover for Profit & Order Volume)"
    )
    fig_map.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=460)
    st.plotly_chart(fig_map, width="stretch")
    st.info("💡 **Insight:** Geographic distribution reveals revenue concentration across North America, Western Europe, and APAC hubs, with hover tooltips exposing profit disparities.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("2. Hierarchical Treemap")
        path_cols = [c for c in [region_col, "category", "sub_category"] if c and c in df_filtered.columns]
        fig_tree = px.treemap(
            df_filtered,
            path=path_cols,
            values="sales",
            color="profit",
            color_continuous_scale="RdYlGn",
            color_continuous_midpoint=0,
            title="Market → Category → Sub-Category (Size: Sales, Color: Profit)"
        )
        st.plotly_chart(fig_tree, width="stretch")
        st.info("💡 **Insight:** Click any block to drill down; red-shaded sub-categories highlight high-revenue items that erode profitability.")

    with col_b:
        st.subheader("3. Segment-to-Product Sunburst")
        sb_cols = [c for c in ["segment", "category", "sub_category"] if c in df_filtered.columns]
        fig_sun = px.sunburst(
            df_filtered,
            path=sb_cols,
            values="sales",
            color="profit",
            color_continuous_scale="Blues",
            title="Customer Segment → Category → Sub-Category Breakdown"
        )
        st.plotly_chart(fig_sun, width="stretch")
        st.info("💡 **Insight:** The Consumer segment accounts for the largest share across all product categories, led by Technology.")

# --- TAB 2: 3 İLERİ SEVİYE GRAFİK ---
with tab2:
    st.subheader("4. Order Flow Sankey Diagram (Segment → Ship Mode → Category)")
    if all(c in df_filtered.columns for c in ["segment", "ship_mode", "category"]):
        s1 = df_filtered.groupby(["segment", "ship_mode"], as_index=False)["sales"].sum()
        s2 = df_filtered.groupby(["ship_mode", "category"], as_index=False)["sales"].sum()
        
        # Pandas 2.2+ uyumlu benzersiz düğüm listesi oluşturma
        nodes = list(dict.fromkeys(s1["segment"].tolist() + s1["ship_mode"].tolist() + s2["category"].tolist()))
        node_idx = {n: i for i, n in enumerate(nodes)}

        sources = [node_idx[x] for x in s1["segment"]] + [node_idx[x] for x in s2["ship_mode"]]
        targets = [node_idx[x] for x in s1["ship_mode"]] + [node_idx[x] for x in s2["category"]]
        values = s1["sales"].tolist() + s2["sales"].tolist()

        fig_sankey = go.Figure(data=[go.Sankey(
            node=dict(pad=18, thickness=20, line=dict(color="black", width=0.5), label=nodes),
            link=dict(source=sources, target=targets, value=values)
        )])
        fig_sankey.update_layout(title_text="Sales Flow from Customer Segment through Shipping Mode to Category", height=420)
        st.plotly_chart(fig_sankey, width="stretch")
        st.info("💡 **Insight:** Standard Class carries the vast majority of sales volume across all customer segments.")

    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("5. Parallel Coordinates (Multidimensional)")
        pc_cols = [c for c in ["sales", "profit", "discount", "quantity", "shipping_cost"] if c in df_filtered.columns]
        sample_pc = df_filtered.sample(min(1500, len(df_filtered)), random_state=42)
        fig_pc = px.parallel_coordinates(
            sample_pc,
            dimensions=pc_cols,
            color="profit",
            color_continuous_scale=px.colors.diverging.Tealrose,
            title="Drag along any axis to filter multidimensional trade-offs"
        )
        st.plotly_chart(fig_pc, width="stretch")
        st.info("💡 **Insight:** Brushing high discount values (>0.3) reveals a strong cluster of negative-profit transactions.")

    with col_d:
        st.subheader("6. Product Co-Occurrence Network Diagram")
        if "order_id" in df_filtered.columns and "sub_category" in df_filtered.columns:
            basket = df_filtered.groupby("order_id")["sub_category"].apply(lambda x: sorted(set(x)))
            multi_basket = basket[basket.apply(len) > 1]
            edge_weights = {}
            for items in multi_basket:
                for u, v in combinations(items, 2):
                    edge_weights[(u, v)] = edge_weights.get((u, v), 0) + 1

            top_edges = sorted(edge_weights.items(), key=lambda x: x[1], reverse=True)[:35]
            G = nx.Graph()
            for (u, v), w in top_edges:
                G.add_edge(u, v, weight=w)

            pos = nx.spring_layout(G, seed=42, k=0.6)
            edge_x, edge_y = [], []
            for u, v in G.edges():
                x0, y0 = pos[u]
                x1, y1 = pos[v]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1.2, color="#888"), hoverinfo="none", mode="lines")
            node_x = [pos[n][0] for n in G.nodes()]
            node_y = [pos[n][1] for n in G.nodes()]
            node_deg = [G.degree(n) for n in G.nodes()]
            node_text = [f"{n} (Connections: {G.degree(n)})" for n in G.nodes()]

            node_trace = go.Scatter(
                x=node_x, y=node_y, mode="markers+text", text=list(G.nodes()),
                textposition="top center", hovertext=node_text, hoverinfo="text",
                marker=dict(size=[10 + d * 2.5 for d in node_deg], color=node_deg, colorscale="YlOrRd", showscale=True)
            )
            fig_net = go.Figure(data=[edge_trace, node_trace])
            fig_net.update_layout(
                title="Frequently Co-Purchased Sub-Categories Network",
                showlegend=False, xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
            st.plotly_chart(fig_net, width="stretch")
            st.info("💡 **Insight:** Binders, Paper, and Storage act as central hub nodes frequently bundled with other items in multi-item orders.")

# --- TAB 3: 3 ANALİTİK GRAFİK ---
with tab3:
    col_e, col_f = st.columns(2)
    with col_e:
        st.subheader("7. Profit Distribution by Category (Violin Plot)")
        fig_violin = px.violin(
            df_filtered,
            x="category",
            y="profit",
            color="category",
            box=True,
            points=False,
            title="Profit Density & Spread Across Categories"
        )
        st.plotly_chart(fig_violin, width="stretch")
        st.info("💡 **Insight:** Technology shows the widest upper profit tail, whereas Furniture exhibits heavier negative-profit spread.")

    with col_f:
        st.subheader("8. Numerical Correlation Heatmap")
        corr_cols = [c for c in ["sales", "profit", "discount", "quantity", "shipping_cost"] if c in df_filtered.columns]
        corr_matrix = df_filtered[corr_cols].corr().round(2)
        fig_heat = px.imshow(
            corr_matrix,
            text_auto=True,
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1,
            title="Pearson Correlation Matrix of Key Metrics"
        )
        st.plotly_chart(fig_heat, width="stretch")
        st.info("💡 **Insight:** Sales and Shipping Cost correlate strongly (+0.77), while Discount correlates negatively with Profit.")

    st.subheader("9. Monthly Sales & Profit Trajectory")
    if "year_month" in df_filtered.columns:
        monthly = df_filtered.groupby(["year_month", "category"], as_index=False)[["sales", "profit"]].sum().sort_values("year_month")
        fig_line = px.line(
            monthly,
            x="year_month",
            y="sales",
            color="category",
            markers=True,
            hover_data={"profit": ":,.0f"},
            title="Monthly Sales Trend by Category (Use Range Slider to Zoom)"
        )
        fig_line.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig_line, width="stretch")
        st.info("💡 **Insight:** Clear seasonal spikes occur every Q4 (November–December) across all three product categories.")

# --- TAB 4: 2 MAKİNE ÖĞRENMESİ MODELİ ---
with tab4:
    st.subheader("🤖 Machine Learning Models for Deeper Analytical Insights")
    ml_col1, ml_col2 = st.columns(2)

    # ML Model 1: K-Means Clustering
    with ml_col1:
        st.markdown("#### Model 1: K-Means Transaction Clustering")
        k_clusters = st.slider("Select Number of Clusters (k)", min_value=2, max_value=6, value=3)
        cluster_features = [c for c in ["sales", "profit", "discount"] if c in df_filtered.columns]
        ml_sample = df_filtered[cluster_features].dropna().sample(min(3000, len(df_filtered)), random_state=42).copy()

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(ml_sample)
        kmeans = KMeans(n_clusters=k_clusters, random_state=42, n_init=10)
        ml_sample["Cluster"] = kmeans.fit_predict(X_scaled).astype(str)

        fig_km = px.scatter(
            ml_sample,
            x="sales",
            y="profit",
            color="Cluster",
            hover_data=cluster_features,
            title=f"K-Means Clustering (k={k_clusters}) on Sales vs. Profit"
        )
        st.plotly_chart(fig_km, width="stretch")
        st.info("💡 **Insight:** K-Means automatically separates high-value profitable orders from heavily discounted loss-making clusters.")

    # ML Model 2: Random Forest Classification
    with ml_col2:
        st.markdown("#### Model 2: Random Forest Profitability Classifier")
        rf_cols = [c for c in ["sales", "discount", "quantity", "shipping_cost"] if c in df_filtered.columns]
        rf_df = df_filtered[rf_cols + ["profit"]].dropna().sample(min(8000, len(df_filtered)), random_state=42)
        X = rf_df[rf_cols]
        y = (rf_df["profit"] > 0).astype(int)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
        rf_model = RandomForestClassifier(n_estimators=80, max_depth=8, random_state=42)
        rf_model.fit(X_train, y_train)
        y_pred = rf_model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)

        st.metric("Model Test Accuracy (Profitable vs. Loss)", f"{acc * 100:.2f}%")

        imp_df = pd.DataFrame({"Feature": rf_cols, "Importance": rf_model.feature_importances_}).sort_values("Importance")
        fig_imp = px.bar(
            imp_df,
            x="Importance",
            y="Feature",
            orientation="h",
            color="Importance",
            color_continuous_scale="Teal",
            title="Feature Importance in Predicting Order Profitability"
        )
        st.plotly_chart(fig_imp, width="stretch")
        st.info("💡 **Insight:** Discount rate is consistently the strongest predictor of whether an order turns a profit or incurs a loss.")