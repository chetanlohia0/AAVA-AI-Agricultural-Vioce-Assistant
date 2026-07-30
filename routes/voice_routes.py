# backend/routes/voice_routes.py
import io
from flask import Blueprint, request, jsonify, render_template, send_file
from gtts import gTTS
from services import market_service, weather_service, nlu_service
from services.gemini_service import GeminiService
from algorithms.price_predictor import predict_price_trend

voice_bp = Blueprint("voice", __name__)

def handle_query(text: str, lang: str = "hi") -> str:
    """Core AI Pipeline."""
    gemini = GeminiService()

    # 1. Gemini NLU Extraction
    parsed = gemini.extract_intent_and_entities(text)
    
    if parsed and parsed.get("intent") in ("price_query", "trend_query", "weather_query"):
        intent = parsed["intent"]
        crop = parsed.get("crop")
        location = parsed.get("location") or "Indore"
    else:
        intent = nlu_service.detect_intent(text)
        crop = nlu_service.extract_crop(text) if intent in ("price_query", "trend_query") else None
        location = "Indore"

    print(f"🤖 [AI Extraction] -> Intent: {intent} | Crop: {crop} | Location: {location}")

    # 2. Data Fetching & Answer Synthesis
    if intent == "weather_query":
        weather_data = weather_service.get_weather(location)
        fact_payload = {"intent": "weather_query", "location": location, "weather": weather_data}
        spoken_response = gemini.synthesize_response(lang, fact_payload)
        return spoken_response or nlu_service.build_response(lang, intent, weather=weather_data)

    if intent in ("price_query", "trend_query") and not crop:
        return nlu_service.build_response(lang, intent, crop=None)

    market_data = market_service.get_market_data(crop, location)
    market_name = market_data["market"]
    current_price = market_data["current_price"]

    if intent == "price_query":
        fact_payload = {
            "intent": "price_query",
            "crop": crop,
            "location": market_name,
            "market": market_name,
            "price_inr": current_price
        }
        spoken_response = gemini.synthesize_response(lang, fact_payload)
        return spoken_response or nlu_service.build_response(lang, intent, crop=crop, market=market_name, price=current_price)

    if intent == "trend_query":
        history = market_data["history"]
        prediction = predict_price_trend(history)
        fact_payload = {
            "intent": "trend_query",
            "crop": crop,
            "location": market_name,
            "market": market_name,
            "predicted_next_price": prediction.predicted_next_price,
            "trend": prediction.trend,
            "confidence": prediction.confidence
        }
        spoken_response = gemini.synthesize_response(lang, fact_payload)
        return spoken_response or nlu_service.build_response(lang, intent, crop=crop, prediction=prediction, history_len=len(history))

    return nlu_service.build_response(lang, "unknown")


@voice_bp.route("/", methods=["GET"])
def dashboard():
    return render_template("index.html")

@voice_bp.route("/demo/query", methods=["POST"])
def demo_query():
    payload = request.get_json(force=True)
    text = payload.get("text", "")
    lang = payload.get("lang", "hi")

    reply_text = handle_query(text, lang=lang)
    return jsonify({"response": reply_text})

@voice_bp.route("/api/tts", methods=["GET"])
def text_to_speech():
    text = request.args.get("text", "")
    lang = request.args.get("lang", "hi")
    lang_code = "hi" if lang == "hi" else ("mr" if lang == "mr" else "en")
    
    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return send_file(fp, mimetype="audio/mpeg")
    except Exception as e:
        return str(e), 500