# spell_bee_streamlit.py
"""
Spell Bee (NYT-style) - Streamlit single-player app
- Picks 7 letters from an actual English word which uses exactly 7 unique letters (a pangram for the puzzle)
- Enforces: min 4 letters, must contain the center letter
- Up to 3 valid words allowed per game
- Scoring: 4->2, 5->4, 6->6, 7->8
- Uses Datamuse API to find valid words for the letter set (no API key)
- Baby-pink/dark-pink visual with a hexagon/honeycomb layout
"""

import streamlit as st
import requests
import random
import string
import math
import time

# -------------------------
# Config / Constants
# -------------------------
MIN_WORD_LEN = 4
MAX_VALID_WORDS = 3
SCORE_MAP = {4: 2, 5: 4, 6: 6, 7: 8}
DATAMUSE_BASE = "https://api.datamuse.com"
# Fallback pangram words (each has >=7 letters and at least 7 unique letters). Used if API fails.
FALLBACK_PANGRAMS = [
    "complex", "orchids", "jumping", "flatbed", "strange", "cupboard", "blanket", "diamond"
]
# Small fallback dictionary if API requests fail
FALLBACK_WORDSET = {"time","mind","love","game","word","play","test","team","code","make","take",
                    "note","tone","stone","alone","phone","sleep","chair","table","drink","write",
                    "bring","light","right","might","night","thing","there","their","water","small",
                    "large","apple","grape","peace","heart","earth","ready","story","happy","smile",
                    "house","mouse","dream","learn","study"}


# -------------------------
# Helper functions
# -------------------------
def datamuse_words_using_letters(letters_string, max_results=1000):
    """
    Query Datamuse to get words composed ONLY from letters_string (Datamuse 'sp' pattern).
    Returns a set of lowercase words.
    """
    # Datamuse 'sp' parameter with character class: e.g. sp=[abcdef]{4,}
    pattern = f"[{letters_string}]{{{MIN_WORD_LEN},}}"
    url = f"{DATAMUSE_BASE}/words"
    try:
        resp = requests.get(url, params={"sp": pattern, "max": max_results}, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            return {item["word"].lower() for item in data}
    except Exception:
        pass
    return set()

def datamuse_find_pangram_candidate(attempts=30):
    """
    Try to find an English word that has (>=7) length and exactly 7 unique letters.
    We'll query Datamuse for common words and choose one which has 7 unique letters.
    """
    url = f"{DATAMUSE_BASE}/words"
    # We'll iterate by asking for many common words and check uniqueness.
    letters = None
    try:
        for _ in range(attempts):
            # Ask for random words (using 'ml' random seed isn't possible); instead fetch many words and sample
            resp = requests.get(url, params={"sp":"????????", "max":1000}, timeout=6)  # 8-letter words example
            if resp.status_code != 200:
                break
            data = resp.json()
            if not data:
                break
            # pick random item and check it
            candidate = random.choice(data)["word"].lower()
            cand = "".join([c for c in candidate if c.isalpha()])
            if len(cand) >= 7 and len(set(cand)) >= 7:
                # take first 7 unique letters from the word
                unique = []
                for ch in cand:
                    if ch not in unique:
                        unique.append(ch)
                    if len(unique) == 7:
                        break
                if len(unique) == 7:
                    return "".join(unique)  # string of 7 letters
    except Exception:
        pass
    return None

def choose_puzzle_letters():
    """
    Central function to choose puzzle letters:
    - Prefer to find a real-word pangram (7 unique letters coming from a real word)
    - Once letters chosen, fetch the valid words (Datamuse) that use only those letters and length >= MIN_WORD_LEN
    - Ensure there is at least one pangram word in the valid_words (i.e., a word that uses all 7 letters)
    - If API fails, use fallback pangram list and fallback dictionary
    """
    # try to get from API first
    letters_set = None
    valid_words = set()
    pangram_word = None

    # try to find pangram candidate via Datamuse
    try:
        unique_letters = datamuse_find_pangram_candidate(attempts=20)
        if unique_letters:
            # For the letter set we got, get valid words
            words = datamuse_words_using_letters(unique_letters, max_results=2000)
            # filter words that contain at least one center letter later; we only ensure that pangram exists
            # find pangram(s) among returned words (a word that uses all 7 letters)
            pangrams = [w for w in words if len(set(w)) >= 7]
            if pangrams:
                letters_set = list(unique_letters.upper())
                valid_words = {w.lower() for w in words}
                pangram_word = random.choice(pangrams)
                return letters_set, valid_words, pangram_word
    except Exception:
        pass

    # fallback strategy: use a built-in pangram word and build letter set from it
    fallback = random.choice(FALLBACK_PANGRAMS)
    unique = []
    for ch in fallback.lower():
        if ch.isalpha() and ch not in unique:
            unique.append(ch)
        if len(unique) == 7:
            break
    if len(unique) < 7:
        # fill with random letters
        while len(unique) < 7:
            c = random.choice(string.ascii_lowercase)
            if c not in unique:
                unique.append(c)
    letters_set = [c.upper() for c in unique]
    # derive valid words by filtering fallback dictionary
    valid_words = {w for w in FALLBACK_WORDSET if all(ch in letters_set or ch.lower() in [x.lower() for x in letters_set] for ch in w)}
    pangram_word = fallback
    return letters_set, valid_words, pangram_word


# -------------------------
# Session state init
# -------------------------
st.set_page_config(page_title="Spell Bee", layout="centered", page_icon="🐝")
st.title("🐝 Spell Bee (NYT-style)")

if "initialized" not in st.session_state:
    letters, valid_words, pangram_word = choose_puzzle_letters()
    st.session_state.letters = letters  # 7 uppercase letters list
    st.session_state.outer = [l for l in letters if l != letters[3]]  # will set middle later
    # pick a middle: choose one letter that is in pangram_word (ensures pangram contains middle)
    possible_centers = [c.upper() for c in letters if c.lower() in pangram_word.lower()]
    if possible_centers:
        middle = random.choice(possible_centers)
    else:
        middle = random.choice(letters)
    # ensure middle is in st.session_state.letters and place it centrally
    # create outer by excluding the selected middle
    st.session_state.middle = middle
    st.session_state.outer = [l for l in letters if l != middle]
    random.shuffle(st.session_state.outer)
    st.session_state.typed = ""          # current typed string
    st.session_state.words = []          # valid words found (uppercase)
    st.session_state.score = 0
    st.session_state.message = ""
    st.session_state.valid_words = valid_words  # lowercase set possibly empty if fallback
    st.session_state.pangram_word = pangram_word if pangram_word else ""  # for debugging
    st.session_state.initialized = True
    st.session_state.game_over = False

# --------------
# Styling (baby pink / dark pink center)
# --------------
st.markdown(
    """
    <style>
    .app-bg { background: #ffe9f2; padding: 10px; border-radius: 6px; }
    .words-box { background: #fff0f6; padding: 10px; border-radius: 8px; border:1px solid #ffd9ec; }
    .letter-cell {
        width:72px; height:72px; border-radius:50%;
        display:flex; align-items:center; justify-content:center;
        font-weight:800; font-size:26px; color:#111; border:3px solid #ff7aa6;
        cursor: pointer;
    }
    .outer-cell { background: linear-gradient(180deg,#ffb3cf,#ff94bd); }
    .center-cell { background: linear-gradient(180deg,#ff5f8a,#ff2f60); color:#fff; width:88px; height:88px; font-size:34px; border:4px solid #ff1744; }
    .control-btn { background:#ff8fb2; color:#fff; border-radius:8px; padding:6px 10px; border:none; }
    .small-btn { background:#ff99cc; color:#fff; border-radius:6px; padding:6px 8px; border:none; }
    </style>
    """, unsafe_allow_html=True
)

# --------------
# Header: Score meter and Words Formed
# --------------
colA, colB = st.columns([1, 2])
with colA:
    st.markdown("**Score**")
    st.metric("", st.session_state.score)
    max_possible = MAX_VALID_WORDS * max(SCORE_MAP.values())
    prog = min(st.session_state.score / max_possible if max_possible else 0, 1.0)
    st.progress(prog)
with colB:
    st.markdown("**Words Formed**")
    st.markdown('<div class="words-box">', unsafe_allow_html=True)
    if st.session_state.words:
        for i, w in enumerate(st.session_state.words, start=1):
            st.write(f"{i}. {w} — {SCORE_MAP.get(len(w), 0)} pts")
    else:
        st.write("_No valid words yet._")
    st.markdown("</div>", unsafe_allow_html=True)

st.write("---")

# --------------
# Visual Hexagon (decorative) — we'll render a neat honeycomb using absolute positions
# --------------
# We'll build a small HTML block that shows the 6 outer letters around 1 center letter.
# Use math to place 6 items around a circle.
outer = st.session_state.outer  # 6 letters
middle = st.session_state.middle  # center letter

# Compose HTML circle positions
radius = 110
center_x = 160
center_y = 140
circle_html = "<div style='position: relative; width: 320px; height: 320px; margin: auto;'>"

for i, letter in enumerate(outer):
    angle = 2 * math.pi * i / 6
    x = center_x + radius * math.cos(angle) - 36
    y = center_y + radius * math.sin(angle) - 36
    circle_html += f"""
    <div style='position:absolute; left:{x}px; top:{y}px;'>
      <div class="letter-cell outer-cell" onclick="window.dispatchEvent(new CustomEvent('add_letter', {{detail:'{letter}'}}));" >
        {letter}
      </div>
    </div>
    """

# center
circle_html += f"""
<div style='position:absolute; left:{center_x-44}px; top:{center_y-44}px;'>
  <div class="letter-cell center-cell" onclick="window.dispatchEvent(new CustomEvent('add_letter', {{detail:'{middle}'}}));" >
    {middle}
  </div>
</div>
"""
circle_html += "</div>"

st.markdown(circle_html, unsafe_allow_html=True)

# --------------
# Click handling: Streamlit can't directly catch the JS custom event; provide clickable Streamlit buttons too
# (so clicking in the HTML remains decorative + we provide functional Streamlit buttons arranged similarly)
# --------------
# Row layout using Streamlit buttons for reliability (these append to typed string)
r1 = st.columns(3)
for idx in range(3):
    letter = outer[idx]
    if r1[idx].button(letter, key=f"b{idx}"):
        st.session_state.typed += letter

r2 = st.columns([1,1,1])
if r2[0].button(outer[3], key="b3"):
    st.session_state.typed += outer[3]
if r2[1].button(middle, key="center_btn"):
    st.session_state.typed += middle
if r2[2].button(outer[4], key="b4"):
    st.session_state.typed += outer[4]

r3 = st.columns(3)
if r3[0].button(outer[5], key="b5"):
    st.session_state.typed += outer[5]
r3[1].empty(); r3[2].empty()

st.write("")  # spacing

# --------------
# Input area and controls
# --------------
st.session_state.typed = st.text_input("Current word (tap letters or edit):", value=st.session_state.typed, max_chars=40).upper().strip()

c1, c2, c3, c4 = st.columns([1,1,1,1])

with c1:
    if st.button("Submit Word"):
        w = st.session_state.typed.strip().upper()
        allowed = set([l.upper() for l in outer] + [middle.upper()])
        # validations
        if len(w) == 0:
            st.warning("Type a word or tap letters first.")
        elif len(w) < MIN_WORD_LEN:
            st.warning("Word is too short")
        elif middle not in w:
            st.warning("Middle letter is not included")
        elif not all(ch in allowed for ch in w):
            st.warning("Word contains letters not in the given set")
        elif w.lower() in [x.lower() for x in st.session_state.words]:
            st.warning("You already entered that word")
        else:
            # Check validity using valid_words from Datamuse if available, else fallback to wordset
            lw = w.lower()
            ok = False
            if st.session_state.valid_words:
                ok = lw in st.session_state.valid_words
            else:
                ok = lw in FALLBACK_WORDSET
            if not ok:
                st.warning("Word not found in dictionary.")
            else:
                # Accept word
                pts = SCORE_MAP.get(len(w), 0) if len(w) <= 7 else SCORE_MAP.get(7, 8)
                st.session_state.words.append(w)
                st.session_state.score += pts
                st.success(f"Accepted: {w} (+{pts} pts)")
                st.session_state.typed = ""
                # Check max words reached
                if len(st.session_state.words) >= MAX_VALID_WORDS:
                    st.session_state.game_over = True

with c2:
    if st.button("🔄 Reshuffle"):
        # change positions of outer letters (shuffle)
        random.shuffle(st.session_state.outer)
        st.experimental_rerun()

with c3:
    if st.button("Restart Game"):
        # re-generate puzzle
        for k in ["initialized", "letters", "outer", "middle"]:
            if k in st.session_state:
                del st.session_state[k]
        # re-run by reloading page
        st.experimental_rerun()

with c4:
    if st.button("Exit"):
        st.stop()

st.write("---")

# --------------
# End-of-game & info
# --------------
if st.session_state.game_over:
    st.balloons()
    st.success(f"Game over — final score: {st.session_state.score}. Click Restart Game to play again.")

st.write(f"**Middle letter (required):** {middle}")
st.write("Allowed letters: " + " ".join(sorted([*st.session_state.outer, st.session_state.middle])))
st.write(f"Puzzle pangram example (for debug): {st.session_state.pangram_word}")
st.write(f"(If API failed to return many words, this puzzle may use fallback data.)")











