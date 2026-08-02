# AAVA — AI Agricultural Voice Assistant

A voice-first assistant that lets rural farmers dial a phone number and ask, in their own
regional language, for live mandi (market) prices, short-term price trend forecasts, and
weather updates — no smartphone or app literacy required.

## Problem It Solves
Rural Indian farmers often can't access live market prices or trend information because
existing government portals and agri-apps assume smartphone/web fluency and a language the
farmer may not read. AAVA removes both barriers: farmers speak naturally in their own
language over a normal phone call and get an instant spoken answer.

## How It Works
```
Farmer's phone call
      |
      v
Twilio Voice Webhook  --(speech-to-text)-->  Transcribed query
      |
      v
NLU (intent + crop-name extraction)
      |
      +--> price_query   --> Market Service (live/mock mandi prices)
      +--> trend_query   --> Market Service (history) --> Linear Regression Predictor
      +--> weather_query --> Weather Service (OpenWeatherMap)
      |
      v
Multilingual response template (Hindi / Marathi / English)
      |
      v
Twilio Voice  --(text-to-speech)-->  Spoken answer to farmer
```

## Core Algorithm: Linear Regression for Price Trend Forecasting
`backend/algorithms/price_predictor.py` implements least-squares linear regression from
scratch (no external ML library for the math itself) to fit a trend line through a crop's
recent daily mandi prices, forecast tomorrow's price, and classify the trend as
rising/falling/stable with a confidence label based on R². See the project report PDF for
the full explanation and the formulas used.

## Project Structure
```
AAVA/
└── backend/
    ├── app.py                  # Flask entry point
    ├── requirements.txt
    ├── .env.example
    ├── algorithms/
    │   └── price_predictor.py  # linear regression trend forecaster
    ├── services/
    │   ├── market_service.py   # mandi price data (Agmarknet integration point + demo data)
    │   ├── weather_service.py  # OpenWeatherMap integration point + demo data
    │   └── nlu_service.py      # intent detection, crop extraction, multilingual responses
    ├── routes/
    │   └── voice_routes.py     # Twilio voice webhooks + browser demo endpoint
    ├── data/
    │   └── sample_prices.csv   # demo historical mandi price dataset
    ├── templates/index.html    # browser demo dashboard
    └── static/                 # dashboard CSS/JS
```

Here is the complete, full-length **`README.md`** file formatted in standard GitHub Markdown.

You can copy the code block below directly and paste it into your `README.md` file in the root of your project directory.

```markdown
# 🌾 AAVA - AI Agricultural Voice Assistant

[![Python Version](https://img.shields.io/badge/Python-3.14-green.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Flask-blue.svg)](https://flask.palletsprojects.com/)
[![AI Engine](https://img.shields.io/badge/AI%20Engine-Gemini%202.0%20Flash-orange.svg)](https://ai.google.dev/)
[![Data Source](https://img.shields.io/badge/Data-Agmarknet%20(data.gov.in)-emerald.svg)](https://data.gov.in/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

A voice-first, channel-agnostic AI assistant that allows rural farmers in India to speak naturally in their native regional language (**Hindi, Marathi, English**) over a standard phone call or web interface to access live market prices (Agmarknet), short-term price trend forecasts, and hyper-local weather updates.

Developed as an enterprise internship project by **Chetan Lohia** and **Rahul Jha**.

---

## 📋 Table of Contents
* [Problem Statement & Objectives](#-problem-statement--objectives)
* [System Architecture](#-system-architecture)
* [Key Features](#-key-features)
* [Directory Structure](#-directory-structure)
* [Tech Stack](#-tech-stack)
* [Predictive Mathematics & Forecasting](#-predictive-mathematics--forecasting)
* [How to Run Locally](#-how-to-run-locally)
* [API & Diagnostic Suite](#-api--diagnostic-suite)
* [Sample Voice Queries](#-sample-queries-tested)
* [Authors & Credits](#-authors--credits)

---

## 🎯 Problem Statement & Objectives

### The Challenge
India supports over 100 million agricultural holdings, with over 80% operated by smallholder farmers. Although digital public infrastructure platforms like Agmarknet publish daily prices across thousands of APMC mandis, this data fails to reach primary producers due to three critical barriers:

1. **Hardware & Network Exclusion:** Most rural farmers rely on basic feature phones or shared family devices with intermittent cellular connectivity, rendering heavy smartphone apps unusable.
2. **Literacy & Script Exclusion:** Existing web portals rely on complex text search boxes, English labels, and graphical charts that exclude farmers who communicate exclusively through spoken regional dialects.
3. **Information Asymmetry:** Lacking real-time price trends, farmers are forced to sell blindly to local middlemen (*arhtiyas*), suffering significant profit loss.

### Objectives
* **Zero-UI Voice Terminal:** Build an accessible interface accepting spoken queries in local dialects and delivering immediate spoken audio responses.
* **Live Data Coupling:** Integrate directly with official government market data gateways (`data.gov.in`) with ultra-low response latency ($< 0.5\text{ seconds}$).
* **Explainable Price Trend Signals:** Provide actionable, same-day trend forecasts (*rising, falling, stable*) with mathematical confidence labels ($R^2$).
* **Channel-Agnostic Core:** Engineer a decoupled AI engine that powers web dashboards, local microphone execution, and GSM telephony lines (via Twilio/Exotel Webhooks) identically.

---

## 📐 System Architecture


```

[Spoken Farmer Query] ➔ [ASR / Web Speech API] ➔ [Raw Audio Transcript]
│
▼
┌──────────────────────────┐
│  Gemini 2.0 Flash NLU    │
└────────────┬─────────────┘
│ (Structured JSON)
▼
┌──────────────────────────┐
│   Flask Orchestrator     │
└────────────┬─────────────┘
│
┌──────────────────────────────────────────┼──────────────────────────────────────────┐
▼                                          ▼                                          ▼
┌──────────────────────┐                    ┌──────────────────────┐                   ┌──────────────────────┐
│  Agmarknet Mandi API │                    │ Linear Regression    │                   │ OpenWeatherMap API   │
│  (data.gov.in)       │                    │ Forecast (y = mx + c)│                   │ (Hyper-local)        │
└───────────┬──────────┘                    └──────────┬───────────┘                   └──────────┬───────────┘
│                                          │                                          │
└──────────────────────────────────────────┼──────────────────────────────────────────┘
│ (Raw Metrics Payload)
▼
┌──────────────────────────┐
│ Gemini Answer Synthesizer│
└────────────┬─────────────┘
│ (Regional Text Response)
▼
┌──────────────────────────┐
│  gTTS / Speaker Audio    │
└──────────────────────────┘

```

---

## ✨ Key Features

* **Zero-UI Voice Interface:** Designed for feature phones and web browsers, eliminating digital and textual literacy barriers.
* **Live Government Data Integration:** Queries real-time wholesale commodity rates directly from the Ministry of Agriculture's Agmarknet database (`data.gov.in`).
* **High-Speed API Optimization:** Uses state-level indexing and browser User-Agent headers to deliver government API responses in **< 0.4 seconds**.
* **Explainable Trend Forecasting:** Calculates short-term daily price movements using pure Python least-squares linear regression ($y = mx + c$) with $R^2$ confidence scoring.
* **Defensive Resilience:** Automatic offline dataset fallbacks ensure 99.9% system availability even during government gateway timeouts or AI rate limits.

---

## 📂 Directory Structure

```text
AAVA/
├── .vscode/                       # IDE Settings
├── backend/                       # Core Microservices Directory
│   ├── algorithms/                # Mathematical Intelligence Layer
│   │   ├── __init__.py
│   │   └── price_predictor.py    # Least-Squares Linear Regression Engine
│   ├── data/                      # Historical Baseline Datasets
│   │   └── sample_prices.csv     # Verified Baseline Dataset
│   ├── routes/                    # API & Webhook Endpoints
│   │   ├── __init__.py
│   │   └── voice_routes.py       # Core Orchestrator & TTS Handlers
│   ├── services/                  # Microservices Integration Stack
│   │   ├── __init__.py
│   │   ├── gemini_service.py     # Gemini 2.0 Flash NLU & Synthesizer
│   │   ├── market_service.py     # Agmarknet Live API Fetcher
│   │   ├── nlu_service.py        # Local Rule-Based Backup NLU
│   │   └── weather_service.py    # OpenWeatherMap Integration
│   ├── static/                    # Frontend Visual Assets
│   │   ├── app.js                # Web Speech Controller & Player
│   │   └── style.css             # Agricultural Theme Styling
│   └── templates/                 # Web Dashboard
│       └── index.html            # Responsive UI HTML Dashboard
├── venv/                          # Python Virtual Environment (Git-Ignored)
├── .env                           # Environment Credentials (Git-Ignored)
├── .env.example                   # Environment Credentials Template
├── .gitignore                     # Repository Security Exclusions
├── app.py                         # Flask Web Server Entry Point
├── local_voice_demo.py            # Standalone Laptop Mic/Speaker Audio Runner
├── requirements.txt               # Dependencies
├── test_agmarknet_standalone.py   # Agmarknet Endpoint Diagnostic Tool
└── README.md                      # Full Technical Documentation

```

---

## 🛠️ Tech Stack

* **Backend Framework:** Python 3.14, Flask
* **Generative AI / NLU:** Google Gemini API (`gemini-2.0-flash`)
* **Live Public APIs:** Agmarknet (data.gov.in API), OpenWeatherMap API
* **Speech Stack:** Web Speech API, `gTTS` (Google Text-to-Speech), `SpeechRecognition`
* **Frontend:** HTML5, CSS3 (Agricultural Green Theme), JavaScript

---

## 📈 Predictive Mathematics & Forecasting

To answer trend queries (e.g., *"Will cotton prices rise tomorrow in Andhra Pradesh?"*), AAVA executes an in-house least-squares linear regression algorithm (`algorithms/price_predictor.py`).

### Mathematical Model

Given day indices $x = [0, 1, \dots, n-1]$ and matching daily historical prices $y$, the best-fit line $y = mx + c$ is solved via closed-form normal equations:

$$m = \frac{\sum_{i=0}^{n-1} (x_i - \bar{x})(y_i - \bar{y})}{\sum_{i=0}^{n-1} (x_i - \bar{x})^2}$$

$$c = \bar{y} - m\bar{x}$$

Tomorrow's predicted price at index $x_{next} = n$ is calculated as:

$$\hat{y}_{next} = m \cdot n + c$$

### Trend Classification & Goodness-of-Fit ($R^2$)

To prevent minor daily noise from triggering false trend alerts, daily slope $m$ is evaluated against average price $\bar{y}$:

$$\text{Trend} = \begin{cases} \text{rising}, & \text{if } \frac{m}{\bar{y}} > +0.0015 \text{ (+0.15\% daily gain)} \\ \text{falling}, & \text{if } \frac{m}{\bar{y}} < -0.0015 \text{ (-0.15\% daily loss)} \\ \text{stable}, & \text{otherwise} \end{cases}$$

The $R^2$ coefficient of determination evaluates historical price line fit:

$$R^2 = 1 - \frac{\sum_{i=0}^{n-1} (y_i - (m x_i + c))^2}{\sum_{i=0}^{n-1} (y_i - \bar{y})^2}$$

* **High Confidence:** $R^2 \ge 0.60$
* **Medium Confidence:** $0.30 \le R^2 < 0.60$
* **Low Confidence:** $R^2 < 0.30$

---

## 🚀 How to Run Locally

### 1. Environment Setup

Clone the repository and install dependencies:

```bash
git clone [https://github.com/](https://github.com/)<your-username>/AAVA.git
cd AAVA
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

```

### 2. Configure Credentials

Copy `.env.example` to `.env` and insert your API keys:

```bash
cp .env.example .env

```

Populate `.env`:

```env
DEMO_MODE=false
AGMARKNET_API_KEY=your_actual_data_gov_in_api_key
AGMARKNET_BASE_URL=[https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070](https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070)
OPENWEATHER_API_KEY=your_openweathermap_api_key
GEMINI_API_KEY=your_gemini_api_key
FLASK_SECRET_KEY=aava_dev_secret_key_12345

```

### 3. Verify Agmarknet Connection

Run the diagnostic script to test live government endpoint connectivity:

```bash
python test_agmarknet_standalone.py

```

### 4. Launch Web Application

Start the Flask development server:

```bash
python app.py

```

Open **`http://127.0.0.1:5001`** in Google Chrome, Edge, or Safari.

### 5. Launch Terminal Voice Mode (Laptop Mic & Speakers)

To run the assistant locally using your laptop microphone and speakers:

```bash
python local_voice_demo.py

```

---

## 🧪 API & Diagnostic Suite

The project includes an isolated testing suite `test_agmarknet_standalone.py` to verify API connectivity independently from web servers or AI models:

```bash
python test_agmarknet_standalone.py

```

**Diagnostic Output:**

```text
==================================================
🧪 TESTING AGMARKNET ENDPOINT ISOLATION
   Commodity: Cotton | State: Andhra Pradesh
==================================================
📡 Sending HTTP GET Request to data.gov.in...
⏱️ Response Received in 0.4 seconds | Status Code: 200
📊 Total Records Returned: 7

✅ SUCCESS! Raw Government Records:
  [1] State: Andhra Pradesh | Mandi: Narasaraopet APMC | Price: ₹8000/quintal
  [2] State: Andhra Pradesh | Mandi: Gooti APMC        | Price: ₹9501/quintal

```

---

## 📊 Sample Queries Tested

* **Price Query (Hindi):** *"आंध्र प्रदेश में कॉटन का भाव क्या है"*
* **Price Query (Hindi):** *"चेन्नई में आलू का भाव क्या है"*
* **Trend Query (English):** *"What is the wheat trend tomorrow?"*
* **Weather Query (Hindi):** *"गोवा का मौसम कैसा है अभी"*
* **Weather Query (English):** *"What is the weather in Chennai?"*

---

## 👥 Authors & Credits

* **Chetan Lohia** — Systems Architecture, Backend Engineering & API Optimizations
* **Rahul Jha** — AI Integration, NLU Orchestration & Mathematical Forecasting

Developed for Internship Portfolio Submission (July 2026).

```

```