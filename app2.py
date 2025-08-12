import streamlit as st
import random
import requests

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Spell Bee Game", layout="centered")

# Custom CSS for NYT-style hexagon
st.markdown("""
    <style>
    body {
        background-color: #ffe6f0;
    }
    .hex-container {
        position: relative;
        width: 250px;
        height: 250px;
        margin: auto;
    }
    .letter {
        position: absolute;
        background-color: #fdd835;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        border: none;
    }
    .middle {
        background-color: #ff1493;
        color: white;
    }
    /* Positions for outer letters (hexagon geometry) */
    .pos1 { top: 0; left: 95px; }
    .pos2 { top: 45px; left: 170px; }
    .pos3 { top: 125px; left: 170px; }
    .pos4 { top: 170px; left: 95px; }
    .pos5 { top: 125px; left: 20px; }
    .pos6 { top: 45px; left: 20px; }
    .middle-pos { top: 85px; left: 95px; }
    </style>
""", unsafe_allow_html=True)

# ---------------- FUNCTIONS ----------------
@st.cache_data
def load_word_list():
    url = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
    words = requests.get(url).text.split("\n")
    return set(w.lower() for w in words if w.isalpha())

def choose_letters():
    while True:
        pangram = random.choice(list(WORD_LIST))
        if len(set(pangram)) == 7:
            letters = list(set(pangram))
            middle_letter = random.choice(letters)
            return letters, middle_letter

def is_valid_word(word, letters, middle_letter):
    if len(word) < 4:
        return "Too short"
    if middle_letter not in word:
        return "Must include middle letter"
    if not set(word).issubset(set(letters)):
        return "Invalid letters"
    if word not in WORD_LIST:
        return "Not in dictionary"
    if word in st.session_state.words_found:
        return "Already used"
    return None

def score_word(word):
    scores = {4: 2, 5: 4, 6: 6, 7: 8}
    return scores.get(len(word), len(word))

def reshuffle_letters():
    outer = [l for l in st.session_state.letters if l != st.session_state.middle_letter]
    random.shuffle(outer)
    st.session_state.letters = outer[:3] + [st.session_state.middle_letter] + outer[3:]

def reset_game():
    st.session_state.letters, st.session_state.middle_letter = choose_letters()
    st.session_state.words_found = []
    st.session_state.score = 0
    st.session_state.input_word = ""

# ---------------- INIT ----------------
if "letters" not in st.session_state:
    WORD_LIST = load_word_list()
    reset_game()
else:
    if "WORD_LIST" not in globals():
        WORD_LIST = load_word_list()

# ---------------- TITLE ----------------
st.title("🐝 Spell Bee Game")
st.markdown(f"### Score: {st.session_state.score}")
st.markdown("**Words Found:** " + ", ".join(st.session_state.words_found) if st.session_state.words_found else "**Words Found:** None")

# ---------------- HEXAGON DISPLAY ----------------
outer = [l for l in st.session_state.letters if l != st.session_state.middle_letter]

# HTML for hexagon buttons
html_buttons = f"""
<div class="hex-container">
    <button class="letter pos1" onclick="sendLetter('{outer[0]}')">{outer[0].upper()}</button>
    <button class="letter pos2" onclick="sendLetter('{outer[1]}')">{outer[1].upper()}</button>
    <button class="letter pos3" onclick="sendLetter('{outer[2]}')">{outer[2].upper()}</button>
    <button class="letter pos4" onclick="sendLetter('{outer[3]}')">{outer[3].upper()}</button>
    <button class="letter pos5" onclick="sendLetter('{outer[4]}')">{outer[4].upper()}</button>
    <button class="letter pos6" onclick="sendLetter('{outer[5]}')">{outer[5].upper()}</button>
    <button class="letter middle middle-pos" onclick="sendLetter('{st.session_state.middle_letter}')">{st.session_state.middle_letter.upper()}</button>
</div>
"""

st.markdown(html_buttons, unsafe_allow_html=True)

# ---------------- INPUT & CONTROLS ----------------
word_input = st.text_input("Your Word:", key="input_word")

col_submit, col_shuffle, col_restart = st.columns(3)
with col_submit:
    if st.button("✅ Submit"):
        w = st.session_state.input_word.lower()
        err = is_valid_word(w, st.session_state.letters, st.session_state.middle_letter)
        if err:
            st.warning(err)
        else:
            st.session_state.words_found.append(w)
            st.session_state.score += score_word(w)
        st.session_state.input_word = ""
with col_shuffle:
    if st.button("🔀 Shuffle"):
        reshuffle_letters()
with col_restart:
    if st.button("🔄 Restart"):
        reset_game()
