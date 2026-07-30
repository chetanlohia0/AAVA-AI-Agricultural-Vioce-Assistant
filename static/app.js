const askBtn = document.getElementById('askBtn');
const micBtn = document.getElementById('micBtn');
const micStatus = document.getElementById('micStatus');
const queryText = document.getElementById('queryText');
const langSelect = document.getElementById('lang');
const resultSection = document.getElementById('result');
const responseText = document.getElementById('responseText');
const replayAudioBtn = document.getElementById('replayAudioBtn');

let currentResponseText = "";

async function askAAVA(customText = null) {
  const text = (customText || queryText.value).trim();
  if (!text) return;

  askBtn.disabled = true;
  askBtn.textContent = 'Processing Query...';

  try {
    const res = await fetch('/demo/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text,
        lang: langSelect.value
      }),
    });

    const data = await res.json();
    currentResponseText = data.response;
    responseText.textContent = currentResponseText;
    resultSection.classList.remove('hidden');

    // Automatically Play Audio Response
    playVoiceAudio(currentResponseText, langSelect.value);

  } catch (err) {
    responseText.textContent = "Error connecting to AAVA backend server.";
    resultSection.classList.remove('hidden');
  } finally {
    askBtn.disabled = false;
    askBtn.textContent = 'Ask AAVA';
  }
}

function playVoiceAudio(text, lang) {
  if (!text) return;
  const audioUrl = `/api/tts?text=${encodeURIComponent(text)}&lang=${lang}`;
  const audio = new Audio(audioUrl);
  audio.play().catch(e => console.log('Autoplay info:', e));
}

// Browser Microphone Voice Recording
let recognition = null;
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = () => {
    micBtn.classList.add('recording');
    micStatus.textContent = 'Listening... Speak Now';
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    queryText.value = transcript;
    askAAVA(transcript);
  };

  recognition.onerror = () => {
    micStatus.textContent = 'Speech Error. Click to try again.';
    micBtn.classList.remove('recording');
  };

  recognition.onend = () => {
    micBtn.classList.remove('recording');
    micStatus.textContent = 'Click Microphone & Speak';
  };
}

micBtn.addEventListener('click', () => {
  if (!recognition) {
    alert("Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.");
    return;
  }
  const langMap = { hi: 'hi-IN', en: 'en-IN', mr: 'mr-IN' };
  recognition.lang = langMap[langSelect.value] || 'hi-IN';
  recognition.start();
});

askBtn.addEventListener('click', () => askAAVA());
replayAudioBtn.addEventListener('click', () => playVoiceAudio(currentResponseText, langSelect.value));

document.querySelectorAll('.sample-chip').forEach((btn) => {
  btn.addEventListener('click', (e) => {
    const q = e.target.dataset.q;
    queryText.value = q;
    askAAVA(q);
  });
});