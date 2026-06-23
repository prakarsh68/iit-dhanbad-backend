from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import json

from scripts.tyre_analysis import analyze_image

from scripts.rul_engine import (
    predict_rul,
    calculate_km_left,
    calculate_risk,
    generate_recommendation
)

from scripts.history_manager import (
    save_inspection
)

from scripts.report_generator import (
    generate_pdf_report
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

LATEST_FILE = (
    DATA_DIR /
    "latest_result.json"
)

app.mount(
    "/data",
    StaticFiles(directory=str(DATA_DIR)),
    name="data"
)


# ==========================================
# REQUEST MODEL
# ==========================================

class WheelRequest(BaseModel):

    wheel: str

    vehicle_type: str

    pressure: float

    recommended_pressure: float

    road_condition: str

    weather_condition: str

    driving_pattern: str

    tyre_age: int

    tread_depth: float

# ==========================================
# ROOT
# ==========================================

@app.get("/")
def root():

    return {
        "status": "running"
    }


# ==========================================
# LATEST RESULT
# ==========================================

@app.get("/latest-result")
def latest_result():

    if not LATEST_FILE.exists():

        return {
            "error":
            "No inspection data"
        }

    with open(
        LATEST_FILE,
        "r"
    ) as f:

        return json.load(f)


# ==========================================
# ANALYZE SELECTED WHEEL
# ==========================================

@app.post("/analyze-wheel")
def analyze_wheel(
    data: WheelRequest
):

    wheel_map = {

        "Front Left Wheel":
            DATA_DIR /
            "wheels" /
            "front_left.jpg",

        "Front Right Wheel":
            DATA_DIR /
            "wheels" /
            "front_right.jpg",

        "Rear Left Wheel":
            DATA_DIR /
            "wheels" /
            "rear_left.jpg",

        "Rear Right Wheel":
            DATA_DIR /
            "wheels" /
            "rear_right.jpg"
    }

    image_path = wheel_map.get(
        data.wheel
    )

    if image_path is None:

        return {
            "success": False,
            "message":
            "Invalid wheel selected"
        }

    if not image_path.exists():

        return {
            "success": False,
            "message":
            f"Image not found: {image_path}"
        }

    # ======================================
    # PHASE A-D
    # ======================================

    analysis = analyze_image(
        str(image_path)
    )

    health_score = analysis[
        "avg_health_score"
    ]

    pressure_diff = abs(
    data.pressure -
    data.recommended_pressure
)
    
    if pressure_diff >= 8:
        health_score -= 15
    
    elif pressure_diff >= 5:
        health_score -= 10
    elif pressure_diff >= 3:
        health_score -= 5

    health_score = max(
    0,
    min(100, health_score)
)

    severity = analysis[
        "overall_severity"
    ]

    # ======================================
    # RUL INPUT DATA
    # ======================================

    user_data = {

        "vehicle_model":
            "Hyundai Elantra",

        "fuel_type":
            "petrol",

        "transmission_type":
            "automatic",

        "maximum_power(hp)":
            110,

        "maximum_torque(N/m)":
            265,

        "maximum_speed (km/h)":
            205,

        "steering_radius(m)":
            5.4,

        "vehicle_acceleration(0-100 km/h in seconds)":
            3.1,

        "vehicle_mileage(mpg)":
            33,

        "vehicle_sprung_mass(kg)":
            1350,

        "tyre_camber_angle(degree)":
            -1,

        "tyre_brand":
            "MRF",

        "tyre_size":
            "205/55R16",

        "tread_material":
            "silica and carbon",

        "Standard_tread_depth(mm)":
            7.14,

        "tread_pattern":
            "Asymmetrical",

        "country":
            "India",

        "tread_wear_rating (UTQG)":
            500,

        "average_tread_temperature(celsius)":
            30,

        "recommended_inflation_pressure(psi)":
            data.recommended_pressure,

        "average_inflation_pressure(psi)":
            data.pressure,

        "tyre_age(years)":
            data.tyre_age,

        "number_of_punctures":
            0,

        "current_tread_depth(mm)":
            data.tread_depth,

        "road_condition":
            data.road_condition,

        "weather_condition":
            data.weather_condition,

        "axle_type(driven/dead)":
            "drive",

        "expected_tyre_life(km)":
            60000,

        "retreaded":
            "no",

        "kilometers_driven(km)":
            10000
    }

    # ======================================
    # PHASE E
    # ======================================

    predicted_rul = predict_rul(
        user_data
    )

    # ======================================
    # PHASE F
    # ======================================

    adjusted_km = calculate_km_left(
    predicted_rul,
    data.vehicle_type,
    data.driving_pattern,
    data.road_condition,
    data.weather_condition
)


    # ======================================
    # PHASE G
    # ======================================

    risk = calculate_risk(
        health_score,
        severity,
        adjusted_km
    )

    risk_score = risk[
        "risk_score"
    ]

    risk_level = risk[
        "risk_level"
    ]

    # ======================================
    # PHASE H
    # ======================================

    recommendations = (
    generate_recommendation(
        health_score,
        severity,
        adjusted_km,
        risk_level,
        data.weather_condition,
        data.road_condition
    )
)

    
    # ======================================
    # SAVE RESULT
    # ======================================

    save_inspection(

        health_score=health_score,

        severity=severity,

        predicted_rul=predicted_rul,

        adjusted_km=adjusted_km,

        risk_level=risk_level,

        risk_score=risk_score,

        vehicle_type=data.vehicle_type,

        temperature=22,

        pressure=data.pressure,

        defect=severity,

        recommendations=recommendations
    )

    # ======================================
    # PDF REPORT
    # ======================================

    generate_pdf_report(

        filename="latest_report.pdf",

        vehicle_type=data.vehicle_type,

        health_score=health_score,

        severity=severity,

        predicted_rul=predicted_rul,

        adjusted_km=adjusted_km,

        risk_score=risk_score,

        risk_level=risk_level,

        recommendations=recommendations
    )

    return {

        "success": True,

        "selected_wheel":
            data.wheel,

        "health_score":
            health_score,

        "severity":
            severity,

        "risk_score":
            risk_score,

        "risk_level":
            risk_level,

        "adjusted_km":
            adjusted_km,

        "predicted_rul":
            predicted_rul,

        "input_image":
            "/data/latest_input.jpg",

        "output_image":
            "/data/latest_output.jpg"
    }


# ==========================================
# DOWNLOAD REPORT
# ==========================================

@app.get("/download-report")
def download_report():

    report_file = (
        BASE_DIR /
        "latest_report.pdf"
    )

    if not report_file.exists():

        return {
            "success": False,
            "message":
            "Report not found"
        }

    return FileResponse(
        path=str(report_file),
        filename="Tyre_Inspection_Report.pdf",
        media_type="application/pdf"
    )