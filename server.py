#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import urllib.request
import urllib.parse
import urllib.error
import ssl
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, DefaultDict, Union
from collections import defaultdict
from itertools import islice

from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, create_engine, Session, select
from datetime import datetime

# --- Configuration ---
PORT = 5001
DATABASE_URL = "sqlite:///./medpulse.db"
DATA_FILE = Path("medicines.json")
ENV_FILE = Path(".env")

# --- Database Models ---
class Medicine(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    strength: Optional[str] = None
    use_case: Optional[str] = None
    category: Optional[str] = Field(default=None, index=True)
    price: float = Field(default=0.0)
    quantity: int = Field(default=0)
    manufacturer: Optional[str] = None
    expiry: Optional[str] = None
    alternatives: Optional[str] = None
    dosage: Optional[str] = None
    avg_daily_demand: float = Field(default=0.0)
    days_to_stockout: int = Field(default=999)

# User model removed - open access system

# --- Auth Requirements ---
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")
# Authentication code removed

# --- AI Logic Components ---
def load_env():
    # Priority 1: System Environment (for Cloud)
    # Priority 2: Local .env file
    env = dict(os.environ)
    if ENV_FILE.exists():
        with open(ENV_FILE, "r") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, val = line.strip().split("=", 1)
                    if key not in env:
                        env[key] = val
    return env

CONFIG = load_env()
GEMINI_KEYS = [
    CONFIG.get("GEMINI_API_KEY"),
    "AIzaSyBwQcjgmXUAsw5r4FZXO5t8_EZ_aUm_TGE",
    "AIzaSyCbsbvGCe7C9mCtdaTycZB2eUFuzsYKG_E"
]
# Clean up keys and remove placeholders
GEMINI_KEYS = [k.strip() for k in GEMINI_KEYS if k and "YOUR_API_KEY" not in k]
GEMINI_API_KEY = GEMINI_KEYS[0] if GEMINI_KEYS else "YOUR_API_KEY_HERE"

# --- FastAPI App Initialization ---
app = FastAPI(title="MedPulse Clinical Intelligence API", version="12.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# Session middleware removed - authentication not required

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def get_session():
    with Session(engine) as session:
        yield session

# --- AI Responders ---
def get_ollama_response(prompt):
    try:
        url = "http://localhost:11434/api/generate"
        payload = {"model": "llama3", "prompt": prompt, "stream": False}
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("response")
    except: return None

def get_ddg_ai_response(prompt):
    try:
        context = ssl._create_unverified_context()
        status_url = "https://duckduckgo.com/duckchat/v1/status"
        status_req = urllib.request.Request(status_url, headers={"x-vqd-accept": "1", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(status_req, context=context, timeout=5) as resp:
            vqd = resp.headers.get("x-vqd-4")
            if not vqd: return None
            
        chat_url = "https://duckduckgo.com/duckchat/v1/chat"
        payload = {"model": "meta-llama/Llama-3-70b-chat-hf", "messages": [{"role": "user", "content": prompt}]}
        chat_req = urllib.request.Request(chat_url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "x-vqd-4": vqd, "User-Agent": "Mozilla/5.0"}, method="POST")
        with urllib.request.urlopen(chat_req, context=context, timeout=10) as resp:
            raw_res = resp.read().decode()
            full_text = ""
            for line in raw_res.split("\n"):
                if line.startswith("data:"):
                    try:
                        chunk = json.loads(line[5:])
                        if "message" in chunk: full_text += chunk["message"]
                    except: pass
            return full_text if full_text else None
    except: return None

# --- Ultra-Smart Clinical Knowledge Base (Offline Intelligence) ---
KNOWLEDGE_BASE = {
    "paracetamol": "Paracetamol is a common analgesic and antipyretic. For adults, the standard dose is 500mg to 1g every 4-6 hours. It is effective for mild to moderate pain and fever. Avoid exceeding 4g in 24 hours to prevent liver toxicity.",
    "amoxicillin": "Amoxicillin is a broad-spectrum penicillin antibiotic. It is used to treat bacterial infections like pneumonia, bronchitis, and ear infections. Typical dosage is 250mg-500mg three times daily. Complete the full course even if you feel better.",
    "fever": "For fever management: 1. Maintain hydration. 2. Use antipyretics like Paracetamol (500mg). 3. Rest in a cool room. If temperature exceeds 103°F (39.4°C) or lasts >3 days, consult a doctor immediately.",
    "headache": "Headaches can be tension-based or migraineous. Immediate relief includes Paracetamol or Ibuprofen. Ensure hydration and rest in a dark room. Seek urgent care if accompanied by neck stiffness or vision changes.",
    "cough": "Cough treatment depends on type (dry vs. productive). Expectorants help with mucus, while suppressants help with dry coughs. Amoxicillin may be required if a bacterial infection is suspected.",
    "diabetes": "Diabetes management focuses on blood sugar control. Metformin (500mg) is the first-line treatment. Monitor glucose regularly and maintain a balanced diet with regular physical activity.",
    "hypertension": "High blood pressure is managed with lifestyle changes and medications like Amlodipine. Reduce salt intake, exercise daily, and avoid smoking to protect cardiac health."
}

def get_local_reply(user_message, medicines: List[Medicine]):
    """Ultra-Smart Clinical Engine (Fallback Tier)"""
    q = user_message.lower()
    res = "🧠 **Smart Clinical Analysis (Local Reasoning)**\n\n"
    
    # Check Knowledge Base
    found_kb = False
    for key, info in KNOWLEDGE_BASE.items():
        if key in q:
            res += f"### 📘 Clinical Overview: {key.capitalize()}\n{info}\n\n"
            found_kb = True
            break
            
    # Check Inventory
    found_meds = [m for m in medicines if m.name.lower() in q or (m.use_case and any(w in m.use_case.lower() for w in q.split()))]
    if found_meds:
        res += "### 💊 Inventory & Dosage Status\n"
        for m in islice(found_meds, 3):
            status = "✅ IN STOCK" if m.quantity > 0 else "⚠️ OUT OF STOCK"
            res += f"- **{m.name}** ({m.strength or ''})\n  • *Usage*: {m.use_case or ''}\n  • *Price*: ₹{m.price}\n  • *Availability*: {status}\n\n"
    elif not found_kb:
        res += "I have analyzed your query across our clinical registry. While I couldn't find a direct match, I recommend consulting a licensed pharmacist for these specific symptoms.\n\n"

    res += "### ⚠️ Safety Sentinel\n> This analysis is based on established clinical protocols. Professional consultation is mandatory for formal prescriptions."
    return res

def get_ai_response(user_message, medicines_context, custom_api_key=None, target_lang='en'):
    # Key Rotation Strategy
    keys_to_try = [custom_api_key.strip()] if custom_api_key else GEMINI_KEYS
    
    lang_map = {'en': 'English', 'hi': 'Hindi', 'te': 'Telugu'}
    lang_name = lang_map.get(target_lang, 'English')
    
    stock_info = "\n".join([
        f"- {m.name} ({m.strength or 'N/A'}): {'✅ In Stock' if m.quantity > 0 else '⚠️ Out of Stock'}. Use: {m.use_case}"
        for m in medicines_context[:10]
    ])
    
    system_prompt = f"""
    ROLE: You are 'MedPulse Universal AI'—a high-performance, versatile artificial intelligence.
    CAPABILITIES: Expert in pharmacy, diagnostics, and general intelligence.
    INVENTORY STATUS: {stock_info}
    INSTRUCTIONS:
    1. Respond TOTALLY in {lang_name} script (No mixing).
    2. Answer ANY user query brilliantly.
    3. PIVOT every single response back to medical, health, or pharmacy needs.
    USER QUERY: "{user_message}"
    """

    # Tier 1 & 2: Gemini Cluster with Key Rotation (v1beta for maximum compatibility)
    for active_key in keys_to_try:
        if not active_key or "YOUR_API_KEY" in active_key: continue
        for model in ["gemini-1.5-flash-latest", "gemini-pro"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={active_key}"
                payload = {"contents": [{"parts": [{"text": system_prompt}]}]}
                req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, context=ssl._create_unverified_context(), timeout=12) as response:
                    res_data = json.loads(response.read().decode())
                    return res_data['candidates'][0]['content']['parts'][0]['text']
            except Exception as e:
                print(f"❌ Gemini Failure ({model}): {e}")

    # Tier 3: DuckDuckGo AI (Final Cloud Fallback)
    ddg_res = get_ddg_ai_response(system_prompt)
    if ddg_res: return ddg_res

    # Tier 3: Local Clinical Sync (Final Safety Net)
    return get_local_reply(user_message, medicines_context)

# Admin dashboard and user management routes removed

# --- Standard API Endpoints ---
def med_to_dict(m: Medicine) -> dict:
    return {
        "id": m.id,
        "name": m.name or "",
        "strength": m.strength or "",
        "use_case": m.use_case or "",
        "alternative": m.alternatives or "",
        "dosage": m.dosage or "",
        "stock": "Yes" if m.quantity > 0 else "No",
        "price": m.price or 0.0,
        "quantity": m.quantity or 0,
        "manufacturer": m.manufacturer or "",
        "expiry": m.expiry or ""
    }

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html", {})

@app.get("/api/health")
def health_check():
    return {"status": "ok", "keyConfigured": True, "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/alerts")
def get_alerts(session: Session = Depends(get_session)):
    meds = session.exec(select(Medicine)).all()
    out_of_stock = [m for m in meds if m.quantity == 0]
    return {"count": len(out_of_stock), "alerts": [{"id": m.id, "name": m.name, "msg": "Out of stock"} for m in out_of_stock]}

@app.get("/api/medicines")
def get_medicines(session: Session = Depends(get_session)):
    meds = session.exec(select(Medicine)).all()
    return {"success": True, "data": [med_to_dict(m) for m in meds]}

@app.post("/api/medicines")
def add_medicine(med_data: Dict, session: Session = Depends(get_session)):
    db_med = Medicine(
        id=str(int(time.time())),
        name=med_data.get("name", ""),
        strength=med_data.get("strength"),
        use_case=med_data.get("use_case"),
        alternatives=med_data.get("alternative"),
        dosage=med_data.get("dosage"),
        quantity=1 if med_data.get("stock") == "Yes" else 0
    )
    session.add(db_med)
    session.commit()
    return {"success": True, "data": med_to_dict(db_med)}

@app.put("/api/medicines/{med_id}")
def update_medicine(med_id: str, med_data: Dict, session: Session = Depends(get_session)):
    db_med = session.get(Medicine, med_id)
    if not db_med: raise HTTPException(status_code=404, detail="Not found")
    
    if "name" in med_data: db_med.name = med_data["name"]
    if "strength" in med_data: db_med.strength = med_data["strength"]
    if "use_case" in med_data: db_med.use_case = med_data["use_case"]
    if "alternative" in med_data: db_med.alternatives = med_data["alternative"]
    if "dosage" in med_data: db_med.dosage = med_data["dosage"]
    if "stock" in med_data: db_med.quantity = 1 if med_data["stock"] == "Yes" else 0
    
    session.add(db_med)
    session.commit()
    return {"success": True, "data": med_to_dict(db_med)}

@app.patch("/api/medicines/{med_id}/stock")
def update_medicine_stock(med_id: str, stock_data: Dict, session: Session = Depends(get_session)):
    db_med = session.get(Medicine, med_id)
    if not db_med: raise HTTPException(status_code=404, detail="Not found")
    
    db_med.quantity = 1 if stock_data.get("stock") == "Yes" else 0
    session.add(db_med)
    session.commit()
    return {"success": True, "data": med_to_dict(db_med)}

@app.delete("/api/medicines/{med_id}")
def delete_medicine(med_id: str, session: Session = Depends(get_session)):
    db_med = session.get(Medicine, med_id)
    if not db_med: raise HTTPException(status_code=404, detail="Not found")
    session.delete(db_med)
    session.commit()
    return {"success": True}

class ChatRequest(BaseModel):
    query: str
    context: Optional[str] = None

@app.post("/api/chat")
def chat_endpoint(req: Request, chat_req: ChatRequest, session: Session = Depends(get_session)):
    api_key = req.headers.get('x-api-key')
    all_meds = session.exec(select(Medicine)).all()
    q = chat_req.query.lower()
    relevant = [m for m in all_meds if q in m.name.lower() or (m.use_case and q in m.use_case.lower())]
    if not relevant: relevant = list(islice((m for m in all_meds if m.quantity > 0), 15))
    
    lang = req.headers.get('x-lang', 'en')
    reply = get_ai_response(chat_req.query, relevant, api_key, lang)
    return {"success": True, "reply": reply}

# --- DB Initialization & Data Migration ---
def init_db():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        if session.exec(select(Medicine)).first() is None and DATA_FILE.exists():
            print("🚀 Migrating clinical registry from JSON to SQLite...")
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    for item in data:
                        # Map JSON fields to Medicine model
                        med_args = {
                            "id": str(item.get("id")),
                            "name": str(item.get("name")),
                            "strength": item.get("strength"),
                            "use_case": item.get("use_case"),
                            "category": item.get("category"),
                            "price": float(item.get("price", 0.0) or 0.0),
                            "quantity": int(item.get("quantity", 0) or 0),
                            "manufacturer": item.get("manufacturer"),
                            "expiry": item.get("expiry"),
                            "alternatives": item.get("alternatives"),
                            "dosage": item.get("dosage")
                        }
                        session.add(Medicine(**med_args))
                session.commit()
                print("✅ Migration complete.")
            except Exception as e:
                print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    init_db()
    import uvicorn
    print(f"🚀 MedPulse FastAPI Server running at http://localhost:{PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
