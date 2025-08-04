import streamlit as st
import requests

st.title("AI Math Coach – Personalized Recommendations")

student = st.text_input("Enter your name")
topic_scores = {}
topics = [
    "Basic Arithmetic",
    "Fractions",
    "Linear Equations",
    "Quadratic Equations",
    "Geometry Basics",
    "Shapes and Angles"
]

for topic in topics:
    score = st.number_input(f"Your score for {topic}", min_value=0, max_value=100, value=50)
    topic_scores[topic] = score

if st.button("Get AI Recommendation"):
    payload = {
        "student": student,
        "scores": topic_scores
    }
    # Update URL with your deployed API endpoint if not localhost!
    response = requests.post("http://localhost:8000/recommend/", json=payload)
    if response.status_code == 200:
        recs = response.json()
        st.header("Your Recommendations:")
        for rec in recs:
            st.write(f"**For improvement in {rec['recommend_for']}, review:** {rec['recommended_topic']}")
            st.success(rec['feedback'])
    else:
        st.error("API call failed. Try again!")
