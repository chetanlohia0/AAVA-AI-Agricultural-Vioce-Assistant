# backend/services/nlu_service.py

INTENT_KEYWORDS = {
    "weather_query": [
        "weather", "rain", "barish", "paus", "mausam", "hawaman", "मौसम", "बारिश",
        "पानी", "पाऊस", "हवामान", "वेदर"
    ],
    "trend_query": [
        "trend", "forecast", "future", "tomorrow", "kal", "agle", "next week",
        "badhega", "ghatega", "vadhel", "kami hoil", "रुझान", "अनुमान", "कल", "अगले",
        "भविष्य", "बढ़ेगा", "घटेगा", "रूझान"
    ],
    "price_query": [
        "price", "bhav", "rate", "daam", "keemat", "kitna", "प्राइस", "भाव", "दाम",
        "कीमत", "कितना", "दर", "रेट"
    ]
}

CROP_KEYWORDS = {
    "Cotton": ["cotton", "कपास", "कॉटन", "कपाशी"],
    "Wheat": ["wheat", "gehu", "gehun", "गेहूं", "गेहू", "गहू"],
    "Onion": ["onion", "pyaaz", "pyaj", "kanda", "प्याज", "प्याज़", "कांदा"],
    "Potato": ["potato", "aloo", "aalu", "batata", "आलू", "बटाटा"],
    "Tomato": ["tomato", "tamatar", "टमाटर", "टोमॅटो"]
}

ALL_STOPWORDS = {
    "weather", "rain", "barish", "paus", "mausam", "hawaman", "मौसम", "बारिश",
    "पानी", "पाऊस", "हवामान", "वेदर", "price", "bhav", "rate", "daam", "keemat",
    "kitna", "प्राइस", "भाव", "दाम", "कीमत", "कितना", "दर", "रेट", "trend", "forecast",
    "future", "tomorrow", "kal", "agle", "next", "week", "badhega", "ghatega",
    "रुझान", "अनुमान", "कल", "अगले", "भविष्य", "बढ़ेगा", "घटेगा", "रूझान",
    "ka", "ki", "ke", "kya", "hai", "hoga", "mein", "me", "in", "for", "at", "of",
    "का", "की", "के", "क्या", "है", "होगा", "में", "बताओ", "जानकारी", "अपडेट"
}

def detect_intent(text: str) -> str:
    text_lower = (text or "").lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return intent
    return "unknown"

def extract_crop(text: str) -> str | None:
    text_lower = (text or "").lower()
    for canonical_name, aliases in CROP_KEYWORDS.items():
        if any(alias in text_lower for alias in aliases):
            return canonical_name
    return None

def extract_location(text: str) -> str | None:
    """Extracts location tokens by filtering out intent words, crops, and filler words."""
    if not text:
        return None
    
    words = text.replace("?", "").replace(",", "").split()
    all_crop_aliases = {alias.lower() for aliases in CROP_KEYWORDS.values() for alias in aliases}
    
    location_tokens = []
    for w in words:
        w_clean = w.strip().lower()
        if w_clean not in ALL_STOPWORDS and w_clean not in all_crop_aliases and len(w_clean) > 1:
            location_tokens.append(w.strip())
    
    if location_tokens:
        return " ".join(location_tokens).title()
    return None

RESPONSES = {
    "en": {
        "price": "The current price of {crop} in {market} is {price} rupees per quintal.",
        "trend": "{crop} price is expected to be {trend} over the next day, around {predicted} rupees per quintal.",
        "weather": "Weather update for {location}: {condition}, temperature {temp}°C.",
        "no_crop": "Sorry, I could not identify the crop name. Please mention wheat, cotton, onion, potato, or tomato.",
        "unknown": "Sorry, I did not understand your question. You can ask about crop price, trend, or weather."
    },
    "hi": {
        "price": "{market} में {crop} का वर्तमान भाव ₹{price} प्रति क्विंटल है।",
        "trend": "अगले दिन {crop} का भाव {trend} रहने की संभावना है, लगभग ₹{predicted} प्रति क्विंटल।",
        "weather": "{location} के लिए मौसम का अपडेट: {condition}, तापमान {temp}°C।",
        "no_crop": "क्षमा करें, मैं फसल की पहचान नहीं कर सका। कृपया गेहूं, कॉटन, प्याज, आलू या टमाटर का नाम कहें।",
        "unknown": "क्षमा करें, मैं आपका प्रश्न समझ नहीं पाया। आप भाव, भाव का रुझान, या मौसम के बारे में पूछ सकते हैं।"
    },
    "mr": {
        "price": "{market} बाजारात {crop} चा दर ₹{price} प्रति क्विंटल आहे.",
        "trend": "पुढील दिवशी {crop} चा दर {trend} राहण्याची शक्यता आहे, सुमारे ₹{predicted} प्रति क्विंटल.",
        "weather": "{location} हवामान अंदाज: {condition}, तापमान {temp}°C.",
        "no_crop": "माफ करा, मी पिकाचे नाव ओळखू शकलो नाही.",
        "unknown": "माफ करा, मला तुमचा प्रश्न समजला नाही."
    }
}

TREND_WORD = {
    "en": {"rising": "rising", "falling": "falling", "stable": "stable"},
    "hi": {"rising": "बढ़ने", "falling": "घटने", "stable": "स्थिर"},
    "mr": {"rising": "वाढणारा", "falling": "कमी होणारा", "stable": "स्थिर"}
}

def build_response(lang="hi", intent="unknown", crop=None, market=None, price=None, prediction=None, weather=None, history_len=None) -> str:
    lang = lang if lang in RESPONSES else "hi"
    templates = RESPONSES[lang]

    if intent == "weather_query":
        if not weather:
            return "मौसम की जानकारी उपलब्ध नहीं है।"
        return templates["weather"].format(
            location=weather.get("location", "आपके क्षेत्र"),
            condition=weather.get("condition", "सामान्य"),
            temp=weather.get("temp_c", 28)
        )

    if intent == "price_query":
        if not crop:
            return templates["no_crop"]
        return templates["price"].format(crop=crop, market=market or "मंडी", price=price or 2400)

    if intent == "trend_query":
        if not crop or not prediction:
            return templates["no_crop"]
        trend_w = TREND_WORD[lang].get(prediction.trend, prediction.trend)
        return templates["trend"].format(crop=crop, trend=trend_w, predicted=prediction.predicted_next_price)

    return templates["unknown"]