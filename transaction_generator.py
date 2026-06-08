import requests
import random
import time
import numpy as np
import pandas as pd
import os

from datetime import datetime, timedelta


# =====================================================
# API CONFIG
# =====================================================

API_URL = "http://127.0.0.1:8000/transactions"

HEALTHCHECK_URL = "http://127.0.0.1:8000/docs"


# =====================================================
# USER PROFILES
# =====================================================

USER_TYPES = {

    "student": {

        "avg_amount": (10, 80),

        "activity_per_day": (2, 8),

        "countries": ["KZ"],

        "devices": [
            "Android",
            "iPhone"
        ]
    },

    "worker": {

        "avg_amount": (50, 400),

        "activity_per_day": (5, 15),

        "countries": [
            "KZ",
            "RU"
        ],

        "devices": [
            "Android",
            "Windows",
            "iPhone"
        ]
    },

    "business": {

        "avg_amount": (500, 5000),

        "activity_per_day": (10, 40),

        "countries": [
            "KZ",
            "DE",
            "UK"
        ],

        "devices": [
            "MacBook",
            "Windows",
            "iPhone"
        ]
    }
}


# =====================================================
# STATIC DATA
# =====================================================

MERCHANTS = [

    "Amazon",
    "Apple",
    "Steam",
    "Netflix",
    "eBay",
    "AliExpress",
    "Booking",
    "Spotify"
]

PAYMENT_METHODS = [

    "Card",
    "ApplePay",
    "GooglePay"
]

CARD_TYPES = [

    "Visa",
    "Mastercard"
]

TRANSACTION_TYPES = [

    "P2P",
    "Online",
    "POS"
]

FRAUD_SCENARIOS = [

    "account_takeover",

    "velocity_attack",

    "money_mule",

    "device_spoofing",

    "social_engineering"
]


# =====================================================
# WAIT FOR API
# =====================================================

def wait_for_api():

    print("⏳ Waiting for API...")

    while True:

        try:

            response = requests.get(
                HEALTHCHECK_URL,
                timeout=3
            )

            if response.status_code == 200:

                print("✅ API is ready")

                return

        except:
            pass

        time.sleep(2)


# =====================================================
# GENERATE USER
# =====================================================

def generate_user():

    user_type = random.choice(
        list(USER_TYPES.keys())
    )

    profile = USER_TYPES[user_type]

    country = random.choice(
        profile["countries"]
    )

    avg_amount = round(

        random.uniform(
            profile["avg_amount"][0],
            profile["avg_amount"][1]
        ),

        2
    )

    device = random.choice(
        profile["devices"]
    )


    return {

        "user_id":
            f"U{random.randint(1000,9999)}",

        "user_type":
            user_type,

        "country":
            country,

        "age":
            random.randint(18, 65),

        "home_ip":
            f"10.0.{random.randint(1,50)}.{random.randint(1,255)}",

        "devices":
            {device},

        "account_age_days":
            random.randint(1, 365),

        "avg_amount":
            avg_amount,

        "history":
            [],
    "activity_weight":
        random.randint(5, 20),
        "fraud_prone":
        random.random()<0.15,

    "target_transactions":
        random.randint(30, 150)
    }


# =====================================================
# REALISTIC TIMESTAMP
# =====================================================

def realistic_timestamp(user_type, fraud=False):

    now = datetime.now()

    days_back = random.randint(0, 30)

    base_date = now - timedelta(days=days_back)

    if fraud:

        hour = random.choice([
            0, 1, 2, 3, 4,
            10, 11, 12, 13,
            18, 19, 20, 21
        ])

    elif user_type == "student":

        hour = random.choice([
            16, 17, 18,
            19, 20, 21, 22
        ])

    elif user_type == "worker":

        hour = random.choice([
            8, 9, 10,
            11, 12,
            18, 19, 20
        ])

    else:

        hour = random.choice([
            8, 9, 10,
            11, 12, 13,
            14, 15, 16
        ])

    timestamp = base_date.replace(
        hour=hour,
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0
    )

    return timestamp.isoformat()

# =====================================================
# NORMAL TRANSACTION
# =====================================================

def generate_normal_transaction(user):

    device = random.choice(
        list(user["devices"])
    )
    recipient_id = (
        f"U{random.randint(1000, 9999)}"
    )

    while recipient_id == user["user_id"]:
        recipient_id = (
            f"U{random.randint(1000, 9999)}"
        )

    recipient_country = random.choice([
        "KZ",
        "RU",
        "UZ",
        "KG",
        "DE",
        "UK"
    ])

    amount = np.random.normal(

        loc=user["avg_amount"],

        scale=user["avg_amount"] * 0.25
    )

    amount = max(
        1,
        round(float(amount), 2)
    )

    tx = {

        "transaction_id":
            f"TX{random.randint(100000,999999)}",

        "user_id":
            user["user_id"],

        "amount":
            amount,

        "currency":
            "USD",

        "country":
            user["country"],

        "ip_address":
            user["home_ip"],

        "device":
            device,

        "recipient_id":
            recipient_id,

        "recipient_country":
            recipient_country,

        "recipient_is_resident":
            recipient_country == "KZ",

        "sender_is_resident":
            user["country"] == "KZ",

        "account_age_days":
            user["account_age_days"],

        "timestamp":
    realistic_timestamp(user["user_type"]),

        "merchant":
            random.choice(MERCHANTS),

        "payment_method":
            random.choice(PAYMENT_METHODS),

        "user_age":
            user["age"],

        "user_registration_country":
            user["country"],

        "card_type":
            random.choice(CARD_TYPES),

        "transaction_type":
            random.choice(
                TRANSACTION_TYPES
            )
    }
    return tx


# =====================================================
# FRAUD TRANSACTION
# =====================================================

def generate_fraud_transaction(user):

    scenario = random.choice(
        FRAUD_SCENARIOS
    )

    device = random.choice(
        list(user["devices"])
    )


    country = user["country"]

    ip = user["home_ip"]

    amount = round(

        user["avg_amount"]

        *

        random.uniform(2, 6),

        2
    )

    timestamp = realistic_timestamp(

        user["user_type"],

        fraud=True
    )

    # =============================================
    # RECIPIENT
    # =============================================

    recipient_id = (
        f"U{random.randint(1000,9999)}"
    )

    while recipient_id == user["user_id"]:

        recipient_id = (
            f"U{random.randint(1000,9999)}"
        )

    recipient_country = random.choice([
        "KZ",
        "RU",
        "UZ",
        "KG",
        "DE",
        "UK"
    ])

    # =============================================
    # ACCOUNT TAKEOVER
    # =============================================

    if scenario == "account_takeover":

        device = random.choice([
            "iPhone",
            "Android",
            "MacBook"
        ])

        ip = (
            f"185.{random.randint(1,255)}."
            f"{random.randint(1,255)}."
            f"{random.randint(1,255)}"
        )

        amount *= 1.5

    # =============================================
    # DEVICE SPOOFING
    # =============================================

    elif scenario == "device_spoofing":

        device = random.choice([
            "Unknown",
            "VirtualMachine"
        ])

    # =============================================
    # MONEY MULE
    # =============================================

    elif scenario == "money_mule":

        country = random.choice([
            "RU",
            "BR",
            "CN",
            "UA"
        ])

        amount = round(

            random.uniform(
                50,
                400
            ),

            2
        )

    # =============================================
    # SOCIAL ENGINEERING
    # =============================================

    elif scenario == "social_engineering":

        amount *= random.uniform(
            3,
            5
        )

    tx = {

        "transaction_id":
            f"TX{random.randint(100000,999999)}",

        "user_id":
            user["user_id"],

        "amount":
            round(amount, 2),

        "currency":
            "USD",

    "recipient_id":
        recipient_id,

    "recipient_country":
        recipient_country,

    "recipient_is_resident":
        recipient_country == "KZ",

    "sender_is_resident":
        user["country"] == "KZ",

    "account_age_days":
        user["account_age_days"],
        "country":
            country,

        "ip_address":
            ip,

        "device":
            device,

        "timestamp":
            timestamp,

        "merchant":
            random.choice(MERCHANTS),

        "payment_method":
            random.choice(PAYMENT_METHODS),

        "user_age":
            user["age"],

        "user_registration_country":
            user["country"],

        "card_type":
            random.choice(CARD_TYPES),

        "transaction_type":
            "P2P"
    }

    return tx


# =====================================================
# LABEL GENERATION
# =====================================================

def calculate_fraud_probability(tx, user):

    fraud_probability = 0.0

    # =============================================
    # AMOUNT DEVIATION
    # =============================================

    if tx["amount"] > user["avg_amount"] * 3:

        fraud_probability += 0.30

    # =============================================
    # NEW DEVICE
    # =============================================

    if tx["device"] not in user["devices"]:

        fraud_probability += 0.20

    # =============================================
    # COUNTRY MISMATCH
    # =============================================

    if tx["country"] != user["country"]:

        fraud_probability += 0.25

    # =============================================
    # NIGHT ACTIVITY
    # =============================================

    hour = datetime.fromisoformat(
        tx["timestamp"]
    ).hour

    if hour in [0, 1, 2, 3, 4]:

        fraud_probability += 0.15

    # =============================================
    # SUSPICIOUS IP
    # =============================================

    if tx["ip_address"].startswith("185."):

        fraud_probability += 0.20

    # =============================================
    # VELOCITY CHECK
    # =============================================

    recent_tx = [

        t

        for t in user["history"]

        if (

            datetime.now()

            -

            datetime.fromisoformat(
                t["timestamp"]
            )

        ).seconds < 600
    ]

    if len(recent_tx) >= 5:

        fraud_probability += 0.25

    return min(
        fraud_probability,
        0.95
    )

# =====================================================
# SAVE TRANSACTION
# =====================================================

def save_transaction(tx):

    file_exists = os.path.isfile(
        "transactions.csv"
    )

    df = pd.DataFrame([tx])

    df.to_csv(

        "transactions.csv",

        mode="a",

        header=not file_exists,

        index=False
    )
# =====================================================
# SEND TRANSACTION
# =====================================================

def send_transaction(payload):

    try:

        response = requests.post(
            API_URL,
            json=payload,
            timeout=5
        )

        if response.status_code == 200:

            data = response.json()

            risk = round(

                data.get(
                    "risk_score",
                    0
                ) * 100,

                2
            )

            fraud = data.get(
                "is_fraud",
                False
            )

            status = (

                "🚨 FRAUD"

                if fraud

                else "✅ NORMAL"
            )

            print(

                f"{status} | "

                f"{payload['transaction_id']} | "

                f"{payload['user_id']} | "

                f"${payload['amount']} | "

                f"Risk={risk}%"
            )

        else:

            print(
                f"❌ API ERROR "
                f"{response.status_code}"
            )

    except Exception as e:

        print(
            "❌ Failed:",
            str(e)
        )


# =====================================================
# MAIN
# =====================================================

print("\n🚀 REALISTIC AI FRAUD GENERATOR\n")

wait_for_api()

users = {}

# =====================================================
# INITIAL USERS
# =====================================================

for _ in range(100):

    user = generate_user()

    users[user["user_id"]] = user

print(
    f"✅ Generated {len(users)} users"
)



# =====================================================
# MAIN LOOP
# =====================================================

while True:

    population = []

    for u in users.values():
        population.extend(
            [u] * u["activity_weight"]
        )

    user = random.choice(population)

    # =============================================
    # FRAUD RATIO
    # =============================================

    if user["fraud_prone"]:

        fraud_mode = (
                random.random() < 0.20
        )

    else:

        fraud_mode = (
                random.random() < 0.02
        )

    # =============================================
    # GENERATE TRANSACTION
    # =============================================

    if fraud_mode:

        tx = generate_fraud_transaction(
            user
        )

    else:

        tx = generate_normal_transaction(
            user
        )

    # =============================================
    # LABEL
    # =============================================

    fraud_probability = (
        calculate_fraud_probability(
            tx,
            user
        )
    )

    tx["is_fraud"] = int(
        random.random()
        < fraud_probability
    )

    # =============================================
    # STORE HISTORY
    # =============================================

    user["history"].append({

        "amount":
            tx["amount"],

        "timestamp":
            tx["timestamp"],

        "country":
            tx["country"],

        "device":
            tx["device"]
    })
    if len(user["history"]) >= user["target_transactions"]:
        user["activity_weight"] = 1

    # limit history
    if len(user["history"]) > 100:

        user["history"] = (
            user["history"][-100:]
        )

    # =============================================
    # SEND
    # =============================================
    save_transaction(tx)
    send_transaction(tx)

    # =============================================
    # VELOCITY ATTACKS
    # =============================================

    if random.random() < 0.02:

        print(
            "⚡ Velocity attack simulation"
        )

        for _ in range(
            random.randint(5, 10)
        ):

            tx = generate_fraud_transaction(
                user
            )

            tx["is_fraud"] = 1

            send_transaction(tx)

            time.sleep(
                random.uniform(
                    0.2,
                    1.0
                )
            )

    # =============================================
    # DELAY
    # =============================================

    time.sleep(
        random.uniform(
            1.0,
            3.0
        )
    )