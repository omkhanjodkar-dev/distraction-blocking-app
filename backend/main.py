import json
import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from dotenv import load_dotenv

# --- Environment Variables ---
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
LLAMA_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# --- App Initialization ---
app = FastAPI(
    title="Focus App API",
    description="API for the Focus App, managing user data and AI interactions.",
    version="1.0.0"
)

# --- CORS Middleware ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class Settings(BaseModel):
    InterventionStyle: str
    SessionTime: int
    ai_model: str
    context_paragraph: str
    safe_topics: List[str]

class Distraction(BaseModel):
    event: str
    timestamp: str

class Session(BaseModel):
    duration: int
    timestamp: str

class Gamification(BaseModel):
    xp: int

class AiRequest(BaseModel):
    prompt: str

class AiResponse(BaseModel):
    response: str

class VideoClassificationRequest(BaseModel):
    video_title: str

class VideoClassificationResponse(BaseModel):
    is_distraction: bool

# --- File Paths ---
# All data files are expected to be in the same directory as this main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_PATH = os.path.join(BASE_DIR, "userData.json")
HISTORY_PATH = os.path.join(BASE_DIR, "distractionHistory.json")
SESSIONS_PATH = os.path.join(BASE_DIR, "userSessions.json")
XP_PATH = os.path.join(BASE_DIR, "userXP.json")
CONTEXT_CACHE_PATH = os.path.join(BASE_DIR, "context_cache.json")


# --- Helper Functions ---
def get_json_data(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
    except (IOError, json.JSONDecodeError):
        pass
    return {}

def save_json_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the Focus App API"}

# --- Settings Endpoints ---
@app.get("/settings", response_model=Settings)
def get_settings():
    settings = get_json_data(USER_DATA_PATH)
    return {
        "InterventionStyle": settings.get("Intervention Style", "nudge"),
        "SessionTime": settings.get("Session Time", 25),
        "ai_model": settings.get("ai_model", "Deepseek"),
        "context_paragraph": settings.get("context_paragraph", ""),
        "safe_topics": settings.get("safe_topics", [])
    }

@app.post("/settings", response_model=Settings)
def update_settings(settings: Settings):
    current_data = get_json_data(USER_DATA_PATH)
    new_data = {
        "Intervention Style": settings.InterventionStyle,
        "Session Time": settings.SessionTime,
        "ai_model": settings.ai_model,
        "context_paragraph": settings.context_paragraph,
        "safe_topics": settings.safe_topics,
        "backendActive": current_data.get("backendActive", False)
    }
    save_json_data(USER_DATA_PATH, new_data)
    return settings

# --- History Endpoints ---
@app.get("/history", response_model=List[Distraction])
def get_distraction_history():
    history = get_json_data(HISTORY_PATH)
    return history.get("Distractions", [])

@app.post("/history", response_model=Distraction)
def add_distraction(distraction: Distraction):
    history = get_json_data(HISTORY_PATH)
    if "Distractions" not in history:
        history["Distractions"] = []
    
    # Pydantic models need to be converted to dicts for JSON serialization
    history["Distractions"].append(distraction.dict())
    save_json_data(HISTORY_PATH, history)
    return distraction

# --- Session Endpoints ---
@app.get("/sessions", response_model=List[Dict])
def get_sessions():
    sessions = get_json_data(SESSIONS_PATH)
    # The frontend might expect a list of objects with 'duration' and 'timestamp'
    return sessions.get("Sessions", [])

@app.post("/sessions", response_model=Session)
def add_session(session: Session):
    sessions = get_json_data(SESSIONS_PATH)
    if "Sessions" not in sessions:
        sessions["Sessions"] = []
    
    # The old format was a list of lists, let's stick to a list of objects
    sessions["Sessions"].append({"duration": session.duration, "timestamp": session.timestamp})
    save_json_data(SESSIONS_PATH, sessions)
    return session

# --- Gamification Endpoints ---
@app.get("/gamification", response_model=Gamification)
def get_gamification_data():
    xp_data = get_json_data(XP_PATH)
    return {"xp": xp_data.get("XP", 0)}

@app.post("/gamification", response_model=Gamification)
def update_xp(gamification_data: Gamification):
    save_json_data(XP_PATH, {"XP": gamification_data.xp})
    return gamification_data

@app.post("/classify_video", response_model=VideoClassificationResponse)
def classify_video_endpoint(request: VideoClassificationRequest):
    settings = get_json_data(USER_DATA_PATH)
    safe_topics = settings.get("safe_topics", [])
    ai_model = settings.get("ai_model", "Deepseek")

    if not safe_topics:
        # If no safe topics are defined, we cannot classify based on them.
        # By default, we'll consider it not a distraction if there's nothing to compare against.
        # Or, we could raise an HTTPException asking the user to define safe topics.
        # For now, let's return False (not a distraction) as a default.
        return {"is_distraction": False}
    
    is_distraction = classify_video_with_ai(request.video_title, safe_topics, ai_model)
    return {"is_distraction": is_distraction}


# --- AI Logic ---
def get_topics_from_ai(paragraph: str, model: str) -> list:
    """
    Sends a paragraph to an AI model to extract key topics.
    Uses caching to avoid redundant API calls.
    """
    context_cache = get_json_data(CONTEXT_CACHE_PATH)
    if paragraph in context_cache:
        print("Found context in cache.")
        return context_cache[paragraph]

    print(f"Context not in cache, calling AI model: {model}")
    
    prompt = f'''
From the following paragraph, extract a list of key topics or subjects the user is interested in. The user is a student.
Return a JSON object with a single key "safe_topics" which is a list of strings.
Paragraph: "{paragraph}"
Your response must be a valid JSON object. Only return the JSON object, with no other text or explanations.
'''
    
    if model == "Deepseek":
        api_url, api_key, model_name = DEEPSEEK_API_URL, DEEPSEEK_API_KEY, "deepseek-chat"
    elif model == "Llama-3.1":
        api_url, api_key, model_name = LLAMA_API_URL, LLAMA_API_KEY, "llama3-8b-8192"
    else:
        raise HTTPException(status_code=400, detail=f"Model '{model}' is not supported.")

    if not api_key or "YOUR_" in api_key:
        raise HTTPException(status_code=500, detail=f"API Key for {model} is not configured on the server.")

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are an expert text classifier. Your response is only a valid JSON object."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        api_response = response.json()
        json_response_str = api_response.get('choices', [{}])[0].get('message', {}).get('content')

        if not json_response_str:
            raise HTTPException(status_code=500, detail="AI server returned an empty response.")

        result = json.loads(json_response_str)
        
        if 'safe_topics' in result and isinstance(result['safe_topics'], list):
            topics = result['safe_topics']
            context_cache[paragraph] = topics
            save_json_data(CONTEXT_CACHE_PATH, context_cache)
            return topics
        else:
            raise HTTPException(status_code=500, detail="AI response is not in the expected format.")

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Error contacting AI server: {e}")
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI server response: {e}")

def classify_video_with_ai(video_title: str, safe_topics: List[str], model: str) -> bool:
    """
    Sends a video title and safe topics to an AI model to classify if the video is a distraction.
    """
    if not safe_topics:
        return False # If no safe topics are defined, nothing can be a distraction based on them

    print(f"Calling AI model: {model} to classify video: '{video_title}'")
    
    # Construct a clear prompt for the AI
    # Explicitly ask for a boolean response to simplify parsing
    prompt = f"""
Given the following list of safe work-related topics: {', '.join(safe_topics)}.
Is the video titled "{video_title}" related to any of these safe topics?
Answer with only 'true' if it is related to any of the safe topics, and 'false' if it is not related to any of them (meaning it's a potential distraction).
Your response must be a valid JSON object with a single key "is_related" and a boolean value.
Only return the JSON object, with no other text or explanations.
"""
    
    if model == "Deepseek":
        api_url, api_key, model_name = DEEPSEEK_API_URL, DEEPSEEK_API_KEY, "deepseek-chat"
    elif model == "Llama-3.1":
        api_url, api_key, model_name = LLAMA_API_URL, LLAMA_API_KEY, "llama3-8b-8192"
    else:
        raise HTTPException(status_code=400, detail=f"Model '{model}' is not supported for video classification.")

    if not api_key or "YOUR_" in api_key:
        raise HTTPException(status_code=500, detail=f"API Key for {model} is not configured on the server.")

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are an expert content classifier. Your response is only a valid JSON object."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        api_response = response.json()
        json_response_str = api_response.get('choices', [{}])[0].get('message', {}).get('content')

        if not json_response_str:
            raise HTTPException(status_code=500, detail="AI server returned an empty response for video classification.")

        result = json.loads(json_response_str)
        
        if 'is_related' in result and isinstance(result['is_related'], bool):
            # If is_related is true, then it's NOT a distraction.
            # If is_related is false, then it IS a distraction.
            return not result['is_related']
        else:
            raise HTTPException(status_code=500, detail="AI response for video classification is not in the expected format.")

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Error contacting AI server for video classification: {e}")
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI server response for video classification: {e}")


# --- AI Endpoint ---
@app.post("/ai_req", response_model=AiResponse)
async def ai_request(request: AiRequest):
    """
    Generic endpoint to handle AI requests. It currently only dispatches
    to the topic extraction logic based on prompt content.
    """
    if "extract a list of key topics" in request.prompt:
        # Extract the paragraph from the prompt
        # This is a bit brittle and depends on the exact prompt format from the old main.py
        try:
            paragraph_match = request.prompt.split('Paragraph: "')[1].split('"')[0]
            user_settings = get_json_data(USER_DATA_PATH)
            ai_model = user_settings.get("ai_model", "Deepseek")
            
            new_topics = get_topics_from_ai(paragraph_match, ai_model)
            
            # The original app expected a JSON string inside the 'response' key
            return {"response": json.dumps({"safe_topics": new_topics})}
        
        except IndexError:
            raise HTTPException(status_code=400, detail="Could not parse paragraph from the prompt.")
    
    # Fallback for other AI requests if any were to be added
    return {"response": "Request received, but no specific action was triggered."}


# --- To run this app: ---
# 1. Make sure you have a .env file in this directory with your DEEPSEEK_API_KEY
# 2. Run the command: uvicorn backend.main:app --reload