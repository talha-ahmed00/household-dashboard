import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(
    page_title="Household Demographics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------
# Helpers
# ---------------------------
@st.cache_data
def load_data():
    # Household Size
    size_data = pd.DataFrame([
        {"Code": 1, "Label": "1 Person", "Count": 112702, "Percent": 26.75},
        {"Code": 2, "Label": "2 People", "Count": 94563, "Percent": 22.45},
        {"Code": 3, "Label": "3 People", "Count": 73065, "Percent": 17.34},
        {"Code": 4, "Label": "4 People", "Count": 61513, "Percent": 14.60},
        {"Code": 5, "Label": "5 People", "Count": 43247, "Percent": 10.27},
        {"Code": 6, "Label": "6 People", "Count": 22991, "Percent": 5.46},
        {"Code": 7, "Label": "7 People", "Count": 9483, "Percent": 2.25},
        {"Code": 8, "Label": "8 People", "Count": 3178, "Percent": 0.75},
        {"Code": 9, "Label": "9 or more People", "Count": 512, "Percent": 0.12},
    ])

    # Marital Status
    marital_data = pd.DataFrame([
        {"Code": "A", "Label": "Inferred Married", "Count": 1884, "Percent": 0.45},
        {"Code": "B", "Label": "Inferred Single", "Count": 444, "Percent": 0.11},
        {"Code": "M", "Label": "Married", "Count": 183131, "Percent": 43.47},
        {"Code": "S", "Label": "Single", "Count": 208958, "Percent": 49.60},
        {"Code": "U", "Label": "Unknown", "Count": 26837, "Percent": 6.37},
    ])

    # Dwelling Type
    dwelling_data = pd.DataFrame([
        {"Code": "S", "Label": "Single Family Dwelling Unit", "Count": 421254, "Percent": 100.00},
    ])

    # Gender
    gender_data = pd.DataFrame([
        {"Code": "F", "Label": "Female", "Count": 225964, "Percent": 53.64},
        {"Code": "M", "Label": "Male", "Count": 195290, "Percent": 46.36},
    ])

    # Presence of Children
    children_data = pd.DataFrame([
        {"Code": "Y", "Label": "Yes", "Count": 182598, "Percent": 43.35},
        {"Code": "U", "Label": "Unknown", "Count": 238656, "Percent": 56.65},
    ])

    # Estimated Household Income
    income_rows = [
        ("A", "Under $10,000", 8355, 1.98),
        ("B", "$10,000 - $14,999", 22648, 5.38),
        ("C", "$15,000 - $19,999", 11623, 2.76),
        ("D", "$20,000 - $24,999", 7403, 1.76),
        ("E", "$25,000 - $29,999", 17893, 4.25),
        ("F", "$30,000 - $34,999", 9375, 2.23),
        ("G", "$35,000 - $39,999", 20246, 4.81),
        ("H", "$40,000 - $44,999", 11391, 2.70),
        ("I", "$45,000 - $49,999", 20876, 4.96),
        ("J", "$50,000 - $54,999", 12451, 2.96),
        ("K", "$55,000 - $59,999", 17267, 4.10),
        ("L", "$60,000 - $64,999", 18289, 4.34),
        ("M", "$65,000 - $74,999", 28233, 6.70),
        ("N", "$75,000 - $99,999", 69929, 16.60),
        ("O", "$100,000 - $149,999", 84627, 20.09),
        ("P", "$150,000 - $174,999", 10646, 2.53),
        ("Q", "$175,000 - $199,999", 15531, 3.69),
        ("R", "$200,000 - $249,999", 14741, 3.50),
        ("S", "$250,000+", 19730, 4.68),
    ]
    income_data = pd.DataFrame(income_rows, columns=["Code", "Label", "Count", "Percent"])
    # Ensure category order
    income_data["Label"] = pd.Categorical(income_data["Label"], categories=[r[1] for r in income_rows], ordered=True)

    # Net Worth
    networth_rows = [
        ("A", "Least wealthy", 76659, 18.20),
        ("B", "Tier 2", 27793, 6.60),
        ("C", "Tier 3", 7547, 1.79),
        ("D", "Tier 4", 21996, 5.22),
        ("E", "Tier 5", 26268, 6.24),
        ("F", "Tier 6", 39978, 9.49),
        ("G", "Tier 7", 68801, 16.33),
        ("H", "Tier 8", 59490, 14.12),
        ("I", "Most Wealthy", 75556, 17.94),
        ("U", "Unknown", 17166, 4.07),
    ]
    networth_data = pd.DataFrame(networth_rows, columns=["Code", "Label", "Count", "Percent"])
    networth_data["Label"] = pd.Categorical(networth_data["Label"], categories=[r[1] for r in networth_rows], ordered=True)

    # Age distribution
    age_rows = [
        (17, 7, 0.00), (18, 20, 0.00), (19, 152, 0.04), (20, 879, 0.21), (21, 1684, 0.40),
        (22, 1552, 0.37), (23, 2042, 0.48), (24, 1937, 0.46), (25, 2043, 0.48), (26, 2425, 0.58),
        (27, 3008, 0.71), (28, 3224, 0.77), (29, 4311, 1.02), (30, 5365, 1.27), (31, 6510, 1.55),
        (32, 5788, 1.37), (33, 6021, 1.43), (34, 6132, 1.46), (35, 5908, 1.40), (36, 5675, 1.35),
        (37, 5182, 1.23), (38, 5477, 1.30), (39, 5997, 1.42), (40, 6178, 1.47), (41, 6164, 1.46),
        (42, 6456, 1.53), (43, 6388, 1.52), (44, 6625, 1.57), (45, 6909, 1.64), (46, 6448, 1.53),
        (47, 6345, 1.51), (48, 6525, 1.55), (49, 6196, 1.47), (50, 6144, 1.46), (51, 6306, 1.50),
        (52, 6339, 1.50), (53, 6572, 1.56), (54, 7259, 1.72), (55, 7264, 1.72), (56, 6774, 1.61),
        (57, 6712, 1.59), (58, 6767, 1.61), (59, 6709, 1.59), (60, 7315, 1.74), (61, 7779, 1.85),
        (62, 7786, 1.85), (63, 7930, 1.88), (64, 8024, 1.90), (65, 8069, 1.92), (66, 8163, 1.94),
        (67, 7970, 1.89), (68, 8071, 1.92), (69, 7574, 1.80), (70, 7442, 1.77), (71, 7477, 1.77),
        (72, 7016, 1.67), (73, 6950, 1.65), (74, 6675, 1.58), (75, 6338, 1.50), (76, 6043, 1.43),
        (77, 6031, 1.43), (78, 6418, 1.52), (79, 4448, 1.06), (80, 4086, 0.97), (81, 4101, 0.97),
        (82, 4098, 0.97), (83, 3640, 0.86), (84, 3245, 0.77), (85, 2867, 0.68), (86, 2789, 0.66),
        (87, 2678, 0.64), (88, 2443, 0.58), (89, 2233, 0.53), (90, 2057, 0.49), (91, 1912, 0.45),
        (92, 1846, 0.44), (93, 1786, 0.42), (94, 1615, 0.38), (95, 1575, 0.37), (96, 1330, 0.32),
        (97, 1272, 0.30), (98, 1163, 0.28), (99, 1006, 0.24), (100, 942, 0.22), (101, 824, 0.20),
        (102, 692, 0.16), (103, 419, 0.10), (104, 35, 0.01), (105, 117, 0.03), (106, 314, 0.07),
        (107, 19, 0.00), (108, 12, 0.00), (109, 7, 0.00), (110, 9, 0.00), (111, 7, 0.00), (112, 4, 0.00),
        (113, 10, 0.00), (114, 3, 0.00),
    ] )
    age_data = pd.DataFrame(age_rows, columns=["Age", "Count", "Percent"])

    # Age Unknown and Totals
    age_unknown = pd.DataFrame([{"Age": "Unknown", "Count": 14160, "Percent": 3.36}])

    total_households = 421_254

    return (
        total_households,
        size_data,
        marital_data,
        dwelling_data,
        gender_data,
        children_data,
        income_data,
        networth_data,
        age_data,
        age_unknown,
    )


def tidy_percent(x):
    return f"{x:.2f}%"


def value_mode(df, value_col="Count"):
    row = df.loc[df[value_col].idxmax()]
    return row


def median_bucket(df, order_col="Label", count_col="Count"):
    # Assumes ordered categorical in order_col
    temp = df[[order_col, count_col]].copy()
    temp["CumCount"] = temp[count_col].cumsum()
    half = temp[count_col].sum() / 2
    median_label = temp.loc[temp["CumCount"] >= half, order_col].iloc[0]
    return median_label


# ---------------------------
# Load
# ---------------------------
(
    TOTAL,
    size_df,
    marital_df,
    dwelling_df,
    gender_df,
    children_df,
    income_df,
    networth_df,
    age_df,
    age_unknown_df,
) = load_data()

# ---------------------------
# Sidebar Controls
# ---------------------------
st.sidebar.header("Controls")
unit = st.sidebar.radio("Show values as", ["Percent", "Count"], index=0, horizontal=True)
show_unknowns = st.sidebar.checkbox("Show 'Unknown' segments where present", value=True)
smooth_age = st.sidebar.slider("Age trend smoothing (rolling window)", min_value=1, max_value=9, value=1, step=2, help="Apply a centered rolling mean to the age line.")

# ---------------------------
# Header / KPIs
# ---------------------------
st.title("📊 Household Demographics Dashboard")
st.caption("Interactive view of household size, marital status, gender, children, income, net worth, age distribution, and home ownership.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Households", f"{TOTAL:,}")
with col2:
    # % with children (from children_df; ignores Unknown)
    pct_children = children_df.loc[children_df["Code"] == "Y", "Percent"].iloc[0]
    st.metric("With Children (Yes)", tidy_percent(pct_children))
with col3:
    # Verified homeowners percent
    verified_homeowners = 320203
    st.metric("Verified Home Owners", tidy_percent(verified_homeowners / TOTAL * 100))
with col4:
    # Income mode / median bucket
    top_income = value_mode(income_df)
    med_income = median_bucket(income_df)
    st.metric("Top Income Bucket", f"{top_income['Label']} ({tidy_percent(top_income['Percent'])})")
    st.caption(f"Median income bucket ≈ {med_income}")

# Tabs
overview_tab, demo_tab, income_tab, age_tab, home_tab = st.tabs([
    "Overview",
    "Demographics",
    "Income & Net Worth",
    "Age",
    "Home Ownership",
])

# ---------------------------
# Overview
# ---------------------------
with overview_tab:
    c1, c2 = st.columns((1,1))
    # Household Size
    df = size_df.copy()
    y = "Percent" if unit == "Percent" else "Count"
    fig_size = px.bar(
        df,
        x=y,
        y="Label",
        orientation="h",
        title="Household Size Distribution",
        text=df[y].map(lambda v: f"{v:,.0f}" if y == "Count" else f"{v:.2f}%"),
    )
    fig_size.update_layout(margin=dict(t=60, r=20, l=0, b=20), yaxis_title="", xaxis_title=y)
    c1.plotly_chart(fig_size, use_container_width=True)

    # Marital Status
    df = marital_df.copy()
    if not show_unknowns:
        df = df[df["Label"] != "Unknown"]
    value_col = "Percent" if unit == "Percent" else "Count"
    fig_marital = px.pie(
        df,
        values=value_col,
        names="Label",
        title="Household Marital Status",
        hole=0.45,
    )
    c2.plotly_chart(fig_marital, use_container_width=True)

    # Gender + Children stacked bars
    c3, c4 = st.columns((1,1))

    df = gender_df.copy()
    fig_gender = px.bar(
        df,
        x="Label",
        y=value_col,
        title="Gender",
        text=df[value_col].map(lambda v: f"{v:,.0f}" if value_col == "Count" else f"{v:.2f}%"),
    )
    fig_gender.update_layout(margin=dict(t=60, r=20, l=20, b=20), xaxis_title="", yaxis_title=value_col)
    c3.plotly_chart(fig_gender, use_container_width=True)

    df = children_df.copy()
    if not show_unknowns:
        df = df[df["Label"] != "Unknown"]
    fig_children = px.bar(
        df,
        x="Label",
        y=value_col,
        title="Presence of Children",
        text=df[value_col].map(lambda v: f"{v:,.0f}" if value_col == "Count" else f"{v:.2f}%"),
    )
    fig_children.update_layout(margin=dict(t=60, r=20, l=20, b=20), xaxis_title="", yaxis_title=value_col)
    c4.plotly_chart(fig_children, use_container_width=True)

# ---------------------------
# Demographics Tab
# ---------------------------
with demo_tab:
    st.subheader("Household Size")
    df = size_df.copy()
    y = "Percent" if unit == "Percent" else "Count"
    fig = px.treemap(df, path=["Label"], values=y, title="Treemap: Household Size")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Marital Status")
    df = marital_df.copy()
    if not show_unknowns:
        df = df[df["Label"] != "Unknown"]
    fig = px.bar(df, x="Label", y=y, text=y, title="Marital Status Distribution")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Gender")
    df = gender_df.copy()
    fig = px.funnel(df, x=y, y="Label", title="Gender Share (Funnel)")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Income & Net Worth Tab
# ---------------------------
with income_tab:
    left, right = st.columns((1.3, 1))

    with left:
        st.subheader("Estimated Household Income")
        df = income_df.sort_values("Label")
        y = "Percent" if unit == "Percent" else "Count"
        fig_income = px.bar(
            df,
            x="Label",
            y=y,
            text=y,
            title="Income Distribution (Ordered)",
        )
        fig_income.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig_income, use_container_width=True)

        # Treemap variant
        fig_income_tree = px.treemap(df, path=["Label"], values=y, title="Income Treemap")
        st.plotly_chart(fig_income_tree, use_container_width=True)

    with right:
        st.subheader("Net Worth")
        df = networth_df.copy()
        if not show_unknowns:
            df = df[df["Label"] != "Unknown"]
        y = "Percent" if unit == "Percent" else "Count"
        fig_net = px.bar(df, x=y, y="Label", orientation="h", text=y, title="Net Worth Tiers")
        st.plotly_chart(fig_net, use_container_width=True)

        # Donut
        fig_net_pie = px.pie(df, values=y, names="Label", hole=0.45, title="Net Worth Share")
        st.plotly_chart(fig_net_pie, use_container_width=True)

# ---------------------------
# Age Tab
# ---------------------------
with age_tab:
    st.subheader("Age Distribution")
    df = age_df.copy().sort_values("Age")
    if smooth_age > 1:
        df["Smoothed"] = df["Percent"].rolling(window=smooth_age, center=True, min_periods=1).mean()
    value_col = "Percent" if unit == "Percent" else "Count"

    # Line chart
    fig_age = go.Figure()
    fig_age.add_trace(go.Scatter(x=df["Age"], y=df[value_col], mode="lines+markers", name=value_col))
    if smooth_age > 1 and unit == "Percent":
        fig_age.add_trace(go.Scatter(x=df["Age"], y=df["Smoothed"], mode="lines", name=f"Smoothed ({smooth_age})"))
    fig_age.update_layout(title="Age by Single Year", xaxis_title="Age", yaxis_title=value_col)
    st.plotly_chart(fig_age, use_container_width=True)

    # Highlight seniors area (65+)
    seniors = df[df["Age"] >= 65]
    if not seniors.empty:
        share = seniors[value_col].sum() / (df[value_col].sum()) * (100 if unit == "Percent" else 1)
        st.caption(f"Share ages 65+: {'{:.2f}%'.format(share) if unit=='Percent' else f'{share:,.0f}'}")

    # Unknown block
    st.info("Age 'Unknown' count: {:,} ({}).".format(int(age_unknown_df["Count"].iloc[0]), tidy_percent(age_unknown_df["Percent"].iloc[0])))

# ---------------------------
# Home Ownership Tab
# ---------------------------
with home_tab:
    st.subheader("Home Ownership")
    home_rows = [
        ("H", "Highly Likely Home Owner", 1758, 0.42),
        ("P", "Probably Home Owner", 17992, 4.27),
        ("V", "Verified Home Owner", 320203, 76.01),
        ("U", "Unknown", 81301, 19.30),
    ]
    home_df = pd.DataFrame(home_rows, columns=["Code", "Label", "Count", "Percent"])
    if not show_unknowns:
        home_df = home_df[home_df["Label"] != "Unknown"]
    y = "Percent" if unit == "Percent" else "Count"

    c1, c2 = st.columns((1,1))
    fig_home = px.bar(home_df, x=y, y="Label", orientation="h", text=y, title="Home Ownership Categories")
    c1.plotly_chart(fig_home, use_container_width=True)

    fig_home_pie = px.pie(home_df, values=y, names="Label", hole=0.45, title="Home Ownership Share")
    c2.plotly_chart(fig_home_pie, use_container_width=True)

# ---------------------------
# Data Export
# ---------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Export Data")
all_tables = {
    "household_size.csv": size_df,
    "marital_status.csv": marital_df,
    "dwelling_type.csv": dwelling_df,
    "gender.csv": gender_df,
    "presence_children.csv": children_df,
    "income.csv": income_df,
    "networth.csv": networth_df,
    "age.csv": pd.concat([age_df, age_unknown_df], ignore_index=True),
    "home_ownership.csv": pd.DataFrame([
        {"Code": "H", "Label": "Highly Likely Home Owner", "Count": 1758, "Percent": 0.42},
        {"Code": "P", "Label": "Probably Home Owner", "Count": 17992, "Percent": 4.27},
        {"Code": "V", "Label": "Verified Home Owner", "Count": 320203, "Percent": 76.01},
        {"Code": "U", "Label": "Unknown", "Count": 81301, "Percent": 19.30},
    ])
}

selected_export = st.sidebar.selectbox("Select a table to download", list(all_tables.keys()))
if selected_export:
    csv = all_tables[selected_export].to_csv(index=False)
    st.sidebar.download_button("Download CSV", csv, file_name=selected_export, mime="text/csv")

st.sidebar.markdown("""
**How to run**
1. Save this file as `household_dashboard_streamlit.py`.
2. Install dependencies: `pip install streamlit plotly pandas`.
3. Run: `streamlit run household_dashboard_streamlit.py`.
""")
