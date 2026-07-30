# backend/local_voice_demo.py
import os
import sys
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure the backend directory is in Python's import path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

from gtts import gTTS
import pygame
from routes.voice_routes import handle_query

# Check PyAudio / SpeechRecognition availability
MIC_AVAILABLE = False
try:
    import speech_recognition as sr
    MIC_AVAILABLE = True
except ImportError:
    MIC_AVAILABLE = False

def play_audio(text: str, lang: str = "hi"):
    """Converts text response to speech and plays it via laptop speakers."""
    lang_code = "hi" if lang == "hi" else ("mr" if lang == "mr" else "en")
    print(f"\n🔊 [AAVA Response]: {text}")
    
    try:
        tts = gTTS(text=text, lang=lang_code, slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_filename = fp.name
            tts.save(temp_filename)
            
        pygame.mixer.init()
        pygame.mixer.music.load(temp_filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
        
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
    except Exception as e:
        print(f"⚠️ Audio Playback Warning: {e}")

def listen_from_mic(lang: str = "hi") -> str:
    """Captures microphone input and converts it to text using ASR."""
    if not MIC_AVAILABLE:
        print("⚠️ Microphone library (PyAudio) not installed.")
        return input("⌨️ Type your query instead: ").strip()

    recognizer = sr.Recognizer()
    lang_code = "hi-IN" if lang == "hi" else ("mr-IN" if lang == "mr" else "en-IN")
    
    try:
        with sr.Microphone() as source:
            print("\n🎤 Calibrating microphone for background noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("🟢 Speak now! (e.g., 'Indore me gehu ka kya bhav hai?')")
            audio = recognizer.listen(source, timeout=7, phrase_time_limit=10)
            print("⚡ Processing spoken audio (ASR)...")
            text = recognizer.recognize_google(audio, language=lang_code)
            print(f"📝 Transcribed Text: '{text}'")
            return text
    except Exception as e:
        print(f"❌ Mic Error/Timeout ({e}). Falling back to text prompt...")
        return input("⌨️ Type your query instead: ").strip()

def main():
    print("==================================================")
    print("🌾 AAVA - AI Agricultural Voice Assistant 🌾")
    print("==================================================")
    
    selected_lang = input("Select Language [hi (Hindi) / en (English) / mr (Marathi)] (default: hi): ").strip() or "hi"
    user_location = input("Default Location (default: Indore): ").strip() or "Indore"

    while True:
        try:
            cmd = input("\n👉 Press [ENTER] to start | Type 'q' to exit: ").strip()
            if cmd.lower() == 'q':
                print("Exiting AAVA. Goodbye!")
                break
                
            transcript = listen_from_mic(lang=selected_lang)
            
            if transcript:
                # Pass transcribed query into core handle_query engine
                response_text = handle_query(text=transcript, lang=selected_lang, location=user_location)
                # Play output audio through speakers
                play_audio(response_text, lang=selected_lang)
        except KeyboardInterrupt:
            print("\nExiting AAVA. Goodbye!")
            break

if __name__ == "__main__":
    main()