import joblib
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE

from backend.ai.feature_engine import preprocess


 
# PATHS
 

RF_MODEL_PATH = "backend/ai/random_forest.pkl"

XGB_MODEL_PATH = "backend/ai/xgboost.pkl"

SCALER_PATH = "backend/ai/scaler.pkl"

FEATURES_PATH = "backend/ai/features.pkl"


 
# ML CLASSIFIER
 

class MLClassifier:

    def __init__(self, feature_columns=None):

        self.feature_columns = (
            feature_columns or []
        )

        self.rf_model = None

        self.xgb_model = None

        self.scaler = StandardScaler()

         # TRAIN
     
    def train(
        self,
        X_train,
        y_train
    ):

        # =============================================
        # FEATURE SCALING
        # =============================================

        X_scaled = self.scaler.fit_transform(
            X_train
        )

        # =============================================
        # SMOTE BALANCING
        # =============================================

        smote = SMOTE(
            random_state=42,
            k_neighbors=5
        )

        X_resampled, y_resampled = (
            smote.fit_resample(
                X_scaled,
                y_train
            )
        )

        # =============================================
        # RANDOM FOREST
        # =============================================

        self.rf_model = RandomForestClassifier(

            n_estimators=200,

            max_depth=12,

            min_samples_split=10,

            class_weight="balanced",

            random_state=42,

            n_jobs=-1
        )

        self.rf_model.fit(
            X_resampled,
            y_resampled
        )

        # =============================================
        # XGBOOST
        # =============================================

        self.xgb_model = XGBClassifier(

            n_estimators=200,

            learning_rate=0.1,

            max_depth=8,

            subsample=0.8,

            colsample_bytree=0.8,

            scale_pos_weight=10,

            eval_metric="logloss",

            random_state=42
        )

        self.xgb_model.fit(
            X_resampled,
            y_resampled
        )

         # PREDICT
     
    def predict(
        self,
        transaction_features
    ):
        X = pd.DataFrame(
            [transaction_features],
            columns=self.feature_columns
        )

        X = self.scaler.transform(X)

        rf_prob = (
            self.rf_model
            .predict_proba(X)[0, 1]
        )

        xgb_prob = (
            self.xgb_model
            .predict_proba(X)[0, 1]
        )

        ensemble_prob = (
            0.5 * rf_prob
            +
            0.5 * xgb_prob
        )

        return ensemble_prob, {

            "rf": round(
                float(rf_prob),
                3
            ),

            "xgb": round(
                float(xgb_prob),
                3
            )
        }

         # FEATURE IMPORTANCE
     
    def get_feature_importance(self):

        return dict(

            zip(

                self.feature_columns,

                self.xgb_model.feature_importances_
            )
        )


 
# GLOBAL MODEL CACHE
 

_classifier = None


 
# TRAIN MODEL
 

def train_model(df):

    global _classifier

    print("\n🧠 Training ML ensemble...")

    df = df.copy()

         # FEATURE ENGINEERING
     
    df = preprocess(
        df,
        training=True
    )

         # TARGET
     
    y = df["is_fraud"]

    X = df.drop(

        columns=[
            "is_fraud",
            "transaction_id"
        ],

        errors="ignore"
    )

    feature_columns = X.columns.tolist()

         # TRAIN TEST SPLIT
     
    X_train, X_test, y_train, y_test = (
        train_test_split(

            X,
            y,

            test_size=0.2,

            random_state=42,

            stratify=y
        )
    )

         # CREATE CLASSIFIER
     
    classifier = MLClassifier(
        feature_columns
    )

    classifier.train(
        X_train,
        y_train
    )

         # EVALUATION
     
    X_test_scaled = (
        classifier.scaler.transform(
            X_test
        )
    )

    rf_probs = (
        classifier.rf_model
        .predict_proba(X_test_scaled)[:, 1]
    )

    xgb_probs = (
        classifier.xgb_model
        .predict_proba(X_test_scaled)[:, 1]
    )

    ensemble_probs = (
        0.5 * rf_probs
        +
        0.5 * xgb_probs
    )

    predictions = (
        ensemble_probs >= 0.5
    ).astype(int)

         # METRICS
     
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

    print("\n📊 MODEL PERFORMANCE")

    print(f"Accuracy : {accuracy:.4f}")

    print(f"Precision: {precision:.4f}")

    print(f"Recall   : {recall:.4f}")

    print(f"F1 Score : {f1:.4f}")

    print("\n📄 Classification Report")

    print(

        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

         # FEATURE IMPORTANCE
     
    importance = (
        classifier.get_feature_importance()
    )

    importance_df = pd.DataFrame({

        "feature": importance.keys(),

        "importance": importance.values()
    })

    importance_df = importance_df.sort_values(
        "importance",
        ascending=False
    )

    print("\n🔥 TOP FEATURES")

    print(
        importance_df.head(10)
    )

         # SAVE MODELS
     
    joblib.dump(
        classifier.rf_model,
        RF_MODEL_PATH
    )

    joblib.dump(
        classifier.xgb_model,
        XGB_MODEL_PATH
    )

    joblib.dump(
        classifier.scaler,
        SCALER_PATH
    )

    joblib.dump(
        feature_columns,
        FEATURES_PATH
    )
    from backend.ai.feature_engine import encoders

    joblib.dump(
        encoders,
        "encoders.pkl"
    )

    _classifier = classifier

    print(
        "\n✅ Ensemble model trained and saved"
    )


 
# LOAD MODELS
 

def load_models():

    global _classifier

    if _classifier is not None:
        return _classifier

    classifier = MLClassifier()

    classifier.rf_model = joblib.load(
        RF_MODEL_PATH
    )

    classifier.xgb_model = joblib.load(
        XGB_MODEL_PATH
    )

    classifier.scaler = joblib.load(
        SCALER_PATH
    )

    classifier.feature_columns = joblib.load(
        FEATURES_PATH
    )

    _classifier = classifier
    print("FEATURES:", classifier.feature_columns)
    return classifier


 
# PREPROCESS TRANSACTION
 

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


 
# PREDICT FRAUD
 

def predict(transaction_dict):

    try:

        classifier = load_models()

        features = preprocess_transaction(

            transaction_dict,

            classifier.feature_columns
        )

        ensemble_prob, model_probs = (
            classifier.predict(
                features
            )
        )

        print(
            f"[ML] "
            f"RF={model_probs['rf']:.2f} "
            f"XGB={model_probs['xgb']:.2f} "
            f"FINAL={ensemble_prob:.2f}"
        )

        return round(
            float(ensemble_prob),
            3
        )

    except Exception as e:

        print(
            "[ML ERROR]",
            str(e)
        )

        return 0.0