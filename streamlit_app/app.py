import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)

from backend.user_risk_engine import calculate_user_risk

API_URL = "http://127.0.0.1:8000/transactions"

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Fraud Monitoring Dashboard",
    layout="wide"
)

st.title("💳 Fraud Monitoring Dashboard")

# =====================================================
# LOAD DATA
# =====================================================

@st.cache_data(ttl=10, show_spinner=False)
def load_data():

    try:

        response = requests.get(
            API_URL,
            timeout=5
        )

        if response.status_code != 200:
            return pd.DataFrame()

        df = pd.DataFrame(
            response.json()
        )

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(
                df["timestamp"],
                format="mixed",
                errors="coerce"
            )

        return df

    except:
        return pd.DataFrame()


df = load_data()

if df.empty:

    st.warning("No transactions available")

    st.stop()

# =====================================================
# GLOBAL METRICS
# =====================================================

total_transactions = len(df)

approved_count = len(
    df[df["risk_level"] == "APPROVED"]
)

review_count = len(
    df[df["risk_level"] == "REVIEW"]
)

declined_count = len(
    df[df["risk_level"] == "DECLINED"]
)

avg_risk_score = round(
    df["risk_score"].mean() * 100,
    2
)

total_volume = round(
    df["amount"].sum(),
    2
)

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Transactions",
    total_transactions
)

col2.metric(
    "Approved",
    approved_count
)

col3.metric(
    "Review",
    review_count
)

col4.metric(
    "Declined",
    declined_count
)

col5.metric(
    "Volume",
    f"${total_volume:,.0f}"
)

st.divider()

# =====================================================
# USER ANALYTICS
# =====================================================

users = []

for user_id in df["user_id"].unique():

    user_df = df[
        df["user_id"] == user_id
    ]

    risk_data = calculate_user_risk(
        user_df
    )
    tx_count = len(user_df)

    if tx_count < 10:
        profile_status = "LEARNING"
    else:
        profile_status = "ESTABLISHED"

    users.append({

        "user_id": user_id,

        "transactions": len(user_df),

        "total_volume": round(
            user_df["amount"].sum(),
            2
        ),
        "profile_status": profile_status,

        "avg_risk": risk_data["avg_risk"],

        "fraud_count": risk_data["fraud_count"],

        "fraud_ratio": risk_data["fraud_ratio"],

        "user_risk": risk_data["risk_score"],

        "status": risk_data["status"]
    })

user_stats = pd.DataFrame(users)

# =====================================================
# USER MONITORING
# =====================================================

st.subheader("👥 User Monitoring")

col_left, col_right = st.columns(2)

# =====================================================
# NORMAL USERS
# =====================================================

with col_left:

    st.markdown("### 🟢 Normal Users")

    normal_users = user_stats[
        user_stats["status"] == "NORMAL"
        ]

    st.dataframe(

        normal_users[[
    "user_id",
    "profile_status",
    "transactions",
    "total_volume",
    "avg_risk"
]]

        .sort_values(
            "transactions",
            ascending=False
        ),

        use_container_width=True
    )

# =====================================================
# SUSPICIOUS USERS
# =====================================================

with col_right:
    st.markdown("### 🟠 Watch & Suspicious Users")

    suspicious_users = user_stats[
        user_stats["status"].isin(
            ["WATCH", "SUSPICIOUS"]
        )
    ]

    st.dataframe(

        suspicious_users[[

            "user_id",

            "profile_status",

            "transactions",

            "fraud_count",

            "fraud_ratio",

            "user_risk",

            "total_volume",

            "status"

        ]]

        .sort_values(
            "user_risk",
            ascending=False
        ),

        use_container_width=True
    )

st.divider()
# =====================================================
# INVESTIGATION
# =====================================================

st.subheader("🔎 Investigate User")

selected_user = st.selectbox(
    "Select user",
    sorted(df["user_id"].unique())
)

if st.button("Open User Profile"):

    st.session_state[
        "selected_user"
    ] = selected_user

    st.switch_page(
        "pages/1_User_Overview.py"
    )
# =====================================================
# FRAUD VS NORMAL
# =====================================================

st.subheader("📊 Fraud vs Normal Distribution")

approved_count = len(
    df[df["risk_level"] == "APPROVED"]
)

review_count = len(
    df[df["risk_level"] == "REVIEW"]
)

declined_count = len(
    df[df["risk_level"] == "DECLINED"]
)

fraud_dist = pd.DataFrame({

    "type": [
        "Approved",
        "Review",
        "Declined"
    ],

    "count": [
        approved_count,
        review_count,
        declined_count
    ]
})

fig_pie = px.pie(
    fraud_dist,
    names="type",
    values="count",
    hole=0.4
)

st.plotly_chart(
    fig_pie,
    use_container_width=True
)

# =====================================================
# TRANSACTION TIMELINE
# =====================================================

st.subheader("📈 Transaction Timeline")

timeline = (

    df.groupby(
        df["timestamp"].dt.date
    )

    .size()

    .reset_index(name="count")
)

fig_timeline = px.line(
    timeline,
    x="timestamp",
    y="count"
)

st.plotly_chart(
    fig_timeline,
    use_container_width=True
)

# =====================================================
# FRAUD BY COUNTRY
# =====================================================

st.subheader("🌍 Countries Involved In Fraud Transactions")

fraud_by_country = (

    df[df["is_fraud"] == True]

    .groupby("country")

    .size()

    .reset_index(name="fraud_count")

    .sort_values(
        "fraud_count",
        ascending=False
    )
)

if not fraud_by_country.empty:

    fig_country = px.bar(
        fraud_by_country,
        x="country",
        y="fraud_count",
        color="fraud_count"
    )

    st.plotly_chart(
        fig_country,
        use_container_width=True
    )

else:

    st.info("No fraud transactions detected yet")

# =====================================================
# COUNTRY DISTRIBUTION
# =====================================================

st.subheader("🌐 Transactions by Country")

country_stats = (

    df.groupby("country")

    .size()

    .reset_index(name="count")

    .sort_values(
        "count",
        ascending=False
    )
)

fig_country_all = px.bar(
    country_stats,
    x="country",
    y="count"
)

st.plotly_chart(
    fig_country_all,
    use_container_width=True
)

st.subheader(
    "🌍 Top Recipient Countries"
)

recipient_country_stats = (

    df["recipient_country"]

    .value_counts()

    .head(10)

    .reset_index()
)

recipient_country_stats.columns = [
    "country",
    "count"
]

fig_recipients = px.bar(
    recipient_country_stats,
    x="country",
    y="count",
    color="count"
)

st.plotly_chart(
    fig_recipients,
    use_container_width=True
)

# =====================================================
# DEVICE DISTRIBUTION
# =====================================================

st.subheader("📱 Device Activity")

device_stats = (

    df.groupby("device")

    .size()

    .reset_index(name="count")
)

fig_device = px.pie(
    device_stats,
    names="device",
    values="count"
)

st.plotly_chart(
    fig_device,
    use_container_width=True
)

# =====================================================
# TRANSACTION TYPE
# =====================================================

st.subheader("💸 Transaction Types")

tx_type_stats = (

    df.groupby("transaction_type")

    .size()

    .reset_index(name="count")
)

fig_tx_type = px.bar(
    tx_type_stats,
    x="transaction_type",
    y="count",
    color="count"
)

st.plotly_chart(
    fig_tx_type,
    use_container_width=True
)

# =====================================================
# RISK DISTRIBUTION
# =====================================================

st.subheader("⚠ Risk Score Distribution")

st.subheader(
    "👥 User Risk Distribution"
)

fig_user_risk = px.histogram(
    user_stats,
    x="user_risk",
    nbins=20
)

st.plotly_chart(
    fig_user_risk,
    use_container_width=True
)
fig_risk = px.histogram(
    df,
    x="risk_score",
    nbins=20
)

st.plotly_chart(
    fig_risk,
    use_container_width=True
)

# =====================================================
# HIGH RISK TRANSACTIONS
# =====================================================

st.subheader("🚨 High Risk Transactions")

high_risk_df = df[
    df["risk_level"].isin(
        ["REVIEW", "DECLINED"]
    )
]

if not high_risk_df.empty:

    display_cols = [

        "transaction_id",
        "user_id",
        "amount",
        "country",
        "device",
        "risk_score",
        "risk_level"
    ]

    # add optional column
    if "fraud_reasons" in high_risk_df.columns:
        display_cols.append(
            "fraud_reasons"
        )

    st.dataframe(

        high_risk_df[display_cols]

        .sort_values(
            "risk_score",
            ascending=False
        ),

        use_container_width=True
    )

else:

    st.info(
        "No high-risk transactions detected"
    )

# =====================================================
# ALL TRANSACTIONS
# =====================================================

st.subheader("📋 All Transactions")

st.dataframe(

    df.sort_values(
        "timestamp",
        ascending=False
    ),

    use_container_width=True
)

st.divider()

