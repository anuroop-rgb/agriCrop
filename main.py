from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import json
import urllib.request
import numpy as np
from PIL import Image
import io
import random  # Added for dynamic crop simulation
from sklearn.ensemble import RandomForestRegressor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core training array for soil moisture engine
X_train = np.array([[35, 20, 0], [22, 80, 50], [28, 50, 10], [40, 15, 0], [15, 90, 100]])
y_train = np.array([12.5, 78.2, 42.0, 5.1, 95.0])

moisture_model = RandomForestRegressor(n_estimators=10, random_state=42)
moisture_model.fit(X_train, y_train)

# NO TENSORFLOW NEEDED: This function randomly simulates multiple crop diagnoses
def predict_leaf_disease(image_bytes: bytes) -> tuple:
    # A rich database of crop profiles for your presentation
    CROP_DIAGNOSES = [
        ("Tomato Late Blight", "High"),
        ("Healthy Tomato Leaf", "Low"),
        ("Corn Common Rust", "High"),
        ("Healthy Corn Crop", "Low"),
        ("Apple Scab", "Medium"),
        ("Cedar Apple Rust", "High"),
        ("Potato Early Blight", "High"),
        ("Healthy Rice Leaf", "Low")
    ]
    # Picks a completely random crop condition every time you upload an image
    return random.choice(CROP_DIAGNOSES)

def fetch_live_weather(lat: float, lon: float):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,rain&timezone=auto"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        current = data["current"]
        return {"temp": float(current["temperature_2m"]), "humidity": float(current["relative_humidity_2m"]), "rain": float(current["rain"])}
    except Exception:
        return {"temp": 26.5, "humidity": 55.0, "rain": 0.0}

@app.post("/api/reports")
async def generate_automated_report(
    latitude: float = Form(...),
    longitude: float = Form(...),
    image: UploadFile = File(...)
):
    weather = fetch_live_weather(latitude, longitude)
    predicted_moisture = float(moisture_model.predict([[weather["temp"], weather["humidity"], weather["rain"]]])[0])
    disease_name, disease_severity = predict_leaf_disease(await image.read())
    
    # DYNAMIC RECOMMENDATION ALGORITHM BASED ON CURRENT SELECTED CROP
    suggestion = "Crop ecosystem looks stable. Maintain regular field observation and moisture cycles."
    final_severity = disease_severity

    if "Blight" in disease_name:
        if weather["humidity"] > 70.0:
            final_severity = "Critical"
            suggestion = f"⚠️ HIGH HUMIDITY THREAT: {disease_name} spreads aggressively above 70% humidity. Crop protection required: Prune infected leaves immediately and apply copper fungicide."
        else:
            suggestion = f"Notice: {disease_name} detected. Isolate affected plot sections and maximize row spacing layout to encourage wind drying lines."
            
    elif "Rust" in disease_name or "Scab" in disease_name:
        suggestion = f"Fungal footprint observed ({disease_name}). Avoid excessive nitrogen fertilization which fuels scaling. Apply organic sulfur spray treatments in early morning."

    elif "Healthy" in disease_name:
        suggestion = f"Excellent! The {disease_name} indicates strong cellular resilience. Continue current soil nutrient program."

    if predicted_moisture < 20.0:
        suggestion += " 🚜 DROUGHT ALERT: Predicted soil profile moisture has fallen below 20%. Active drip irrigation lines now."

    return {
        "disease_name": disease_name,
        "severity": final_severity,
        "latitude": latitude,
        "longitude": longitude,
        "temperature": weather["temp"],
        "humidity": weather["humidity"],
        "rainfall": weather["rain"],
        "soil_moisture": round(predicted_moisture, 1),
        "betterment_suggestion": suggestion
    }

@app.delete("/api/reports/clear")
def clear_database():
    return {"message": "Reset"}

@app.get("/", response_class=HTMLResponse)
def read_dashboard():
    html_path = Path(__file__).with_name("index..html")
    if not html_path.exists():
        html_path = Path(__file__).with_name("index.html")
    return html_path.read_text(encoding="utf-8")
    
    


    
    