import streamlit as st
import pandas as pd
import os
import requests
import plotly.express as px
import plotly.graph_objects as go

#from backend.user_risk_engine import calculate_user_risk

API_URL = "https://fraud-monitoring-api.onrender.com/transactions"

st.title("👤 User Profile Overview")

# =====================================================
# LOAD DATA
# =====================================================

@st.cache_data
def load_data():

    project_root = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            ".."
        )
    )

    csv_path = os.path.join(
        project_root,
        "transactions.csv"
    )

    df = pd.read_csv(csv_path)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )

    return df
df = load_data()

df["risk_score"] = df["is_fraud"].apply(
    lambda x: 90 if float(x) == 1 else 20
)

df["risk_level"] = df["is_fraud"].apply(
    lambda x: "DECLINED" if float(x) == 1 else "APPROVED"
)

if df.empty:

    st.warning("No data available")

    st.stop()

# =====================================================
# SELECT USER
# =====================================================

if "selected_user" not in st.session_state:

    st.error("No user selected")

    st.stop()

selected_user = st.session_state[
    "selected_user"
]

user_df = df[
    df["user_id"] == selected_user
]

if user_df.empty:

    st.warning("User not found")

    st.stop()

# =====================================================
# USER RISK
# =====================================================

fraud_count = int(user_df["is_fraud"].sum())

fraud_ratio = round(
    user_df["is_fraud"].mean() * 100,
    2
)

risk_score = round(
    (fraud_ratio * 0.8)
    + min(fraud_count * 10, 20),
    2
)

if fraud_count >= 2:
    risk_level = "SUSPICIOUS"
elif fraud_count >= 1:
    risk_level = "WATCH"
else:
    risk_level = "NORMAL"

# =====================================================
# PROFILE STATUS
# =====================================================

tx_count = len(user_df)

if tx_count == 0:
    profile_status = "NEW"

elif tx_count < 10:
    profile_status = "LEARNING"

else:
    profile_status = "ESTABLISHED"

# =====================================================
# HEADER
# =====================================================

st.header(
    f"🧠 User Investigation: {selected_user}"
)

# =====================================================
# RISK ALERTS
# =====================================================

st.subheader("🚨 Risk Alerts")

if risk_level == "NORMAL":

    st.success(
        "No significant anomalies detected"
    )

elif risk_level == "WATCH":

    st.warning(
        "User requires additional monitoring"
    )

else:

    st.error(
        "Multiple fraud indicators detected"
    )

alerts = []

if fraud_ratio >= 20:
    alerts.append(
        "High fraud ratio detected"
    )

if user_df["amount"].max() > 10000:
    alerts.append(
        "Very large transaction amount"
    )

if user_df["country"].nunique() >= 3:
    alerts.append(
        "Multiple countries detected"
    )

if user_df["device"].nunique() >= 4:
    alerts.append(
        "Multiple devices detected"
    )

night_tx = user_df[
    user_df["timestamp"].dt.hour.isin(
        [0,1,2,3,4]
    )
]

if len(night_tx) > 3:
    alerts.append(
        "Night activity detected"
    )

if alerts:

    for alert in alerts:

        if risk_level == "WATCH":
            st.warning(alert)
        else:
            st.error(alert)

# =====================================================
# METRICS
# =====================================================

total = len(user_df)

fraud = fraud_count
volume = round(
    user_df["amount"].sum(),
    2
)

avg_risk = risk_score / 100

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Transactions",
    total
)

col2.metric(
    "Fraud Count",
    fraud
)

col3.metric(
    "Total Volume",
    f"${volume:,.2f}"
)

col4.metric(
    "Avg Risk",
    f"{avg_risk*100:.1f}%"
)

st.info(
    f"Profile Status: {profile_status}"
)
# =====================================================
# RISK SCORE
# =====================================================

st.subheader("⚠ Risk Score")

st.progress(
    min(risk_score / 100, 1.0)
)

if risk_level == "SUSPICIOUS":

    level_icon = "🔴"

elif risk_level == "WATCH":

    level_icon = "🟠"

else:

    level_icon = "🟢"

st.write(
    f"User Risk Score: "
    f"{risk_score}/100"
)

st.write(
    f"{level_icon} User Status: "
    f"{risk_level}"
)

st.write(
    f"Fraud Ratio: {fraud_ratio}%"
)


# =====================================================
# TRANSACTION TIMELINE
# =====================================================

if tx_count >= 10:

    st.subheader("📈 Transaction Timeline")

    timeline = (

        user_df.groupby(
            user_df["timestamp"].dt.date
        )

        .size()

        .reset_index(name="count")
    )

    fig_timeline = px.line(
        timeline,
        x="timestamp",
        y="count",
        markers=True
    )

    st.plotly_chart(
        fig_timeline,
        use_container_width=True
    )

else:

    st.info(
        "Profile is still learning. Not enough transaction history for timeline analysis."
    )

# =====================================================
# RECIPIENTS
# =====================================================

if "recipient_id" in user_df.columns:

    st.subheader(
        "👤 Top Recipients"
    )

    recipient_df = (

        user_df["recipient_id"]

        .value_counts()

        .head(10)

        .reset_index()
    )

    recipient_df.columns = [
        "recipient_id",
        "count"
    ]

    fig_recipients = px.bar(
        recipient_df,
        x="recipient_id",
        y="count"
    )

    st.plotly_chart(
        fig_recipients,
        use_container_width=True
    )

# =====================================================
# DEVICE PROFILE
# =====================================================

st.subheader("📱 Device Activity")

device_df = (

    user_df["device"]

    .value_counts()

    .reset_index()
)

device_df.columns = [
    "device",
    "count"
]

fig_device = px.pie(
    device_df,
    names="device",
    values="count"
)

st.plotly_chart(
    fig_device,
    use_container_width=True
)

# =====================================================
# COUNTRY PROFILE
# =====================================================

st.subheader("🌍 Country Activity")

country_df = (

    user_df["country"]

    .value_counts()

    .reset_index()
)

country_df.columns = [
    "country",
    "count"
]

fig_country = px.bar(
    country_df,
    x="country",
    y="count"
)

st.plotly_chart(
    fig_country,
    use_container_width=True
)

# =====================================================
# TRANSACTION TYPES
# =====================================================

st.subheader("💳 Transaction Types")

tx_type_df = (

    user_df["transaction_type"]

    .value_counts()

    .reset_index()
)

tx_type_df.columns = [
    "transaction_type",
    "count"
]

fig_tx_type = px.bar(
    tx_type_df,
    x="transaction_type",
    y="count",
    color="count"
)

st.plotly_chart(
    fig_tx_type,
    use_container_width=True
)

# =====================================================
# HOUR ANALYSIS
# =====================================================

st.subheader("🕒 Hourly Activity")

hour_df = (

    user_df["timestamp"]

    .dt.hour

    .value_counts()

    .sort_index()

    .reset_index()
)

hour_df.columns = [
    "hour",
    "count"
]

fig_hour = px.line(
    hour_df,
    x="hour",
    y="count"
)

st.plotly_chart(
    fig_hour,
    use_container_width=True
)


# =====================================================
# HIGH RISK OPERATIONS
# =====================================================

# =====================================================
# HIGH RISK OPERATIONS
# =====================================================

if risk_level in ["WATCH", "SUSPICIOUS"]:

    st.subheader("🚨 High Risk Operations")

    high_risk_df = user_df[
        user_df["is_fraud"] == True
        ]

    if not high_risk_df.empty:

        display_cols = [

            "transaction_id",
            "amount",
            "country",
            "device",
            "merchant",
            "transaction_type"
        ]

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
# RECENT TRANSACTIONS
# =====================================================

st.subheader("📋 Transaction History")

st.dataframe(

    user_df.sort_values(
        "timestamp",
        ascending=False
    ),

    use_container_width=True
)

# =====================================================
# RAW USER FEATURES
# =====================================================

st.subheader("🧬 User Behavioral Indicators")

profile_data = {

    "Unique Countries":
        user_df["country"].nunique(),

    "Unique Devices":
        user_df["device"].nunique(),

    "Unique Merchants":
        user_df["merchant"].nunique(),

    "Average Amount":
        round(
            user_df["amount"].mean(),
            2
        ),

    "Maximum Amount":
        round(
            user_df["amount"].max(),
            2
        ),
"Known Recipients":
    user_df["recipient_id"].nunique(),

"Cross Border Transfers":
    (
        user_df["country"]
        != user_df["recipient_country"]
    ).sum(),

"Non Resident Recipients":
    (
        user_df["recipient_is_resident"]
        == False
    ).sum(),
    "Night Transactions":
        len(night_tx)

}

profile_df = pd.DataFrame({

    "Indicator":
        list(profile_data.keys()),

    "Value":
        list(profile_data.values())
})

st.dataframe(
    profile_df,
    use_container_width=True
)

# =====================================================
# DEEP INVESTIGATION
# =====================================================

if st.button("🧠 Open Deep Investigation"):

    st.switch_page(
        "pages/2_User_Investigation.py"
    )