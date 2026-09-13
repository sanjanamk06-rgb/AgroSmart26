import os
import requests
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

# Weather thresholds for rice blast / BPH — based on published agro-met risk models
DISEASE_PROFILES = {
    "rice_blast": {"temp_range": (20, 28), "humidity_threshold": 85,
                    "rain_weight": 0.3, "humidity_weight": 0.4, "temp_weight": 0.3},
    "brown_planthopper": {"temp_range": (25, 32), "humidity_threshold": 80,
                    "rain_weight": 0.2, "humidity_weight": 0.5, "temp_weight": 0.3},
}

PREVENTIVE_ALERTS = {
    ("rice_blast", "high"): "Apply preventive fungicide (e.g., Tricyclazole) within 48 hours. Avoid excess nitrogen application.",
    ("rice_blast", "medium"): "Monitor leaves closely for lesions over next 3-4 days; keep field drained if possible.",
    ("rice_blast", "low"): "No immediate action needed. Continue routine field monitoring.",
    ("brown_planthopper", "high"): "Inspect plant base for hoppers; apply recommended insecticide if population exceeds threshold.",
    ("brown_planthopper", "medium"): "Increase monitoring frequency at plant base; avoid dense planting.",
    ("brown_planthopper", "low"): "No immediate action needed.",
}

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
    if disease not in DISEASE_PROFILES:
        disease = "rice_blast"  # safe fallback so the demo never crashes

    daily_weather = aggregate_daily(fetch_forecast(lat, lng))
    dates = sorted(daily_weather.keys())[:5]
    mult = severity_multiplier(primary_detection.get("severity_level", "medium"))

    daily_scores = [{"date": d, "risk_percent": min(round(score_day(disease, daily_weather[d]) * mult), 100)} for d in dates]
    current = daily_scores[0]["risk_percent"]
    peak = max(daily_scores, key=lambda d: d["risk_percent"])
    direction = "rising" if daily_scores[-1]["risk_percent"] > current else "falling" if daily_scores[-1]["risk_percent"] < current else "stable"
    risk_level = "high" if peak["risk_percent"] >= 70 else "medium" if peak["risk_percent"] >= 40 else "low"

    spread_text = {
        "high": f"Rapid local spread likely within 2-3 days due to favorable conditions for {disease.replace('_',' ')}.",
        "medium": "Moderate spread possible over the next 4-5 days if conditions persist.",
        "low": "Low likelihood of spread under current forecast conditions.",
    }[risk_level]

    return {
        "outbreak_risk_percent": current,
        "risk_trend": {"direction": direction, "daily": daily_scores},
        "expected_window": {"start": peak["date"], "end": peak["date"]},
        "spread_forecast": spread_text,
        "preventive_alert": PREVENTIVE_ALERTS.get((disease, risk_level), "Consult extension officer for guidance."),
    }

if __name__ == "__main__":
    import json
    mock_detection = {"prediction": "rice_blast", "confidence": 0.88, "severity_level": "high"}
    print(json.dumps(generate_forecast(mock_detection, False, lat=13.0827, lng=80.2707), indent=2))