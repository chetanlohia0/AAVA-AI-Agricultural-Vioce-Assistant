"""
services/nlu_service.py

Lightweight rule-based Natural Language Understanding for the voice
assistant. Speech-to-text (via Twilio's <Gather input="speech">, which
itself uses Google's ASR under the hood) converts the farmer's spoken
regional-language question into text. This module then:

  1. Detects intent: does the farmer want a live price, a price
     trend/forecast, or a weather update?
  2. Extracts the crop name mentioned (fuzzy-matched to handle ASR
     noise), delegated to market_service.resolve_crop_name.
  3. Builds a natural-language response in the farmer's language.

A keyword-based approach (rather than a trained classifier) was
chosen deliberately: the intent space for this assistant is small and
well-defined (price / trend / weather / help), Hindi/Marathi/English
keyword sets are easy to enumerate and extend, and it requires zero
training data or model hosting - important for a low-cost rural
telephony deployment where every added service is added latency.
"""

from services import market_service

INTENT_KEYWORDS = {
    "trend_query": [
        "trend", "forecast", "future", "tomorrow", "kal", "agle", "next week",
        "badhega", "ghatega", "vadhel", "kami hoil",
    ],
    "price_query": [
        "price", "bhav", "rate", "daam", "keemat", "kitna", "किंमत", "भाव",
    ],
    "weather_query": [
        "weather", "rain", "barish", "paus", "mausam", "hawaman", "बारिश", "पाऊस",
    ],
}


def detect_intent(text: str) -> str:
    text_lower = (text or "").lower()
    # Trend is checked before price since a trend question often
    # also contains the word "price" (e.g. "what will onion price be tomorrow").
    for intent in ["trend_query", "weather_query", "price_query"]:
        if any(kw in text_lower for kw in INTENT_KEYWORDS[intent]):
            return intent
    return "unknown"


# Words that must never be treated as crop-name candidates, because
# they are either intent keywords (e.g. "price" fuzzy-matches "Rice"
# closely enough to cause false positives) or common filler words in
# English/Hindi/Marathi queries.
_ALL_INTENT_KEYWORDS = {kw.lower() for kws in INTENT_KEYWORDS.values() for kw in kws}
_STOPWORDS = _ALL_INTENT_KEYWORDS | {
    "of", "the", "is", "what", "will", "be", "a", "an", "for",
    "ka", "ki", "ke", "kya", "hai", "hoga", "kitna", "mein", "baare",
    "cha", "chi", "che", "aahe", "sathi",
}


def extract_crop(text: str):
    """
    Naive token-based extraction: try each word/phrase in the
    transcript against the known crop list via fuzzy matching, after
    filtering out intent keywords and filler words that could
    otherwise false-positive match a crop name (e.g. "price" is a
    close fuzzy match to "Rice").
    """
    words = (text or "").replace(",", " ").split()
    filtered = [w for w in words if w.lower() not in _STOPWORDS and len(w) >= 3]
    candidates = filtered + [" ".join(filtered[i:i + 2]) for i in range(len(filtered) - 1)]
    for candidate in candidates:
        match = market_service.resolve_crop_name(candidate)
        if match:
            return match
    return None


# --- Multilingual response templates -------------------------------------

RESPONSES = {
    "en": {
        "price": "The current price of {crop} in {market} mandi is {price} rupees per quintal.",
        "trend": "{crop} price is expected to be {trend} over the next day, around {predicted} rupees "
                 "per quintal, based on the last {days} days of data. Confidence: {confidence}.",
        "weather": "Weather update for {location}: {condition}, temperature {temp}°C, "
                   "{rain}% chance of rain.",
        "no_crop": "Sorry, I could not identify the crop name. Please say the crop name clearly, "
                   "for example 'onion' or 'wheat'.",
        "unknown": "Sorry, I did not understand your question. You can ask about crop price, "
                   "price trend, or weather.",
    },
    "hi": {
        "price": "{market} मंडी में {crop} का वर्तमान भाव {price} रुपये प्रति क्विंटल है।",
        "trend": "पिछले {days} दिनों के आंकड़ों के आधार पर, {crop} का भाव अगले दिन {trend} रहने की उम्मीद है, "
                 "लगभग {predicted} रुपये प्रति क्विंटल। विश्वसनीयता: {confidence}।",
        "weather": "{location} के लिए मौसम अपडेट: {condition}, तापमान {temp} डिग्री सेल्सियस, "
                   "बारिश की संभावना {rain}%।",
        "no_crop": "क्षमा करें, मैं फसल का नाम समझ नहीं पाया। कृपया फिर से फसल का नाम बताएं।",
        "unknown": "क्षमा करें, मैं आपका प्रश्न समझ नहीं पाया। आप भाव, भाव का रुझान, या मौसम के बारे में पूछ सकते हैं।",
    },
    "mr": {
        "price": "{market} बाजारात {crop} चा सध्याचा भाव {price} रुपये प्रति क्विंटल आहे.",
        "trend": "गेल्या {days} दिवसांच्या माहितीनुसार, {crop} चा भाव पुढील दिवशी {trend} राहण्याची शक्यता आहे, "
                 "अंदाजे {predicted} रुपये प्रति क्विंटल. विश्वासार्हता: {confidence}.",
        "weather": "{location} साठी हवामान अपडेट: {condition}, तापमान {temp}°C, "
                   "पावसाची शक्यता {rain}%.",
        "no_crop": "माफ करा, मला पिकाचे नाव समजले नाही. कृपया पुन्हा पिकाचे नाव सांगा.",
        "unknown": "माफ करा, मला तुमचा प्रश्न समजला नाही. तुम्ही भाव, भावाचा कल किंवा हवामानाबद्दल विचारू शकता.",
    },
}

TREND_WORD = {
    "en": {"rising": "rising", "falling": "falling", "stable": "stable"},
    "hi": {"rising": "बढ़ता हुआ", "falling": "घटता हुआ", "stable": "स्थिर"},
    "mr": {"rising": "वाढता", "falling": "कमी होणारा", "stable": "स्थिर"},
}


def build_response(lang: str, intent: str, crop: str = None, market: str = None,
                    price: float = None, prediction=None, weather: dict = None,
                    history_len: int = None) -> str:
    lang = lang if lang in RESPONSES else "en"
    templates = RESPONSES[lang]

    if intent == "price_query":
        if not crop:
            return templates["no_crop"]
        return templates["price"].format(crop=crop, market=market, price=price)

    if intent == "trend_query":
        if not crop:
            return templates["no_crop"]
        trend_word = TREND_WORD[lang][prediction.trend]
        return templates["trend"].format(
            crop=crop, trend=trend_word, predicted=prediction.predicted_next_price,
            days=history_len, confidence=prediction.confidence,
        )

    if intent == "weather_query":
        return templates["weather"].format(
            location=weather["location"], condition=weather["condition"],
            temp=weather["temp_c"], rain=weather["rain_probability_pct"],
        )

    return templates["unknown"]
