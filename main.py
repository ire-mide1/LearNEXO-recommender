import requests
import os
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd

# ---------------------- Settings ----------------------
HF_TOKEN = os.environ.get("HF_TOKEN", "YOUR_HF_TOKEN")  # On Render, set in env vars!

# ---------------------- Topics ------------------------
topics = [
    {"topic_id": "t1", "name": "Basic Arithmetic",     "tags": ["math", "arithmetic"], "prerequisite": None},
    {"topic_id": "t2", "name": "Fractions",            "tags": ["math", "arithmetic"], "prerequisite": "t1"},
    {"topic_id": "t3", "name": "Linear Equations",     "tags": ["math", "algebra"],    "prerequisite": "t2"},
    {"topic_id": "t4", "name": "Quadratic Equations",  "tags": ["math", "algebra"],    "prerequisite": "t3"},
    {"topic_id": "t5", "name": "Geometry Basics",      "tags": ["math", "geometry"],   "prerequisite": None},
    {"topic_id": "t6", "name": "Shapes and Angles",    "tags": ["math", "geometry"],   "prerequisite": "t5"},
]

# ------------------ Recommender Logic -----------------
def get_recommendations(student, df, topics, mastery_threshold=70):
    topic_dict = {t['topic_id']: t for t in topics}
    recommendations = []
    weak_topics = df[(df['student'] == student) & (df['score'] < mastery_threshold)]
    for _, weak_row in weak_topics.iterrows():
        topic_id = weak_row['topic_id']
        topic_info = topic_dict[topic_id]
        prereq_id = topic_info.get('prerequisite')
        # 1. If a prerequisite exists, recommend it regardless of its score (so users always have a next step)
        if prereq_id:
            prereq_name = topic_dict[prereq_id]['name']
            recommendations.append({
                "recommend_for": topic_info['name'],
                "recommended_topic": prereq_name
            })
        else:
            # 2. Otherwise, recommend a related topic (in same tag group)
            specific_tags = [tag for tag in topic_info['tags'] if tag != 'math']
            for specific_tag in specific_tags:
                for t in topics:
                    if t['topic_id'] != topic_id and specific_tag in t['tags'] and 'math' in t['tags']:
                        recommendations.append({
                            "recommend_for": topic_info['name'],
                            "recommended_topic": t['name']
                        })
    # Deduplicate recommendations
    seen = set()
    deduped = []
    for rec in recommendations:
        key = (rec['recommend_for'], rec['recommended_topic'])
        if key not in seen:
            deduped.append(rec)
            seen.add(key)
    return deduped, []

# --------- Hugging Face Inference API (LLM Feedback) ----------
def get_llm_feedback_hfapi(rec):
    prompt = (
        f"Question: Give a creative, direct, and motivating one-sentence message to a student struggling with {rec['recommend_for']}. "
        f"Encourage them to review {rec['recommended_topic']} by telling them how it will help. "
        "Do not give definitions or introductions. Start with encouragement.\n"
        "Answer:"
    )
    API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt, "parameters": {"max_new_tokens": 60}}
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        outputs = response.json()
        if isinstance(outputs, list) and "generated_text" in outputs[0]:
            result = outputs[0]["generated_text"]
        elif isinstance(outputs, dict) and "generated_text" in outputs:
            result = outputs["generated_text"]
        elif isinstance(outputs, dict) and "error" in outputs:
            return "Sorry, API error: " + outputs["error"]
        else:
            result = str(outputs)
        feedback = str(result).split("Answer:")[-1].split("Question:")[0].strip().strip('"').strip("'")
        return feedback
    else:
        return f"Error: {response.status_code} {response.text}"

def add_llm_feedback_hfapi(recommendations):
    results = []
    for rec in recommendations:
        feedback = get_llm_feedback_hfapi(rec)
        rec_with_feedback = {**rec, "feedback": feedback}
        results.append(rec_with_feedback)
    return results

# ------------------ FastAPI Setup ---------------------
class ScoreInput(BaseModel):
    student: str
    scores: dict  # e.g. {"Basic Arithmetic": 45, ...}

app = FastAPI()

@app.post("/recommend/")
def recommend(input: ScoreInput):
    data = []
    for t in topics:
        score = input.scores.get(t["name"], 0)
        data.append({"student": input.student, "topic_id": t["topic_id"], "score": score})
    df = pd.DataFrame(data)
    core_recs, _ = get_recommendations(input.student, df, topics)
    core_feedback = add_llm_feedback_hfapi(core_recs)
    return [
        {
            "recommend_for": r["recommend_for"],
            "recommended_topic": r["recommended_topic"],
            "feedback": r["feedback"]
        }
        for r in core_feedback
    ]
