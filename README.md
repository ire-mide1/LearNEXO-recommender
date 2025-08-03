# LearNEXO-recommender
# AI Math Coach – Personalized Recommender

## Overview

This project provides an AI-powered recommendation and feedback system for students struggling with different math topics.

## How to Run Locally

1. Install requirements:
    pip install -r requirements.txt

2. Start backend:
    uvicorn main:app --reload

3. In another terminal, start frontend:
    streamlit run app.py

4. Open the Streamlit app and input your scores!

## Deployment

- Can be deployed to Render or Railway. Set backend and frontend start commands as shown above.
- Update Streamlit's API endpoint with your public backend URL when deployed.
