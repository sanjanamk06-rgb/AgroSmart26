# AI Risk Forecasting Module

## What it does
Takes a crop's detected disease/pest + severity (from the detection module) and a live 5-day weather forecast for the farm's location, and produces a daily risk score for the week ahead — not just a single number, but a trend.

## Approach: rule-based / knowledge-based — not ML/DL
This is a deliberate design choice, not a shortcut:
- No dataset linking historical weather to confirmed outbreaks exists for us to train against in this timeframe — training a model on synthetic or absent data would produce a number nobody could defend.
- Weather-driven risk scoring for plant disease is an established, accepted method in agricultural science (used operationally in real crop advisory systems), not something invented for this project.
- It's fully explainable: every risk score can be traced back to a specific, published weather threshold — useful for an extension officer who needs to trust *why* a farm is flagged, not just *that* it is.

## How the scoring works
1. Pull a 5-day weather forecast (OpenWeatherMap), aggregated from 3-hour intervals into daily averages (temp, humidity, rainfall).
2. Compare each day's weather against published risk thresholds for the detected disease (e.g., rice blast risk rises with humidity ≥85%, temp 20–28°C, sustained rainfall).
3. Weight the resulting score by the severity level from the detection module.
4. Return a 5-day risk series, the expected peak window, a plain-language spread forecast, and a preventive action recommendation.

## Output schema
```json
{
  "outbreak_risk_percent": 72,
  "risk_trend": { "direction": "rising", "daily": [ {"date": "...", "risk_percent": 0} ] },
  "expected_window": { "start": "...", "end": "..." },
  "spread_forecast": "...",
  "preventive_alert": "..."
}
```

## Validation
Since this is rule-based rather than trained, standard ML accuracy metrics (precision/recall/F1) don't apply — there's no model to score. What was validated instead:
- Tested against live weather API data (not mocked), confirmed to run end-to-end without errors.
- Verified across multiple locations to confirm scores respond correctly to different real weather conditions rather than returning a static number.
- Thresholds are sourced from published agro-meteorological research rather than arbitrary values.

## Status
- Core scoring logic: complete and tested standalone.
- Pending: final integration into the backend (format TBD — direct function import vs. dedicated endpoint), and syncing disease label strings once the detection module's final labels are locked.

## Scope
Currently covers Paddy — Rice Blast, with Brown Planthopper added if time permits before the round.
