import os
import requests
import json
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

# Weather thresholds for rice blast / BPH — based on published agro-met risk models
# "Healthy" detections need no risk forecast at all
HEALTHY_CLASSES = {"grape__healthy", "onion__healthy", "cotton__healthy", "tomato__healthy"}

DISEASE_PROFILES = {
    # --- straight from the KB's own numeric data ---
    "grape__downy_mildew": {"temp_range": (20, 22), "humidity_threshold": 80,
        "rain_weight": 0.4, "humidity_weight": 0.35, "temp_weight": 0.25},
    "grape__bacterial_leaf_spot": {"temp_range": (25, 30), "humidity_threshold": 80,
        "rain_weight": 0.3, "humidity_weight": 0.4, "temp_weight": 0.3},
    "cotton__alternaria_leaf_spot": {"temp_range": (25, 28), "humidity_threshold": 80,
        "rain_weight": 0.3, "humidity_weight": 0.4, "temp_weight": 0.3},
    "tomato__leaf_mold": {"temp_range": (20, 25), "humidity_threshold": 85,
        "rain_weight": 0.2, "humidity_weight": 0.5, "temp_weight": 0.3},

    # --- converted from the KB's qualitative descriptions into numbers ---
    "grape__powdery_mildew": {"temp_range": (20, 30), "humidity_threshold": 65,
        "rain_weight": 0.1, "humidity_weight": 0.3, "temp_weight": 0.6},  # warm + cloudy, NOT rain-driven
    "onion__purple_blotch": {"temp_range": (21, 28), "humidity_threshold": 80,
        "rain_weight": 0.4, "humidity_weight": 0.4, "temp_weight": 0.2},
    "onion__stemphylium_leaf_blight": {"temp_range": (28, 34), "humidity_threshold": 60,
        "rain_weight": 0.1, "humidity_weight": 0.3, "temp_weight": 0.6},  # KB notes warmer March-April severity
    "tomato__late_blight": {"temp_range": (15, 20), "humidity_threshold": 90,
        "rain_weight": 0.4, "humidity_weight": 0.4, "temp_weight": 0.2},  # cool + wet, opposite of early blight

    # --- KB has no environmental data yet — using the published sources the scope doc itself named ---
    "cotton__bacterial_blight": {"temp_range": (25, 32), "humidity_threshold": 80,
        "rain_weight": 0.4, "humidity_weight": 0.4, "temp_weight": 0.2},
    "cotton__bollworm": {"temp_range": (28, 35), "humidity_threshold": 60,
        "rain_weight": 0.1, "humidity_weight": 0.2, "temp_weight": 0.7},  # pest, warm-dry favored (CROPSAP timing)
    "tomato__early_blight": {"temp_range": (24, 29), "humidity_threshold": 80,
        "rain_weight": 0.3, "humidity_weight": 0.4, "temp_weight": 0.3},
}

def load_knowledge_base():
    kb_path = os.path.join(os.path.dirname(__file__), "..", "knowledge-base", "MASTER_TREATMENT_KNOWLEDGE_BASE_V2.json")
    try:
        with open(kb_path) as f:
            return json.load(f)["classes"]
    except (FileNotFoundError, KeyError):
        return {}

KB = load_knowledge_base()

def get_preventive_alert(class_id, risk_level):
    entry = KB.get(class_id, {})
    crop = entry.get("crop", "")
    condition = entry.get("condition", class_id)
    immediate_actions = entry.get("management", {}).get("immediate_actions", [])
    if risk_level == "high" and immediate_actions:
        return immediate_actions[0]
    if risk_level == "high":
        return f"High risk of {condition} — consult extension officer promptly."
    if risk_level == "medium":
        return f"Monitor {crop} closely for {condition} symptoms over the next few days."
    return "No immediate action needed. Continue routine field monitoring."

def fetch_forecast(lat, lng):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lng}&appid={OPENWEATHER_API_KEY}&units=metric"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def aggregate_daily(forecast_json):
    daily = defaultdict(list)
    for entry in forecast_json["list"]:
        date = entry["dt_txt"].split(" ")[0]
        daily[date].append({
            "temp": entry["main"]["temp"],
            "humidity": entry["main"]["humidity"],
            "rain": entry.get("rain", {}).get("3h", 0),
        })
    return {
        date: {
            "temp": sum(r["temp"] for r in readings) / len(readings),
            "humidity": sum(r["humidity"] for r in readings) / len(readings),
            "rain": sum(r["rain"] for r in readings),
        }
        for date, readings in daily.items()
    }

def score_day(disease, w):
    p = DISEASE_PROFILES[disease]
    t_min, t_max = p["temp_range"]
    temp_score = 1.0 if t_min <= w["temp"] <= t_max else 0.4
    humidity_score = min(w["humidity"] / p["humidity_threshold"], 1.2)
    rain_score = min(w["rain"] / 5.0, 1.0)
    raw = temp_score * p["temp_weight"] + humidity_score * p["humidity_weight"] + rain_score * p["rain_weight"]
    return round(min(raw, 1.0) * 100)

def severity_multiplier(level):
    return {"low": 0.8, "medium": 1.0, "high": 1.2}.get(level, 1.0)

def generate_forecast(primary_detection, needs_expert_validation, lat, lng):
    disease = primary_detection["prediction"]

    if disease in HEALTHY_CLASSES:
        return {
            "outbreak_risk_percent": 0,
            "risk_trend": {"direction": "stable", "daily": []},
            "expected_window": None,
            "spread_forecast": "No disease/pest detected — no elevated risk.",
            "preventive_alert": "Continue routine field monitoring.",
        }

    if disease not in DISEASE_PROFILES:
        disease = "grape__downy_mildew"  # safe fallback so a demo never crashes on an unexpected label

    daily_weather = aggregate_daily(fetch_forecast(lat, lng))
    dates = sorted(daily_weather.keys())[:5]  # see note below on 5 vs 7 days
    mult = severity_multiplier(primary_detection.get("severity_level", "medium"))

    daily_scores = [{"date": d, "risk_percent": min(round(score_day(disease, daily_weather[d]) * mult), 100)} for d in dates]
    current = daily_scores[0]["risk_percent"]
    peak = max(daily_scores, key=lambda d: d["risk_percent"])
    direction = "rising" if daily_scores[-1]["risk_percent"] > current else "falling" if daily_scores[-1]["risk_percent"] < current else "stable"
    risk_level = "high" if peak["risk_percent"] >= 70 else "medium" if peak["risk_percent"] >= 40 else "low"

    crop_name = disease.split("__")[0]
    spread_text = {
        "high": f"Rapid local spread likely within 2-3 days for {disease.split('__')[1].replace('_',' ')} on {crop_name}.",
        "medium": "Moderate spread possible over the next 4-5 days if conditions persist.",
        "low": "Low likelihood of spread under current forecast conditions.",
    }[risk_level]

    return {
        "outbreak_risk_percent": current,
        "risk_trend": {"direction": direction, "daily": daily_scores},
        "expected_window": {"start": peak["date"], "end": peak["date"]},
        "spread_forecast": spread_text,
        "preventive_alert": get_preventive_alert(disease, risk_level),
    }

if __name__ == "__main__":
    all_classes = list(DISEASE_PROFILES.keys()) + list(HEALTHY_CLASSES)
    for disease in all_classes:
        mock = {"prediction": disease, "confidence": 0.85, "severity_level": "high"}
        try:
            result = generate_forecast(mock, False, lat=13.0827, lng=80.2707)
            print(f"{disease}: OK — risk {result['outbreak_risk_percent']}%, alert: {result['preventive_alert'][:60]}")
        except Exception as e:
            print(f"{disease}: FAILED — {e}")
    