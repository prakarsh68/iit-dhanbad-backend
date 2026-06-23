import os
import cv2
from pathlib import Path

# ==========================================
# PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

OUTPUT_DIR = BASE_DIR / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

# ==========================================
# LOAD MODELS (CONDITIONAL)
# ==========================================

MOCK_YOLO = os.environ.get("MOCK_YOLO", "false").lower() == "true"

detector_model = None
health_model = None
severity_model = None

if not MOCK_YOLO:
    try:
        from ultralytics import YOLO
        detector_model = YOLO(
            str(MODELS_DIR / "detector.pt")
        )
        health_model = YOLO(
            str(MODELS_DIR / "health.pt")
        )
        severity_model = YOLO(
            str(MODELS_DIR / "severity.pt")
        )
    except ImportError:
        print("Ultralytics not installed. Falling back to mock mode.")
        MOCK_YOLO = True

# ==========================================
# HEALTH SCORE
# ==========================================

def calculate_health_score(
    health_label,
    severity_label,
    confidence
):

    if health_label.lower() == "normal":
        return 100

    confidence = float(confidence)

    if severity_label == "Minor":

        return int(
            80 + (1 - confidence) * 20
        )

    elif severity_label == "Moderate":

        return int(
            50 + (1 - confidence) * 30
        )

    elif severity_label == "Severe":

        return int(
            10 + (1 - confidence) * 40
        )

    return 100


# ==========================================
# IMAGE ANALYSIS
# ==========================================

def analyze_image(image_path):

    image = cv2.imread(image_path)

    if image is None:

        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    if MOCK_YOLO:
        path_str = str(image_path).lower()
        if "front_left" in path_str:
            health_label = "normal"
            severity_label = "Normal"
            health_score = 92
        elif "front_right" in path_str:
            health_label = "normal"
            severity_label = "Normal"
            health_score = 90
        elif "rear_left" in path_str:
            health_label = "damaged"
            severity_label = "Moderate"
            health_score = 58
        elif "rear_right" in path_str:
            health_label = "damaged"
            severity_label = "Minor"
            health_score = 82
        else:
            health_label = "normal"
            severity_label = "Normal"
            health_score = 95

        h, w, _ = image.shape
        x1, y1, x2, y2 = int(w * 0.15), int(h * 0.15), int(w * 0.85), int(h * 0.85)

        tyre_info = {
            "health_label": health_label,
            "health_conf": 0.92,
            "severity_label": severity_label,
            "severity_conf": 0.88,
            "health_score": health_score,
            "bbox": [x1, y1, x2, y2]
        }
        tyres = [tyre_info]
        avg_health_score = health_score
        worst_tyre = tyre_info
    else:
        results = detector_model(
            image,
            conf=0.25,
            verbose=False
        )

        tyres = []

        for result in results:

            boxes = result.boxes

            for box in boxes:

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )

                tyre_crop = image[
                    y1:y2,
                    x1:x2
                ]

                if tyre_crop.size == 0:
                    continue

                # ===============================
                # HEALTH
                # ===============================

                health_result = health_model(
                    tyre_crop,
                    verbose=False
                )[0]

                health_id = int(
                    health_result.probs.top1
                )

                health_conf = float(
                    health_result.probs.top1conf
                )

                health_label = (
                    health_model.names[
                        health_id
                    ]
                )

                # ===============================
                # DEFAULTS
                # ===============================

                severity_label = "Normal"
                severity_conf = 1.0

                score = 100

                # ===============================
                # SEVERITY
                # ===============================

                if health_label.lower() == "damaged":

                    severity_result = (
                        severity_model(
                            tyre_crop,
                            verbose=False
                        )[0]
                    )

                    severity_id = int(
                        severity_result.probs.top1
                    )

                    severity_conf = float(
                        severity_result.probs.top1conf
                    )

                    severity_label = (
                        severity_model.names[
                            severity_id
                        ]
                    )

                    score = (
                        calculate_health_score(
                            health_label,
                            severity_label,
                            severity_conf
                        )
                    )

                tyre_info = {

                    "health_label":
                        health_label,

                    "health_conf":
                        health_conf,

                    "severity_label":
                        severity_label,

                    "severity_conf":
                        severity_conf,

                    "health_score":
                        score,

                    "bbox":
                        [x1, y1, x2, y2]
                }

                tyres.append(
                    tyre_info
                )

        # ======================================
        # FALLBACK
        # ======================================

        if len(tyres) == 0:

            health_result = health_model(
                image,
                verbose=False
            )[0]

            health_id = int(
                health_result.probs.top1
            )

            health_label = (
                health_model.names[
                    health_id
                ]
            )

            score = 100

            severity_label = "Normal"

            if health_label.lower() == "damaged":

                severity_result = (
                    severity_model(
                        image,
                        verbose=False
                    )[0]
                )

                severity_id = int(
                    severity_result.probs.top1
                )

                severity_label = (
                    severity_model.names[
                        severity_id
                    ]
                )

                severity_conf = float(
                    severity_result.probs.top1conf
                )

                score = (
                    calculate_health_score(
                        health_label,
                        severity_label,
                        severity_conf
                    )
                )

            tyres.append({

                "health_label":
                    health_label,

                "health_conf":
                    1.0,

                "severity_label":
                    severity_label,
            
                "severity_conf":                
                    1.0,

                "health_score":
                    score,

                "bbox":
                    None
            })

        avg_health_score = sum(
            t["health_score"]
            for t in tyres
        ) / len(tyres)

        worst_tyre = min(
            tyres,
            key=lambda x:
            x["health_score"]
        )

       # ======================================
    # DRAW BOUNDING BOXES
    # ======================================

    annotated_image = image.copy()

    for tyre in tyres:

        if tyre["bbox"] is None:
            continue

        x1, y1, x2, y2 = tyre["bbox"]

        if tyre["health_label"].lower() == "damaged":
            color = (0, 0, 255)
        else:
            color = (0, 255, 0)

        cv2.rectangle(
            annotated_image,
            (x1, y1),
            (x2, y2),
            color,
            2
        )

        label = (
            f"{tyre['severity_label']} "
            f"({tyre['health_score']})"
        )

        cv2.putText(
            annotated_image,
            label,
            (x1, max(20, y1 - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2
        )

    # ======================================
    # SAVE IMAGES FOR DIGITAL TWIN
    # ======================================

    input_path = OUTPUT_DIR / "latest_input.jpg"
    output_path = OUTPUT_DIR / "latest_output.jpg"

    cv2.imwrite(
        str(input_path),
        image
    )

    cv2.imwrite(
        str(output_path),
        annotated_image
    )

    return {

        "num_tyres":
            len(tyres),

        "avg_health_score":
            round(
                avg_health_score,
                2
            ),

        "overall_severity":
            worst_tyre[
                "severity_label"
            ],

        "input_image":
            str(input_path),

        "output_image":
            str(output_path),

        "annotated_image":
            annotated_image,

        "tyres":
            tyres
    }