import json
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)

HISTORY_FILE = DATA_DIR / "inspection_history.json"


def save_inspection(
    health_score,
    severity,
    predicted_rul,
    adjusted_km,
    risk_level
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
            str(risk_level)
    }

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

    with open(
        HISTORY_FILE,
        "r"
    ) as f:

        history = json.load(
            f
        )

    history.append(
        inspection
    )

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