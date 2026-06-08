import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from backend.user_risk_engine import calculate_user_risk
from backend.risk_engine import analyze_user

API_URL = "http://127.0.0.1:8000/transactions"

st.title("🧠 Deep User Investigation")

# =====================================================
# LOAD DATA
# =====================================================
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

    except Exception as e:

        st.error(str(e))

        return pd.DataFrame()

    except:
        return pd.DataFrame()


df = load_data()

if df.empty:

    st.warning("No transactions available")

    st.stop()

# =====================================================
# SELECTED USER
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

risk_data = calculate_user_risk(
    user_df
)

risk_score = risk_data["risk_score"]

risk_level = risk_data["status"]

fraud_ratio = risk_data["fraud_ratio"]

# =====================================================
# HEADER
# =====================================================

st.header(
    f"🧠 Deep Investigation: {selected_user}"
)

# =====================================================
# ALERTS
# =====================================================

night_tx = user_df[
    user_df["timestamp"].dt.hour.isin(
        [0, 1, 2, 3, 4]
    )
]

alerts = analyze_user(user_df)

if fraud_ratio >= 20:
    alerts.append(
        "High fraud ratio detected"
    )

if user_df["amount"].max() > 10000:
    alerts.append(
        "Very large transaction amount"
    )

if len(night_tx) > 3:
    alerts.append(
        "Night activity detected"
    )

# Показываем алерты только WATCH и SUSPICIOUS

if risk_level in ["WATCH", "SUSPICIOUS"]:

    st.subheader("🚨 Risk Alerts")

    if alerts:

        for alert in alerts:

            if risk_level == "SUSPICIOUS":
                st.error(alert)
            else:
                st.warning(alert)

    else:

        st.info(
            "No active alerts"
        )

# =====================================================
# METRICS
# =====================================================

st.subheader("📊 User Metrics")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Transactions",
    len(user_df)
)

col2.metric(
    "Fraud Count",
    risk_data["fraud_count"]
)

col3.metric(
    "Total Volume",
    f"${user_df['amount'].sum():,.2f}"
)

col4.metric(
    "User Risk",
    risk_score
)

col5.metric(
    "Fraud Ratio",
    f"{fraud_ratio}%"
)

# =====================================================
# RISK LEVEL
# =====================================================

st.subheader("⚠ User Risk Level")

st.progress(
    min(risk_score / 100, 1.0)
)

if risk_level == "SUSPICIOUS":

    st.error(
        f"🔴 Risk Status: {risk_level}"
    )

elif risk_level == "WATCH":

    st.warning(
        f"🟠 Risk Status: {risk_level}"
    )

else:

    st.success(
        f"🟢 Risk Status: {risk_level}"
    )

# =====================================================
# RISK DISTRIBUTION
# =====================================================

st.subheader("📉 Risk Distribution")

fig_risk = px.histogram(
    user_df,
    x="risk_score",
    nbins=20
)

st.plotly_chart(
    fig_risk,
    use_container_width=True
)

# =====================================================
# TIMELINE
# =====================================================

st.subheader("📈 Transaction Timeline")

timeline = (

    user_df.groupby(
        user_df["timestamp"].dt.date
    )

    .size()

    .reset_index(name="count")
)

fig_time = px.bar(
    timeline,
    x="timestamp",
    y="count"
)

st.plotly_chart(
    fig_time,
    use_container_width=True
)

# =====================================================
# COUNTRY PROFILE
# =====================================================

st.subheader("🌍 Country Activity")

geo = (

    user_df["country"]

    .value_counts()

    .reset_index()
)

geo.columns = [
    "country",
    "count"
]

fig_geo = px.bar(
    geo,
    x="country",
    y="count",
    color="count"
)

st.plotly_chart(
    fig_geo,
    use_container_width=True
)

# =====================================================
# DEVICE PROFILE
# =====================================================

st.subheader("📱 Device Activity")

device = (

    user_df["device"]

    .value_counts()

    .reset_index()
)

device.columns = [
    "device",
    "count"
]

fig_device = px.pie(
    device,
    names="device",
    values="count"
)

st.plotly_chart(
    fig_device,
    use_container_width=True
)

# =====================================================
# TRANSACTION TYPES
# =====================================================

st.subheader("💳 Transaction Types")

tx_types = (

    user_df["transaction_type"]

    .value_counts()

    .reset_index()
)

tx_types.columns = [
    "transaction_type",
    "count"
]

fig_types = px.bar(
    tx_types,
    x="transaction_type",
    y="count",
    color="count"
)

st.plotly_chart(
    fig_types,
    use_container_width=True
)

# =====================================================
# HOURLY ACTIVITY
# =====================================================

st.subheader("🕒 Hourly Activity")

hourly = (

    user_df["timestamp"]

    .dt.hour

    .value_counts()

    .sort_index()

    .reset_index()
)

hourly.columns = [
    "hour",
    "count"
]

fig_hour = px.line(
    hourly,
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

st.subheader("🚨 High Risk Operations")

high_risk_df = user_df[

    (user_df["risk_level"] == "REVIEW")

    |

    (user_df["risk_level"] == "DECLINED")
]

if not high_risk_df.empty:

    display_cols = [

        "transaction_id",
        "amount",
        "country",
        "device",
        "merchant",
        "transaction_type",
        "risk_score",
        "risk_level"
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
# BEHAVIORAL INDICATORS
# =====================================================

st.subheader("🧬 Behavioral Indicators")

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
"Unique Recipients":
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
# RECENT TRANSACTIONS
# =====================================================

st.subheader("📜 Transaction History")

st.dataframe(

    user_df.sort_values(
        "timestamp",
        ascending=False
    ),

    use_container_width=True
)

# =====================================================
# EXPORT SECTION
# =====================================================

st.subheader("📥 Export User Transactions")

csv = user_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(

    label="Download CSV",

    data=csv,

    file_name=f"{selected_user}_transactions.csv",

    mime="text/csv"
)

# =====================================================
# BACK
# =====================================================

if st.button("⬅ Back to Dashboard"):

    st.switch_page(
        "app.py"
    )