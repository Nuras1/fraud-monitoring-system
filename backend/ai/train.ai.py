import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)

from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE


# =====================================================
# LOAD DATASET
# =====================================================

print("\n📂 Loading dataset...")

df = pd.read_csv("transactions.csv")

print(f"✅ Loaded {len(df)} transactions")


# =====================================================
# DATA CLEANING
# =====================================================

df = df.copy()

# remove duplicates
if "transaction_id" in df.columns:

    df = df.drop_duplicates(
        subset=["transaction_id"]
    )

# remove invalid amounts
df = df[df["amount"] > 0]

# fill missing values
df = df.fillna("unknown")

print("\n📊 Fraud distribution")

fraud_count = df["is_fraud"].sum()

print(
    f"🚨 Fraud transactions: "
    f"{fraud_count}/{len(df)}"
)



# =====================================================
# TIMESTAMP FEATURES
# =====================================================

if "timestamp" in df.columns:

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    df["hour"] = df["timestamp"].dt.hour

    df["day_of_week"] = (
        df["timestamp"].dt.dayofweek
    )

    df["is_weekend"] = (
        df["day_of_week"].isin([5, 6])
    ).astype(int)


# =====================================================
# FEATURE ENGINEERING
# =====================================================

df["country_mismatch"] = (
    df["country"]
    != df["user_registration_country"]
).astype(int)

df["suspicious_device"] = (
    df["device"] == "Unknown"
).astype(int)

df["high_amount"] = (
    df["amount"] > 3000
).astype(int)


# =====================================================
# CATEGORICAL ENCODING
# =====================================================

categorical_columns = [
    "currency",
    "country",
    "device",
    "merchant",
    "payment_method",
    "card_type",
    "transaction_type"
]

encoders = {}

for col in categorical_columns:

    le = LabelEncoder()

    df[col] = le.fit_transform(
        df[col].astype(str)
    )

    encoders[col] = le


# =====================================================
# FEATURE SELECTION
# =====================================================

features = [

    "amount",

    "currency",
    "country",
    "device",

    "payment_method",

    "user_age",

    "card_type",
    "transaction_type",

    "hour",
    "day_of_week",
    "is_weekend",

    "country_mismatch",
    "suspicious_device",
    "high_amount"
]

X = df[features]

y = df["is_fraud"]


# =====================================================
# TRAIN / TEST SPLIT
# =====================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# =====================================================
# SMOTE ONLY ON TRAIN SET
# =====================================================

print("\n⚖ Balancing classes with SMOTE...")

smote = SMOTE(random_state=42)

X_train_resampled, y_train_resampled = (
    smote.fit_resample(
        X_train,
        y_train
    )
)


# =====================================================
# MODEL
# =====================================================

print("\n🧠 Training XGBoost model...")

model = XGBClassifier(
    n_estimators=150,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    eval_metric="logloss"
)

model.fit(
    X_train_resampled,
    y_train_resampled
)


# =====================================================
# PREDICTIONS
# =====================================================

predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)[:, 1]

# =====================================================
# METRICS
# =====================================================

accuracy = accuracy_score(
    y_test,
    predictions
)

precision = precision_score(
    y_test,
    predictions,
    zero_division=0
)

recall = recall_score(
    y_test,
    predictions,
    zero_division=0
)

f1 = f1_score(
    y_test,
    predictions,
    zero_division=0
)
roc_auc = roc_auc_score(
    y_test,
    probabilities
)
print("\n📊 MODEL PERFORMANCE")

print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1 Score : {f1:.4f}")
print(f"ROC-AUC  : {roc_auc:.4f}")

print("\n📄 Classification Report")

print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)


# =====================================================
# FEATURE IMPORTANCE
# =====================================================

importance_df = pd.DataFrame({
    "feature": features,
    "importance": model.feature_importances_
})

importance_df = importance_df.sort_values(
    "importance",
    ascending=False
)

print("\n🔥 TOP FEATURE IMPORTANCE")

print(importance_df.head(10))


# =====================================================
# SAVE MODEL
# =====================================================

joblib.dump(
    model,
    "fraud_model.pkl"
)

joblib.dump(
    encoders,
    "encoders.pkl"
)

joblib.dump(
    features,
    "features.pkl"
)

print("\n✅ Model saved successfully")