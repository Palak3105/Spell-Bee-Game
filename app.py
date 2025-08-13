import streamlit as st
import random
import requests

# -------------------------
# CONFIG & THEME
# -------------------------
st.set_page_config(page_title="Spell Bee", layout="centered")

st.markdown(
    """
    <style>
    :root { color-scheme: light; }
    html, body, .stApp, .main, .block-container {
        background-color: #ffe6f0 !important;
        color: #000000 !important;
    }
    h1, h2, h3, h4, h5, h6, p, span, label, div, a, li {
        color: #000000 !important;
    }

    /* Make only the text input white */
    input[type="text"] {
        background-color: white !important;
        color: black !important;
        border: 2px solid #ffb6d5 !important;
        border-radius: 5px !important;
    }

    /* Keep circle button style */
    .stButton>button {
        height: 80px; 
        width: 80px; 
        border-radius: 50%;
        font-size: 16px; 
        font-weight: bold;
        border: 2px solid #ffb6d5 !important;
        background-color: #ffffff !important;
        color: black !important;
    }

    .outer-letter {
        background-color: #ffd1e8 !important; /* Light pink */
        color: black !important;
    }
    .center-letter {
        background-color: #ff1493 !important; /* Dark pink */
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# GAME SETTINGS
# -------------------------
WORDS_RAW_URL = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
SCORING = {4: 2, 5: 4, 6: 6, 7: 8}
MAX_WORDS = 3

def points_for_length(n):
    return 0 if n < 4 else SCORING.get(n, 8)

# -------------------------
# LOAD WORD LIST
# -------------------------
@st.cache_data
def load_words():
    try:
        r = requests.get(WORDS_RAW_URL, timeout=5)
        words = [w.strip().lower() for w in r.text.splitlines() if w.isalpha()]
    except:
        words = ["planet", "general", "lantern", "pattern", "explain", "related", "partner",
                 "garden", "danger", "ranged", "learning", "triangle", "integral",
                 "altering", "orange", "granola"]
    return [w for w in words if len(w) >= 4]

# -------------------------
# GENERATE LETTERS
# -------------------------
def find_good_set(word_list):
    pangrams = [w for w in word_list if len(set(w)) == 7 and len(w) >= 7]
    random.shuffle(pangrams)
    for cand in pangrams:
        letters = sorted(set(cand))
        for center in letters:
            valid = [w for w in word_list if set(w) <= set(letters) and center in w]
            if len(valid) >= 10:
                outer = [l for l in letters if l != center]
                return letters, center, valid, random.sample(outer, len(outer))
    letters = list("planetg")
    center = letters[0]
    valid = [w for w in word_list if set(w) <= set(letters) and center in w]
    outer = [l for l in letters if l != center]
    return letters, center, valid, random.sample(outer, len(outer))

# -------------------------
# INIT GAME
# -------------------------
def init_game():
    word_list = load_words()
    letters, center, valid, outer_order = find_good_set(word_list)
    st.session_state.letters = letters
    st.session_state.center = center
    st.session_state.valid_words = valid
    st.session_state.outer_order = outer_order
    st.session_state.current_word = ""
    st.session_state.words_entered = []
    st.session_state.score = 0
    st.session_state.messages = []
    st.session_state.game_over = False

if "letters" not in st.session_state:
    init_game()

# -------------------------
# GAME FUNCTIONS
# -------------------------
def append_letter(l): st.session_state.current_word += l
def backspace(): st.session_state.current_word = st.session_state.current_word[:-1]
def clear_word(): st.session_state.current_word = ""
def reshuffle():
    outer = [l for l in st.session_state.letters if l != st.session_state.center]
    st.session_state.outer_order = random.sample(outer, len(outer))
def restart(): init_game()

def submit_word():
    word = st.session_state.current_word.lower()
    if len(word) < 4:
        st.session_state.messages.append("Word is too short")
    elif st.session_state.center not in word:
        st.session_state.messages.append("Middle letter is not included")
    elif any(ch not in st.session_state.letters for ch in word):
        st.session_state.messages.append("Word contains invalid letters")
    elif word not in load_words():
        st.session_state.messages.append("Word not found in dictionary")
    elif word in st.session_state.words_entered:
        st.session_state.messages.append("You already used that word")
    else:
        pts = points_for_length(len(word))
        st.session_state.score += pts
        st.session_state.words_entered.append(word)
        st.session_state.messages.append(f"Accepted! +{pts} points for '{word}'")
        if len(st.session_state.words_entered) >= MAX_WORDS:
            st.session_state.game_over = True
    st.session_state.current_word = ""

# -------------------------
# HEADER
# -------------------------
st.title("✨ Spell Bee")
st.metric("Score", f"{st.session_state.score} pts")

st.subheader("Words Formed")
if st.session_state.words_entered:
    st.write(", ".join(st.session_state.words_entered))
else:
    st.write("_No words yet_")
for m in st.session_state.messages[-3:]:
    st.info(m)

if st.session_state.game_over:
    st.success(f"Game over! Final score: {st.session_state.score}")
    st.write("Possible words:", ", ".join(st.session_state.valid_words[:20]))
    if st.button("Restart Game"): restart()
    st.stop()

# -------------------------
# HEXAGON LAYOUT
# -------------------------
outer = st.session_state.outer_order
center = st.session_state.center

def letter_btn(letter, css_class, key):
    if letter:
        if st.button(letter.upper(), key=key, use_container_width=False):
            append_letter(letter)
        st.markdown(
            f"<style>div[data-testid='stButton'][key='{key}'] button {{ background-color: inherit; }}</style>",
            unsafe_allow_html=True
        )

# Row 1 (top 2)
cols = st.columns([2,1,1,2])
with cols[1]: letter_btn(outer[0], "outer-letter", "top_left")
with cols[2]: letter_btn(outer[1], "outer-letter", "top_right")

# Row 2 (middle upper 3)
cols = st.columns([1,1,1,1,1])
with cols[0]: letter_btn(outer[2], "outer-letter", "mid_left")
with cols[2]: letter_btn(center, "center-letter", "center_btn")
with cols[4]: letter_btn(outer[3], "outer-letter", "mid_right")

# Row 3 (bottom 2)
cols = st.columns([2,1,1,2])
with cols[1]: letter_btn(outer[4], "outer-letter", "bot_left")
with cols[2]: letter_btn(outer[5], "outer-letter", "bot_right")

# -------------------------
# WORD INPUT
# -------------------------
st.subheader("Compose Word")
st.session_state.current_word = st.text_input(
    "Type or tap letters", value=st.session_state.current_word, key="word_input"
)

col1, col2, col3, col4 = st.columns(4)
if col1.button("⟲ Reshuffle"): reshuffle()
if col2.button("⌫ Backspace"): backspace()
if col3.button("Clear"): clear_word()
if col4.button("Submit Word"): submit_word()

# Restart / Exit
col1, col2 = st.columns(2)
if col1.button("Restart Game"): restart()
if col2.button("Exit"):
    st.session_state.game_over = True


