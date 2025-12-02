from fastapi import FastAPI
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import json
import os
from fastapi.middleware.cors import CORSMiddleware
import spacy

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ClassifyRequest(BaseModel):
    url: str

class Settings(BaseModel):
    intervention_style: str
    session_time: int
    context_paragraph: str

class SafeTopicsRequest(BaseModel):
    paragraph: str

CACHE_FILENAME = "classification_cache.json"
DISTRACTION_HISTORY_FILENAME = "../../final/distractionHistory.json"
USER_DATA_FILENAME = "../../final/userData.json"
USER_SESSIONS_FILENAME = "../../final/userSessions.json"
USER_XP_FILENAME = "../../final/userXP.json"


def load_cache():
    if os.path.exists(CACHE_FILENAME):
        with open(CACHE_FILENAME, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILENAME, 'w') as f:
        json.dump(cache, f, indent=4)

cache = load_cache()
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
nlp = spacy.load("en_core_web_sm")

def scrape_url(url: str):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text()
    except requests.exceptions.RequestException as e:
        print(f"Error scraping URL: {e}")
        return None

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/api/classify")
def classify_url(request: ClassifyRequest):
    url = request.url
    if url in cache:
        return {"url": url, "classification": cache[url]}

    content = scrape_url(url)
    if not content:
        return {"url": url, "classification": "Could not scrape content"}

    labels = ["Distracting", "Not Distracting"]
    result = classifier(content, labels)
    classification = result['labels'][0]
    cache[url] = classification
    save_cache(cache)
    return {"url": url, "classification": classification}

@app.get("/api/history")
def get_history():
    if os.path.exists(DISTRACTION_HISTORY_FILENAME):
        with open(DISTRACTION_HISTORY_FILENAME, 'r') as f:
            return json.load(f)
    return {"Distractions": []}

@app.get("/api/sessions")
def get_sessions():
    if os.path.exists(USER_SESSIONS_FILENAME):
        with open(USER_SESSIONS_FILENAME, 'r') as f:
            return json.load(f)
    return {"Sessions": []}

@app.get("/api/xp")
def get_xp():
    if os.path.exists(USER_XP_FILENAME):
        with open(USER_XP_FILENAME, 'r') as f:
            return json.load(f)
    return {"XP": 0}

@app.get("/api/settings")
def get_settings():
    if os.path.exists(USER_DATA_FILENAME):
        with open(USER_DATA_FILENAME, 'r') as f:
            return json.load(f)
    return {}

@app.post("/api/settings")
def update_settings(settings: Settings):
    if os.path.exists(USER_DATA_FILENAME):
        with open(USER_DATA_FILENAME, 'r') as f:
            data = json.load(f)
    else:
        data = {}

    data["Intervention Style"] = settings.intervention_style
    data["Session Time"] = settings.session_time
    data["context_paragraph"] = settings.context_paragraph

    with open(USER_DATA_FILENAME, 'w') as f:
        json.dump(data, f, indent=4)

    return {"message": "Settings updated successfully"}

@app.post("/api/safe_topics")
def get_safe_topics(request: SafeTopicsRequest):
    doc = nlp(request.paragraph)
    topics = [chunk.text for chunk in doc.noun_chunks]
    return {"safe_topics": topics}
