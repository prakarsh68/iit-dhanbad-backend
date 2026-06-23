---
title: IIT Project API
emoji: 🚗
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# AI Tyre Health Inspection System

Developed at IIT Dhanbad

## Features

- Tyre Detection
- Health Classification
- Severity Analysis
- Remaining Useful Life Prediction
- PDF Report Generation
- Streamlit Dashboard

## Models

- detector.pt
- health.pt
- severity.pt
- rul_model.pkl

## Run

```bash
pip install -r requirements.txt
streamlit run scripts/dashboard.py
```

## Deployment

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/prakarsh68/iit-dhanbad-backend)

Click the button above to deploy this FastAPI backend to Render. The configuration is automatically loaded from `render.yaml`.