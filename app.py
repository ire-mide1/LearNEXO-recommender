import streamlit as st
import requests

# ------ Update this with your deployed API URL ------
API_URL = "https://learnexo-recommender-1.onrender.com/recommend/"

# If running locally for testing, use: API_URL = "http://localhost:10000/recommend/"

# ----- Topic List -----
topics = [
    "Basic Arithmetic",
    "Fractions",
    "Linear Equations",
    "Quadratic Equations",
    "Geometry Basics",
    "Shapes and Angles"
]

st.title("AI Math Coach – Personalized Recommendations")

# ----- User Inputs -----
student = st.text_input("Enter your name")
topic_scores = {}

st.subheader("Enter your scores for each topic (0–100):")
for topic in topics:
    score = st.number_input(f"{topic}", min_value=0, max_value=100, value=50, step=1)
    topic_scores[topic] = score

if st.button("Get AI Recommendations"):
    with st.spinner("Generating recommendations... (may take a few seconds)"):
        payload = {
            "student": student if student.strip() else "Student",
            "scores": topic_scores
        }
        try:
            response = requests.post(API_URL, json=payload, timeout=30)
            if response.status_code == 200:
                recs = response.json()
                if recs:
                    st.header("Your Recommendations:")
                    for rec in recs:
                        st.write(f"**For improvement in `{rec['recommend_for']}`:**")
                        st.info(f"Review **{rec['recommended_topic']}**")
                        st.success(rec['feedback'])
                        st.markdown("---")
                else:
                    st.warning("No recommendations needed—you’re doing great in all topics!")
            else:
                st.error(f"API call failed ({response.status_code}): {response.text}")
        except Exception as e:
            st.error(f"An error occurred: {e}")

st.caption("Built with Streamlit + Hugging Face LLM + FastAPI.")
