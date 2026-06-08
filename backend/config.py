from dotenv import load_dotenv
import os

# =====================================================
# LOAD ENVIRONMENT VARIABLES
# =====================================================

load_dotenv()

# =====================================================
# DATABASE CONFIGURATION
# =====================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./fraud_monitoring.db"
)

# =====================================================
# API CONFIGURATION
# =====================================================

API_HOST = os.getenv(
    "API_HOST",
    "127.0.0.1"
)

API_PORT = int(
    os.getenv(
        "API_PORT",
        8000
    )
)

# =====================================================
# AI / FRAUD SETTINGS
# =====================================================

FRAUD_THRESHOLD = float(
    os.getenv(
        "FRAUD_THRESHOLD",
        0.65
    )
)

BLOCK_THRESHOLD = float(
    os.getenv(
        "BLOCK_THRESHOLD",
        0.85
    )
)

# =====================================================
# MODEL PATHS
# =====================================================

ML_MODEL_PATH = os.getenv(
    "ML_MODEL_PATH",
    "backend/ai/fraud_model.pkl"
)

ANOMALY_MODEL_PATH = os.getenv(
    "ANOMALY_MODEL_PATH",
    "backend/ai/anomaly_model.pkl"
)

# =====================================================
# SECURITY SETTINGS
# =====================================================

MAX_USER_HISTORY = int(
    os.getenv(
        "MAX_USER_HISTORY",
        100
    )
)

REQUEST_TIMEOUT = int(
    os.getenv(
        "REQUEST_TIMEOUT",
        5
    )
)

# =====================================================
# DEBUG MODE
# =====================================================

DEBUG = os.getenv(
    "DEBUG",
    "False"
).lower() == "true"