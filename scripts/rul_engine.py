import joblib
import pandas as pd
from datetime import datetime
from pathlib import Path

# ==========================================
# PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
RUL_MODEL_PATH = BASE_DIR / "models" / "rul_model.pkl"

# ==========================================
# LOAD RUL MODEL
# ==========================================

rul_model = joblib.load(str(RUL_MODEL_PATH))

# ==========================================
# PHASE E
# RUL PREDICTION
# ==========================================

def predict_rul(user_data):

    input_df = pd.DataFrame([user_data])

    predicted_rul = rul_model.predict(
        input_df
    )[0]

    return float(predicted_rul)


# ==========================================
# PHASE F
# CONTEXT-AWARE KM LEFT
# ==========================================

def calculate_km_left(
    predicted_rul,
    vehicle_type,
    driving_pattern,
    road_condition,
    weather_condition
):

    weather_factor = {
        "Clear": 1.00,
        "Rain": 0.95,
        "Heavy Rain": 0.90,
        "Flood-Prone": 0.85
    }

    road_factor = {
        "Good": 1.00,
        "Average": 0.95,
        "Poor": 0.85
    }

    usage_factor = {
        "Highway": 1.00,
        "Mixed": 0.95,
        "City": 0.90,
        "Off-road": 0.75
    }

    vehicle_factor = {
        "Sedan": 1.00,
        "SUV": 0.95,
        "Motorcycle": 1.00,
        "Truck": 0.80
    }

    wf = weather_factor.get(
        weather_condition,
        1.0
    )

    rf = road_factor.get(
        road_condition,
        1.0
    )

    uf = usage_factor.get(
        driving_pattern,
        1.0
    )

    vf = vehicle_factor.get(
        vehicle_type,
        1.0
    )

    adjusted_km = (
        predicted_rul
        * wf
        * rf
        * uf
        * vf
    )

    return round(adjusted_km, 2)


# ==========================================
# PHASE G
# RISK ASSESSMENT
# ==========================================

def calculate_risk(
    health_score,
    severity,
    adjusted_km
):

    severity = severity.lower()

    base_risk = (
        100 - health_score
    )

    severity_penalty = {
        "minor": 5,
        "moderate": 15,
        "severe": 30
    }

    sev_penalty = (
        severity_penalty.get(
            severity,
            0
        )
    )

    if adjusted_km > 40000:

        km_penalty = 0

    elif adjusted_km > 20000:

        km_penalty = 10

    elif adjusted_km > 10000:

        km_penalty = 20

    else:

        km_penalty = 30

    risk_score = (
        base_risk
        + sev_penalty
        + km_penalty
    )

    risk_score = min(
        100,
        max(0, risk_score)
    )

    if risk_score <= 25:

        risk_level = "LOW"

    elif risk_score <= 50:

        risk_level = "MEDIUM"

    elif risk_score <= 75:

        risk_level = "HIGH"

    else:

        risk_level = "CRITICAL"

    return {
        "risk_score": round(
            risk_score,
            2
        ),
        "risk_level": risk_level
    }


# ==========================================
# PHASE H
# AI MAINTENANCE ASSISTANT
# ==========================================

def generate_recommendation(
    health_score,
    severity,
    adjusted_km,
    risk_level,
    weather,
    road_condition
):

    recommendations = []

    severity = severity.lower()

    if risk_level == "LOW":

        recommendations.append(
            "Tyre condition is healthy."
        )

    elif risk_level == "MEDIUM":

        recommendations.append(
            "Monitor tyre condition regularly."
        )

    elif risk_level == "HIGH":

        recommendations.append(
            "Schedule tyre inspection soon."
        )

    else:

        recommendations.append(
            "Replace tyre immediately."
        )

    if severity == "minor":

        recommendations.append(
            "Minor wear detected."
        )

    elif severity == "moderate":

        recommendations.append(
            "Moderate tyre damage detected."
        )

    elif severity == "severe":

        recommendations.append(
            "Severe tyre degradation detected."
        )

    if adjusted_km < 10000:

        recommendations.append(
            "Remaining usable distance is critically low."
        )

    if weather.lower() in [
        "rain",
        "heavy rain"
    ]:

        recommendations.append(
            "Wet roads may reduce traction."
        )

    if road_condition.lower() == "poor":

        recommendations.append(
            "Poor roads may accelerate tyre wear."
        )

    return recommendations


# ==========================================
# PHASE I
# INSPECTION REPORT
# ==========================================

def generate_report(
    vehicle_type,
    health_score,
    severity,
    predicted_rul,
    adjusted_km,
    risk_score,
    risk_level,
    recommendations
):

    inspection_date = (
        datetime.now()
        .strftime("%d-%m-%Y")
    )

    report = f"""
=========================================
AI TYRE HEALTH INSPECTION REPORT
=========================================

Inspection Date : {inspection_date}

Vehicle Type    : {vehicle_type}

Health Score    : {health_score:.0f}/100

Severity        : {severity.title()}

Predicted RUL   : {predicted_rul:,.0f} km

Adjusted KM Left: {adjusted_km:,.0f} km

Risk Score      : {risk_score:.0f}/100

Risk Level      : {risk_level}

-----------------------------------------

Recommendations

"""

    for idx, rec in enumerate(
        recommendations,
        start=1
    ):

        report += (
            f"{idx}. {rec}\n"
        )

    report += """

=========================================
END OF REPORT
=========================================
"""

    return report