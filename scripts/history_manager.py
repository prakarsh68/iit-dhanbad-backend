import json
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)

HISTORY_FILE = DATA_DIR / "inspection_history.json"
LATEST_FILE = DATA_DIR / "latest_result.json"


def save_inspection(
    health_score,
    severity,
    predicted_rul,
    adjusted_km,
    risk_level,
    risk_score=None,
    vehicle_type=None,
    temperature=None,
    pressure=None,
    defect=None,
    recommendations=None
):

    inspection = {

        "date": datetime.now().strftime(
            "%d-%m-%Y %H:%M"
        ),

        "health_score":
            float(health_score),

        "severity":
            str(severity),

        "predicted_rul":
            float(predicted_rul),

        "adjusted_km":
            float(adjusted_km),

        "risk_level":
            str(risk_level),

        "risk_score":
            risk_score,

        "vehicle_type":
            vehicle_type,

        "temperature":
            temperature,

        "pressure":
            pressure,

        "defect":
            defect,

        "recommendations":
            recommendations if recommendations else []
    }

    # Save latest inspection
    with open(
        LATEST_FILE,
        "w"
    ) as f:

        json.dump(
            inspection,
            f,
            indent=4
        )

    # Create history file if needed
    if not os.path.exists(
        HISTORY_FILE
    ):

        with open(
            HISTORY_FILE,
            "w"
        ) as f:

            json.dump(
                [],
                f
            )

    # Load history
    with open(
        HISTORY_FILE,
        "r"
    ) as f:

        history = json.load(
            f
        )

    # Append new record
    history.append(
        inspection
    )

    # Save history
    with open(
        HISTORY_FILE,
        "w"
    ) as f:

        json.dump(
            history,
            f,
            indent=4
        )


def load_history():

    if not os.path.exists(
        HISTORY_FILE
    ):

        return []

    with open(
        HISTORY_FILE,
        "r"
    ) as f:

        return json.load(
            f
        )


def load_latest():

    if not os.path.exists(
        LATEST_FILE
    ):

        return None

    with open(
        LATEST_FILE,
        "r"
    ) as f:

        return json.load(
            f
        )