import streamlit as st
import wikipedia
import speech_recognition as sr
import pyttsx3
import requests
import urllib.parse
import threading

# --- Setup ---
SERPAPI_KEY = "your_serpapi_key_here"
tts_engine = pyttsx3.init()

def speak_text(text):
    def run():
        tts_engine.say(text)
        tts_engine.runAndWait()
    threading.Thread(target=run).start()

st.set_page_config(page_title="Smart Wikipedia Bot", page_icon="🤖", layout="centered")

# --- Custom CSS for chatbot theme ---
st.markdown("""
<style>
    html, body, [class*="css"] {
        background-color: #0B0C2A;
        color: #E6ECF1;
        font-family: 'Courier New', monospace;
    }
    .stApp {
        background-image: url('https://www.e-spincorp.com/wp-content/uploads/2018/03/CRN_14_chatbot-e1521081812790.jpg');
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center;
    }
    .chat-container {
        background-color: rgba(0,0,0,0.7);
        border-radius: 20px;
        padding: 1rem;
        margin: 1rem auto;
        width: 80%;
        max-height: 65vh;
        overflow-y: auto;
    }
    .chat-msg {
        margin: 8px 0;
        padding: 12px;
        border-radius: 16px;
        font-size: 16px;
        line-height: 1.5;
        max-width: 75%;
        word-wrap: break-word;
    }
    .user-msg {
        background-color: #3399FF;  /* Bright blue */
        color: white;
        margin-left: auto;
        text-align: right;
    }
    .bot-msg {
        background-color: #FFB347;  /* Light orange */
        color: black;
        margin-right: auto;
    }
    .input-area input {
        width: 80%;
        padding: 10px;
        border-radius: 25px;
        border: none;
        outline: none;
        font-size: 1rem;
        margin-right: 10px;
    }
    .input-area button {
        background: #ff79c6;
        border: none;
        border-radius: 50%;
        width: 48px;
        height: 48px;
        font-size: 24px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center;'>🤖 Smart Wikipedia Bot</h2>", unsafe_allow_html=True)

# --- Session history ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- Language & toggle ---
col1, col2 = st.columns(2)
with col1:
    lang = st.selectbox("🌍 Language", ["en", "hi", "fr", "es", "de"])
with col2:
    show_full = st.checkbox("📄 Show Full Article")

wikipedia.set_lang(lang)

# --- Voice Input ---
def get_voice_input():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        st.info("🎧 Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio, language=lang)
    except:
        return "Sorry, I couldn't understand."

if st.button("🎙️ Speak"):
    voice_query = get_voice_input()
    st.session_state.last_query = voice_query
else:
    voice_query = st.session_state.get("last_query", "")

# --- Text Input ---
user_input = st.text_input("💬 Ask Anything About...", value=voice_query, key="input")

# --- Bing Fallback ---
def bing_fallback_search(query):
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "bing",
        "q": query,
        "api_key": SERPAPI_KEY
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        return data.get("organic_results", [{}])[0].get("snippet", "No Bing data found.")
    except Exception as e:
        return f"Bing search error: {e}"

# --- Processing query ---
if user_input and (len(st.session_state.history) == 0 or st.session_state.history[-1][0] != user_input):
    try:
        content = wikipedia.page(user_input).content if show_full else wikipedia.summary(user_input, sentences=3)
    except wikipedia.exceptions.DisambiguationError as e:
        content = f"Ambiguous! Try: {', '.join(e.options[:3])}"
    except wikipedia.exceptions.PageError:
        content = bing_fallback_search(user_input)
    except Exception as e:
        content = f"Error occurred: {str(e)}"

    st.session_state.history.append(("You", user_input))
    st.session_state.history.append(("Bot", content))
    speak_text(content)

# --- Chat history UI ---
with st.container():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for sender, msg in st.session_state.history:
        css_class = "user-msg" if sender == "You" else "bot-msg"
        st.markdown(f'<div class="chat-msg {css_class}">{msg}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Download option ---
chat_data = "\n".join([f"{s}: {m}" for s, m in st.session_state.history])
st.download_button("💾 Download Chat", chat_data, "chat_history.txt")
