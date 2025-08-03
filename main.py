from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import pandas as pd

topics = [
    {"topic_id": "t1", "name": "Basic Arithmetic",     "tags": ["math", "arithmetic"], "prerequisite": None},
    {"topic_id": "t2", "name": "Fractions",            "tags": ["math", "arithmetic"], "prerequisite": "t1"},
    {"topic_id": "t3", "name": "Linear Equations",     "tags": ["math", "algebra"],    "prerequisite": "t2"},
    {"topic_id": "t4", "name": "Quadratic Equations",  "tags": ["math", "algebra"],    "prerequisite": "t3"},
    {"topic_id": "t5", "name": "Geometry Basics",      "tags": ["math", "geometry"],   "prerequisite": None},
    {"topic_id": "t6", "name": "Shapes and Angles",    "tags": ["math", "geometry"],   "prerequisite": "t5"},
]

model_name = "microsoft/phi-3-mini-4k-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

def get_recommendations(student, df, topics, mastery_threshold=70):
    topic_dict = {t['topic_id']: t for t in topics}
    recommendations = []
    weak_topics = df[(df['student'] == student) & (df['score'] < mastery_threshold)]
    for _, weak_row in weak_topics.iterrows():
        topic_id = weak_row['topic_id']
        topic_info = topic_dict[topic_id]
        prereq_id = topic_info.get('prerequisite')
        if prereq_id:
            prereq_row = df[(df['student'] == student) & (df['topic_id'] == prereq_id)]
            if not prereq_row.empty and prereq_row.iloc[0]['score'] < mastery_threshold:
                prereq_name = topic_dict[prereq_id]['name']
                recommendations.append({
                    "recommend_for": topic_info['name'],
                    "recommended_topic": prereq_name
                })
        else:
            specific_tags = [tag for tag in topic_info['tags'] if tag != 'math']
            for specific_tag in specific_tags:
                for t in topics:
                    if (t['topic_id'] != topic_id and specific_tag in t['tags'] and 'math' in t['tags']):
                        t_row = df[(df['student'] == student) & (df['topic_id'] == t['topic_id'])]
                        if not t_row.empty and t_row.iloc[0]['score'] < mastery_threshold:
                            recommendations.append({
                                "recommend_for": topic_info['name'],
                                "recommended_topic": t['name']
                            })
    seen = set()
    deduped = []
    for rec in recommendations:
        key = (rec['recommend_for'], rec['recommended_topic'])
        if key not in seen:
            deduped.append(rec)
            seen.add(key)
    return deduped, []

def get_llm_feedback_phi3(rec):
    prompt = (
        f"Question: Give a creative, direct, and motivating one-sentence message to a student struggling with {rec['recommend_for']}. "
        f"Encourage them to review {rec['recommended_topic']} by telling them how it will help. "
        "Do not give definitions or introductions. Start with encouragement.\n"
        "Answer:"
    )
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=60, pad_token_id=tokenizer.eos_token_id)
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)
    feedback = result.split("Answer:")[-1].split("Question:")[0].strip().strip('"').strip("'")
    return feedback

def add_llm_feedback_phi3(recommendations):
    results = []
    for rec in recommendations:
        feedback = get_llm_feedback_phi3(rec)
        rec_with_feedback = {**rec, "feedback": feedback}
        results.append(rec_with_feedback)
    return results

class ScoreInput(BaseModel):
    student: str
    scores: dict

app = FastAPI()

@app.post("/recommend/")
def recommend(input: ScoreInput):
    data = []
    for t in topics:
        score = input.scores.get(t["name"], 0)
        data.append({"student": input.student, "topic_id": t["topic_id"], "score": score})
    df = pd.DataFrame(data)
    core_recs, _ = get_recommendations(input.student, df, topics)
    core_feedback = add_llm_feedback_phi3(core_recs)
    return [
        {
            "recommend_for": r["recommend_for"],
            "recommended_topic": r["recommended_topic"],
            "feedback": r["feedback"]
        }
        for r in core_feedback
    ]
