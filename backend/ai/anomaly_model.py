import joblib
import pandas as pd
import numpy as np

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from backend.ai.feature_engine import preprocess


# =====================================================
# PATHS
# =====================================================

MODEL_PATH = "backend/ai/anomaly_detector.pkl"

SCALER_PATH = "backend/ai/anomaly_scaler.pkl"

FEATURES_PATH = "backend/ai/anomaly_features.pkl"

MINMAX_PATH = "backend/ai/anomaly_minmax.pkl"


# =====================================================
# ANOMALY DETECTOR
# =====================================================

class AnomalyDetector:

    def __init__(self, contamination=0.05):

        self.contamination = contamination

        self.model = None

        self.scaler = StandardScaler()

        self.score_min = None

        self.score_max = None

    # =================================================
    # TRAIN
    # =================================================

    def train(self, X_train):

        # =============================================
        # SCALING
        # =============================================

        X_scaled = self.scaler.fit_transform(
            X_train
        )

        # =============================================
        # ISOLATION FOREST
        # =============================================

        self.model = IsolationForest(

            n_estimators=100,

            max_samples="auto",

            contamination=self.contamination,

            max_features=1.0,

            bootstrap=False,

            random_state=42,

            n_jobs=-1
        )

        self.model.fit(X_scaled)

        # =============================================
        # SCORE NORMALIZATION
        # =============================================

        raw_scores = -self.model.decision_function(
            X_scaled
        )

        self.score_min = float(
            np.min(raw_scores)
        )

        self.score_max = float(
            np.max(raw_scores)
        )

    # =================================================
    # PREDICT
    # =================================================

    def predict(
        self,
        transaction_features
    ):

        X = self.scaler.transform(
            [transaction_features]
        )

        raw_score = -self.model.decision_function(
            X
        )[0]

        is_anomaly = int(
            self.model.predict(X)[0] == -1
        )

        risk_score = self._normalize(
            raw_score
        )

        return risk_score, is_anomaly

    # =================================================
    # NORMALIZATION
    # =================================================

    def _normalize(self, score):

        if self.score_max == self.score_min:
            return 0.0

        normalized = (

            (score - self.score_min)

            /

            (self.score_max - self.score_min)
        )

        return max(
            0.0,
            min(1.0, normalized)
        )


# =====================================================
# GLOBAL CACHE
# =====================================================

_detector = None


# =====================================================
# TRAIN ANOMALY MODEL
# =====================================================

def train_anomaly(df):

    global _detector

    print("\n🧠 Training anomaly detector...")

    df = df.copy()

    # =================================================
    # FEATURE ENGINEERING
    # =================================================

    df = preprocess(
        df,
        training=True
    )

    # =============================================
    # TRAIN ONLY ON NORMAL TRANSACTIONS
    # =============================================

    normal_df = df[
        df["is_fraud"] == 0
        ]

    print(
        f"\n🟢 Normal transactions: "
        f"{len(normal_df)}"
    )

    X = normal_df.drop(

        columns=[
            "is_fraud",
            "transaction_id"
        ],

        errors="ignore"
    )

    feature_columns = X.columns.tolist()

    # =================================================
    # CREATE DETECTOR
    # =================================================

    detector = AnomalyDetector(
        contamination=0.05
    )
    print(X.dtypes)
    detector.train(X)

    # =================================================
    # SAVE ARTIFACTS
    # =================================================

    joblib.dump(
        detector.model,
        MODEL_PATH
    )

    joblib.dump(
        detector.scaler,
        SCALER_PATH
    )

    joblib.dump(
        feature_columns,
        FEATURES_PATH
    )

    joblib.dump(

        {
            "min": detector.score_min,
            "max": detector.score_max
        },

        MINMAX_PATH
    )

    _detector = detector

    print(
        "\n✅ Anomaly detector trained"
    )


# =====================================================
# LOAD DETECTOR
# =====================================================

def load_detector():

    global _detector

    if _detector is not None:
        return _detector

    detector = AnomalyDetector()

    detector.model = joblib.load(
        MODEL_PATH
    )

    detector.scaler = joblib.load(
        SCALER_PATH
    )

    minmax = joblib.load(
        MINMAX_PATH
    )

    detector.score_min = minmax["min"]

    detector.score_max = minmax["max"]

    detector.feature_columns = joblib.load(
        FEATURES_PATH
    )

    _detector = detector

    return detector


# =====================================================
# PREPROCESS TRANSACTION
# =====================================================

def preprocess_transaction(
    transaction_dict,
    feature_columns
):

    df = pd.DataFrame([
        transaction_dict
    ])

    df = preprocess(
        df,
        training=False
    )

    for col in feature_columns:

        if col not in df.columns:
            df[col] = 0

    df = df[feature_columns]

    return df.iloc[0].values


# =====================================================
# ANOMALY SCORE
# =====================================================

def anomaly_score(transaction_dict):

    try:

        detector = load_detector()

        features = preprocess_transaction(

            transaction_dict,

            detector.feature_columns
        )

        risk_score, is_anomaly = (
            detector.predict(
                features
            )
        )

        print(
            f"[ANOMALY] "
            f"SCORE={risk_score:.2f} "
            f"ANOMALY={is_anomaly}"
        )

        return round(
            float(risk_score),
            3
        )

    except Exception as e:

        print(
            "[ANOMALY ERROR]",
            str(e)
        )

        return 0.0