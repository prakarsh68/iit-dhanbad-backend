import streamlit as st
import tempfile
from tyre_analysis import analyze_image
from rul_engine import (
    predict_rul,
    calculate_km_left,
    calculate_risk,
    generate_recommendation
)
from report_generator import generate_pdf_report

from history_manager import (
    save_inspection,
    load_history
)

st.set_page_config(
    page_title="AI Tyre Health Inspection",
    layout="wide"
)

st.title("🚗 AI Tyre Health Inspection System")

# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.header("Vehicle Information")

vehicle_type = st.sidebar.selectbox(
    "Vehicle Type",
    ["Sedan", "SUV", "Truck", "Motorcycle"]
)

fuel_type = st.sidebar.selectbox(
    "Fuel Type",
    ["Petrol", "Diesel", "Electric"]
)

transmission = st.sidebar.selectbox(
    "Transmission",
    ["Manual", "Automatic"]
)

tyre_brand = st.sidebar.text_input(
    "Tyre Brand",
    "MRF"
)

tyre_size = st.sidebar.text_input(
    "Tyre Size",
    "205/55R16"
)

expected_life = st.sidebar.number_input(
    "Expected Tyre Life (km)",
    value=60000
)

km_driven = st.sidebar.number_input(
    "Kilometers Driven",
    value=10000
)

road_condition = st.sidebar.selectbox(
    "Road Condition",
    ["Good", "Average", "Poor"]
)

weather_condition = st.sidebar.selectbox(
    "Weather Condition",
    ["Clear", "Rain", "Heavy Rain"]
)

driving_pattern = st.sidebar.selectbox(
    "Driving Pattern",
    ["Highway", "Mixed", "City", "Off-road"]
)

# ==========================================
# IMAGE UPLOAD
# ==========================================

uploaded_file = st.file_uploader(
    "Upload Vehicle Image",
    type=["jpg", "jpeg", "png", "webp"]
)

# ==========================================
# ANALYZE
# ==========================================

if st.button("Analyze Tyres"):

    if uploaded_file is None:

        st.error("Please upload an image.")

    else:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".jpg"
        ) as tmp_file:

            tmp_file.write(
                uploaded_file.getbuffer()
            )

            image_path = tmp_file.name

        st.image(
            uploaded_file,
            caption="Uploaded Vehicle Image",
            use_container_width=True
        )

        # ==================================
        # PHASE A-D
        # ==================================

        analysis = analyze_image(
            image_path
        )

        health_score = analysis[
            "avg_health_score"
        ]

        severity = analysis[
            "overall_severity"
        ]

        # ==================================
        # USER DATA FOR RUL
        # ==================================

        user_data = {

            "vehicle_model":
                "Hyundai Elantra",

            "fuel_type":
                fuel_type.lower(),

            "transmission_type":
                transmission.lower(),

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
                tyre_brand,

            "tyre_size":
                tyre_size,

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
                22,

            "recommended_inflation_pressure(psi)":
                35,

            "average_inflation_pressure(psi)":
                30,

            "tyre_age(years)":
                2,

            "number_of_punctures":
                0,

            "current_tread_depth(mm)":
                5.5,

            "road_condition":
                road_condition,

            "weather_condition":
                weather_condition,

            "axle_type(driven/dead)":
                "drive",

            "expected_tyre_life(km)":
                expected_life,

            "retreaded":
                "no",

            "kilometers_driven(km)":
                km_driven
        }

        # ==================================
        # PHASE E
        # ==================================

        predicted_rul = predict_rul(
            user_data
        )

        # ==================================
        # PHASE F
        # ==================================

        adjusted_km = calculate_km_left(
            predicted_rul,
            vehicle_type,
            driving_pattern,
            road_condition,
            weather_condition
        )

        # ==================================
        # PHASE G
        # ==================================

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

        # ==================================
        # PHASE H
        # ==================================

        recommendations = (
            generate_recommendation(
                health_score,
                severity,
                adjusted_km,
                risk_level,
                weather_condition,
                road_condition
            )
        )

        save_inspection(
            
            health_score=health_score,
            severity=severity,
            predicted_rul=predicted_rul,
            adjusted_km=adjusted_km,
            risk_level=risk_level
        )
        

        # ==================================
        # RESULTS
        # ==================================

        st.subheader("Detected Tyres")

        st.image(
            analysis["annotated_image"],
            channels="BGR",
            use_container_width=True
        )

        st.subheader("Overall Health")

        st.progress(
            float(health_score) / 100
        )

        st.write(
            f"Health Score: {health_score:.0f}/100"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Health Score",
            f"{health_score:.0f}/100"
        )

        col2.metric(
            "Severity",
            severity
        )

        col3.metric(
            "Tyres Found",
            analysis["num_tyres"]
        )

        col4, col5, col6 = st.columns(3)

        col4.metric(
            "Predicted RUL",
            f"{predicted_rul:,.0f} km"
        )

        col5.metric(
            "Adjusted KM Left",
            f"{adjusted_km:,.0f} km"
        )

        col6.metric(
            "Risk Level",
            risk_level
        )

        st.subheader(
            "Individual Tyre Analysis"
        )

        for i, tyre in enumerate(
            analysis["tyres"],
            start=1
        ):

            with st.expander(
                f"Tyre {i}"
            ):

                st.write(
                    f"Health: {tyre['health_label']}"
                )

                st.write(
                    f"Severity: {tyre['severity_label']}"
                )

                st.write(
                    f"Health Score: {tyre['health_score']}/100"
                )

                if "health_conf" in tyre:
                    
                    st.write(
                        f"Confidence: {tyre['health_conf']:.2%}"
                    )

        st.subheader(
            "AI Recommendations"
        )

        for rec in recommendations:

            st.info(rec)

        
        # ==================================
        # # PDF REPORT
        # # ==================================
        
        pdf_file = generate_pdf_report(
            
            filename="latest_report.pdf",
            vehicle_type=vehicle_type,
            health_score=health_score,
            severity=severity,
            predicted_rul=predicted_rul,
            adjusted_km=adjusted_km,
            risk_score=risk_score,
            risk_level=risk_level,
            recommendations=recommendations
        )
        
        with open(
            pdf_file,
            "rb"
        ) as file:
            
            st.download_button(
                
                label="📄 Download Inspection Report",
                data=file,
                file_name="AI_Tyre_Inspection_Report.pdf",
                mime="application/pdf"
    )
        
    # ==================================
    # # INSPECTION HISTORY
    # # ==================================
    
    st.subheader(
        "📈 Inspection History"
    )
    
    history = load_history()
    
    if len(history) == 0:
        st.warning(
            "No inspection history found."
        )
        
    else:
        for idx, item in enumerate(
            reversed(history[-10:]),
            start=1
        ):
            with st.expander(
                f"Inspection #{idx}"
            ):
                st.write(
                    f"Date: {item['date']}"
                    )
                
                st.write(
                    f"Health Score: {item['health_score']:.0f}/100"
                )
                
                st.write(
                    f"Severity: {item['severity']}"
                    )
                
                st.write(
                    f"Predicted RUL: {item['predicted_rul']:,.0f} km"
                    )
                
                st.write(
                    f"Adjusted KM Left: {item['adjusted_km']:,.0f} km"
                    )
                
                st.write(
                    f"Risk Level: {item['risk_level']}"
                    )
        
    
             
     