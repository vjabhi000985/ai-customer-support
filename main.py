from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os

# ==============================
# CONFIG
# ==============================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

# ==============================
# MEMORY + ANALYTICS STORE
# ==============================

chat_history = []
issue_counts = {
    "Delivery": 0,
    "Refund": 0,
    "Technical": 0,
    "Other": 0
}

# ==============================
# REQUEST MODEL
# ==============================

class Query(BaseModel):
    message: str
    prototype: str

# ==============================
# HELPER FUNCTIONS
# ==============================

def classify_issue(text):
    text = text.lower()
    if "delivery" in text or "delay" in text:
        return "Delivery"
    elif "refund" in text or "money" in text:
        return "Refund"
    elif "error" in text or "not working" in text:
        return "Technical"
    else:
        return "Other"

def is_customer_query(text):
    keywords = ["order","delivery","refund","payment","error",
                "problem","issue","cancel","technical","account"]
    return any(word in text.lower() for word in keywords)

# ==============================
# MAIN ENDPOINT
# ==============================

@app.post("/ask")
def ask_ai(query: Query):

    if not is_customer_query(query.message):
        return {
            "reply": "I am designed only for customer support queries.",
            "issue_counts": issue_counts
        }

    system_prompt = """
    You are an AI Customer Support Assistant.
    Only answer customer service related queries.
    """

    if query.prototype == "Prototype 1":
        prompt = query.message

    elif query.prototype == "Prototype 2":
        chat_history.append(query.message)
        prompt = "\n".join(chat_history)

    else:
        chat_history.append(query.message)
        prompt = "\n".join(chat_history)

    response = model.generate_content(system_prompt + prompt)

    reply = response.text

    issue_type = classify_issue(query.message)
    issue_counts[issue_type] += 1

    return {
        "reply": reply,
        "issue_counts": issue_counts,
        "issue_type": issue_type
    }