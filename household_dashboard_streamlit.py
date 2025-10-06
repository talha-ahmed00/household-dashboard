import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import json
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

# ---------------------------
# Helpers
# ---------------------------
st.sidebar.image("GE Logo.png", width=200)
def tidy_percent(val):
    if hasattr(val, "iloc"):
        val = float(val.iloc[0]) if not val.empty else 0
    try:
        return f"{float(val):.2f}%"
    except Exception:
        return "0.00%"

def value_mode(df):
    """
    Return the row (as a dict) with the highest Count value.
    Used to identify the most common category.
    """
    if "Count" not in df.columns or df["Count"].isna().all():
        return {"Label": "N/A", "Percent": 0}
    top_row = df.loc[df["Count"].idxmax()]
    return {"Label": top_row.get("Label", "N/A"), "Percent": top_row.get("Percent", 0)}


def median_bucket(df):
    """
    Approximate median category by cumulative Count.
    Returns the Label whose cumulative share crosses 50%.
    """
    if "Count" not in df.columns or df["Count"].isna().all():
        return "N/A"
    df_sorted = df.copy()
    df_sorted["cum_share"] = df_sorted["Count"].cumsum() / df_sorted["Count"].sum()
    med_row = df_sorted.loc[df_sorted["cum_share"] >= 0.5].iloc[0]
    return med_row.get("Label", "N/A")
# --- Google Sheets helpers (optional) ---
# This app will automatically use a Google Sheet if Streamlit secrets are
# configured. Otherwise it falls back to the built-in sample data.
#
# Configure Streamlit Cloud (or local .streamlit/secrets.toml):
#
# [gcp_service_account]
# type = "service_account"
# project_id = "..."
# private_key_id = "..."
# private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
# client_email = "...@...gserviceaccount.com"
# client_id = "..."
#
# [sheets]
# SHEET_ID = "<your-google-sheet-id>"
#
# Each worksheet/tab should be named exactly:
#   Household Size, Household Marital Status, Dwelling Type, Gender,
#   Presence of Children, Estimated Household Income, Networth, Age, Home Owner
# with columns like: Code | Label | Count | Percent  (Age uses Age | Count | Percent)

try:
    import gspread
    from google.oauth2.service_account import Credentials
    _GS_OK = True
except Exception:
    _GS_OK = False

@st.cache_resource(show_spinner=False)
def _get_gs_client():
    if not _GS_OK:
        raise RuntimeError("gspread not installed. Add gspread and google-auth to requirements.")
    if "gcp_service_account" not in st.secrets or "sheets" not in st.secrets or "SHEET_ID" not in st.secrets["sheets"]:
        raise RuntimeError("Google Sheets secrets not configured.")
    creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]))
    scoped = creds.with_scopes(["https://www.googleapis.com/auth/spreadsheets.readonly"])
    return gspread.authorize(scoped)

@st.cache_data(show_spinner=False)
def _read_ws(sheet_id: str, ws_name: str) -> pd.DataFrame:
    """Read a worksheet by name into a DataFrame and coerce numeric columns."""
    gc = _get_gs_client()
    sh = gc.open_by_key(sheet_id)
    ws = sh.worksheet(ws_name)
    rows = ws.get_all_records()
    df = pd.DataFrame(rows)
    # Standardize common column names
    colmap = {c: c.strip() for c in df.columns}
    df.rename(columns=colmap, inplace=True)
    # Normalize numeric columns if present
    for col in ["Count", "Percent", "Age"]:
        if col in df.columns:
            df[col] = (
                pd.to_numeric(
                    df[col]
                    .astype(str)
                    .str.replace(",", "", regex=False)
                    .str.replace("%", "", regex=False)
                    .str.strip(),
                    errors="coerce",
                )
            )
    # Drop empty rows
    df = df.dropna(how="all")
    return df
st.sidebar.header("🔄 Data Controls")

if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()
    st.experimental_rerun()

@st.cache_data(ttl=300, show_spinner=False)  # ttl = seconds
def load_data_from_google_sheets():
    sid = st.secrets["sheets"]["SHEET_ID"]
    # Read all expected tabs
    tabs = {
        "size_df": "Household Size",
        "marital_df": "Household Marital Status",
        "dwelling_df": "Dwelling Type",
        "gender_df": "Gender",
        "children_df": "Presence of Children",
        "income_df": "Estimated Household Income",
        "networth_df": "Networth",
        "age_df": "Age",
        "home_df": "Home Owner",
    }
    data = {}
    for key, ws in tabs.items():
        data[key] = _read_ws(sid, ws)
    # Coerce required dtypes and ensure expected columns
    def _ensure_cols(df, cols):
        for c in cols:
            if c not in df.columns:
                df[c] = pd.NA
        return df[cols]

    data["size_df"] = _ensure_cols(data["size_df"], ["Code", "Label", "Count", "Percent"]).copy()
    data["marital_df"] = _ensure_cols(data["marital_df"], ["Code", "Label", "Count", "Percent"]).copy()
    data["dwelling_df"] = _ensure_cols(data["dwelling_df"], ["Code", "Label", "Count", "Percent"]).copy()
    data["gender_df"] = _ensure_cols(data["gender_df"], ["Code", "Label", "Count", "Percent"]).copy()
    data["children_df"] = _ensure_cols(data["children_df"], ["Code", "Label", "Count", "Percent"]).copy()
    data["income_df"] = _ensure_cols(data["income_df"], ["Code", "Label", "Count", "Percent"]).copy()
    data["networth_df"] = _ensure_cols(data["networth_df"], ["Code", "Label", "Count", "Percent"]).copy()
    data["age_df"] = _ensure_cols(data["age_df"], ["Age", "Count", "Percent"]).copy()
    data["home_df"] = _ensure_cols(data["home_df"], ["Code", "Label", "Count", "Percent"]).copy()

    # Compute TOTAL from any table with Count
    total_candidates = []
    for k in ["size_df", "marital_df", "gender_df", "children_df", "income_df", "networth_df", "home_df"]:
        df = data[k]
        if "Count" in df.columns and df["Count"].notna().any():
            total_candidates.append(df["Count"].sum())
    TOTAL = int(max(total_candidates)) if total_candidates else 0

    # Age unknown (if present as a separate row). If none, set 0.
    age_unknown_df = pd.DataFrame([{"Age": "Unknown", "Count": 0, "Percent": 0.0}])

    return (
        TOTAL,
        data["size_df"],
        data["marital_df"],
        data["dwelling_df"],
        data["gender_df"],
        data["children_df"],
        data["income_df"],
        data["networth_df"],
        data["age_df"],
        age_unknown_df,
        data["home_df"],
    )

# ---------------------------
# Load
# ---------------------------
# Try Google Sheets first; fall back to built-in sample data
try:
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
        home_df,
    ) = load_data_from_google_sheets()
    st.success("Loaded data")
except Exception as e:
    st.warning(f"Google Sheets not configured or failed ({e}). Using sample data bundled in app.")
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
    # Build home_df from sample rows
    # Using home_df loaded earlier (Google Sheets or sample fallback)

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
    "home_ownership.csv": home_df,
}

selected_export = st.sidebar.selectbox("Select a table to download", list(all_tables.keys()))
if selected_export:
    csv = all_tables[selected_export].to_csv(index=False)
    st.sidebar.download_button("Download CSV", csv, file_name=selected_export, mime="text/csv")

