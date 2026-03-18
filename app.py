import streamlit as st
import google.generativeai as genai
import json
import os
import hashlib
from datetime import datetime, timedelta
from supabase import create_client, Client

# ─── KONFIGURACE ───────────────────────────────────────────────
st.set_page_config(
    page_title="AI Tutor 4.D",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ⚠️ VYPLŇ SVOJE ÚDAJE:
SUPABASE_URL = st.secrets["SUPABASE_URL"]        # z Supabase → Settings → API
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]   # anon/public klíč
GEMINI_KEY   = st.secrets["GEMINI_KEY"]

# XP HODNOTY
XP_FLASHKARTA_ZNAM   = 5
XP_FLASHKARTA_TEZKE  = 2
XP_KVIZ_SPRAVNE      = 10
XP_ZKOUSKA           = 30

# ─── SUPABASE CLIENT ───────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# ─── GEMINI ────────────────────────────────────────────────────
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# ─── HESLO — HASH ──────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ─── XP HELPER ─────────────────────────────────────────────────
def pridat_xp(user_id: str, akce: str, xp: int):
    try:
        supabase.table("xp_log").insert({
            "user_id": user_id,
            "akce": akce,
            "xp_ziskano": xp
        }).execute()
    except:
        pass

def get_user_xp(user_id: str) -> int:
    try:
        r = supabase.table("xp_log").select("xp_ziskano").eq("user_id", user_id).execute()
        return sum(row["xp_ziskano"] for row in r.data)
    except:
        return 0

# ─── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

#MainMenu, footer { visibility: hidden; }
[data-testid="collapsedControl"] {
    display: flex !important; visibility: visible !important;
    background: #0d1120 !important;
    border: 1px solid rgba(0,200,255,0.25) !important;
    border-radius: 0 8px 8px 0 !important;
    color: #00c8ff !important;
}
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.main .block-container { padding: 2rem 2.5rem 3rem; max-width: 1200px; }
.stApp {
    background-color: #0a0e1a;
    background-image:
        radial-gradient(ellipse at 20% 0%, rgba(0,200,255,0.07) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 100%, rgba(100,0,255,0.06) 0%, transparent 50%);
}
[data-testid="stSidebar"] {
    background-color: #0d1120 !important;
    border-right: 1px solid rgba(0,200,255,0.15);
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] .stMarkdown p { color: #8899bb !important; font-size:13px; font-family:'Space Mono',monospace !important; }
[data-testid="stSidebar"] h1 { color:#fff !important; font-family:'Syne',sans-serif !important; font-size:22px !important; }
[data-testid="stSidebar"] hr { border-color: rgba(0,200,255,0.15) !important; }
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: #151c30 !important; border: 1px solid rgba(0,200,255,0.2) !important;
    color: #e0eaff !important; border-radius: 8px !important;
}
h1,h2,h3 { font-family:'Syne',sans-serif !important; color:#fff !important; }
h1 { font-size:2.4rem !important; font-weight:800 !important; }
h2 { font-size:1.6rem !important; font-weight:700 !important; }
h3 { font-size:1.2rem !important; }
p, li { color:#a8bbd8 !important; font-size:15px; line-height:1.7; }
.hero-title {
    font-family:'Syne',sans-serif; font-weight:800; font-size:3.2rem; line-height:1.05;
    background: linear-gradient(135deg, #00c8ff 0%, #7c3aed 60%, #f43f5e 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.badge {
    display:inline-block; font-family:'Space Mono',monospace; font-size:11px;
    color:#00c8ff; background:rgba(0,200,255,0.1); border:1px solid rgba(0,200,255,0.25);
    border-radius:20px; padding:3px 12px; letter-spacing:0.08em; text-transform:uppercase; margin-right:8px;
}
.card {
    background: linear-gradient(135deg,#111827,#0d1525);
    border:1px solid rgba(0,200,255,0.15); border-radius:16px; padding:24px;
    margin-bottom:12px; position:relative; overflow:hidden;
}
.card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background: linear-gradient(90deg, transparent, var(--accent,#00c8ff), transparent);
}
.stTabs [data-baseweb="tab-list"] {
    gap:4px; background:#0d1120; border-radius:12px; padding:6px;
    border:1px solid rgba(0,200,255,0.1);
}
.stTabs [data-baseweb="tab"] {
    font-family:'Space Mono',monospace !important; font-size:12px !important;
    text-transform:uppercase; letter-spacing:0.08em; color:#566a8a !important;
    background:transparent !important; border-radius:8px !important;
    padding:10px 20px !important; height:auto !important; border:none !important;
}
.stTabs [aria-selected="true"] { background:rgba(0,200,255,0.12) !important; color:#00c8ff !important; }
.stButton > button {
    font-family:'Space Mono',monospace !important; font-size:13px !important;
    text-transform:uppercase; letter-spacing:0.1em;
    background:linear-gradient(135deg,#00c8ff15,#7c3aed15) !important;
    color:#00c8ff !important; border:1px solid rgba(0,200,255,0.35) !important;
    border-radius:10px !important; padding:10px 24px !important; width:100%;
    transition:all 0.25s !important;
}
.stButton > button:hover {
    background:linear-gradient(135deg,#00c8ff25,#7c3aed25) !important;
    border-color:#00c8ff !important; transform:translateY(-2px);
    box-shadow:0 0 20px rgba(0,200,255,0.2);
}
.stFormSubmitButton > button {
    background:linear-gradient(135deg,#00c8ff,#7c3aed) !important;
    color:#000 !important; font-weight:700 !important; border:none !important;
}
[data-testid="stForm"] {
    background:#0d1120; border:1px solid rgba(0,200,255,0.12);
    border-radius:16px; padding:24px;
}
.stTextInput input, .stSelectbox > div > div {
    background:#111827 !important; border:1px solid rgba(0,200,255,0.25) !important;
    color:#e0eaff !important; border-radius:10px !important; font-family:'DM Sans',sans-serif !important;
}
.stTextInput label, .stSelectbox label {
    color:#8899bb !important; font-size:12px; text-transform:uppercase;
    letter-spacing:0.07em; font-family:'Space Mono',monospace !important;
}
hr { border:none; border-top:1px solid rgba(0,200,255,0.1) !important; margin:24px 0 !important; }
.stRadio label { color:#a8bbd8 !important; font-size:14px !important; }
.stSpinner > div { border-top-color:#00c8ff !important; }

/* ─── OPRAVA KLAVESNICE NA MOBILU ─── */
select, [data-baseweb="select"] input {
    font-size: 16px !important;
}
[data-baseweb="select"] [contenteditable] {
    -webkit-user-select: none !important;
    user-select: none !important;
    pointer-events: none !important;
}
[data-baseweb="select"] input[readonly] {
    font-size: 16px !important;
    pointer-events: none !important;
}

/* ── FLASHKARTA ── */
.flashcard-front {
    background: linear-gradient(135deg, #111827, #1a2035);
    border: 2px solid rgba(0,200,255,0.3);
    border-radius: 20px; padding: 48px 40px; text-align: center;
    min-height: 200px; display: flex; align-items: center; justify-content: center;
    margin: 20px 0;
}
.flashcard-question {
    font-family: 'Syne', sans-serif; font-size: 1.5rem;
    font-weight: 700; color: #ffffff; line-height: 1.4;
}
.flashcard-answer {
    background: linear-gradient(135deg, #0d1a0d, #111827);
    border: 2px solid rgba(0,255,150,0.3);
    border-radius: 20px; padding: 32px 40px; text-align: center;
    margin: 12px 0;
}
.flashcard-answer-text {
    font-family: 'DM Sans', sans-serif; font-size: 1.1rem;
    color: #a8f0c8; line-height: 1.6;
}

/* ── XP BADGE ── */
.xp-badge {
    font-family: 'Space Mono', monospace; font-size: 13px;
    color: #ffd700; background: rgba(255,215,0,0.1);
    border: 1px solid rgba(255,215,0,0.3); border-radius: 20px;
    padding: 4px 14px; display: inline-block;
}

/* ── LEADERBOARD ── */
.lb-row {
    display: flex; align-items: center; gap: 16px;
    background: #111827; border: 1px solid rgba(0,200,255,0.1);
    border-radius: 12px; padding: 14px 20px; margin-bottom: 8px;
    transition: border-color 0.2s;
}
.lb-row:hover { border-color: rgba(0,200,255,0.35); }
.lb-rank { font-family:'Space Mono',monospace; font-size:18px; font-weight:700; min-width:36px; }
.lb-name { font-family:'Syne',sans-serif; font-size:16px; font-weight:600; color:#fff; flex:1; }
.lb-xp { font-family:'Space Mono',monospace; font-size:14px; color:#ffd700; }
.rank-1 { color:#ffd700; }
.rank-2 { color:#c0c0c0; }
.rank-3 { color:#cd7f32; }

/* ── LOGIN ── */
.login-wrap { max-width: 420px; margin: 80px auto 0; }
.login-title {
    font-family:'Syne',sans-serif; font-size:2.2rem; font-weight:800;
    background:linear-gradient(135deg,#00c8ff,#7c3aed);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; text-align:center;
    margin-bottom:8px;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# AUTH — LOGIN / SESSION
# ══════════════════════════════════════════════
if "user" not in st.session_state:
    st.session_state.user = None

def login(username: str, password: str) -> bool:
    try:
        ph = hash_password(password)
        r = supabase.table("users").select("*").eq("username", username).eq("password_hash", ph).execute()
        if r.data:
            st.session_state.user = r.data[0]
            return True
    except Exception as e:
        st.error(f"Chyba připojení k databázi: {e}")
    return False

def logout():
    st.session_state.user = None
    st.session_state.clear()
    st.rerun()

# ── PŘIHLAŠOVACÍ OBRAZOVKA ──────────────────────────────────────
if st.session_state.user is None:
    st.markdown("""
    <div class="login-wrap">
        <div class="login-title">AI Tutor 4.D</div>
        <p style="text-align:center; color:#566a8a; font-family:'Space Mono',monospace; font-size:12px; letter-spacing:0.1em; text-transform:uppercase;">
        SPŠOL · Maturita 2026
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Přihlašovací jméno")
            password = st.text_input("Heslo", type="password")
            submitted = st.form_submit_button("Přihlásit se →")

        if submitted:
            if login(username, password):
                st.success(f"Vítej, {st.session_state.user['display_name']}! 👋")
                st.rerun()
            else:
                st.error("Špatné jméno nebo heslo.")

        st.markdown("""
        <p style="text-align:center; font-size:12px; color:#3a4a66; margin-top:16px;">
        Přihlašovací údaje dostaneš od správce aplikace.
        </p>
        """, unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════
# UŽIVATEL JE PŘIHLÁŠEN — HLAVNÍ APLIKACE
# ══════════════════════════════════════════════
user = st.session_state.user
user_id = user["id"]
is_admin = user.get("is_admin", False)

# ── INICIALIZACE SESSION STATE ──────────────────
defaults = {
    "kviz_data": None, "kviz_tema": None, "vyhodnotene": False,
    "vybrana_kniha": None, "kviz_data_cj": None, "vyhodnotene_cj": False,
    "flash_index": 0, "flash_zobrazit_odpoved": False,
    "flash_predmet": "automatizace", "flash_okruh": None,
    "flash_karty": [], "flash_session_stats": {"znam": 0, "tezke": 0, "neznam": 0},
    "chat_messages": [], "chat_okruh": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── BOČNÍ PANEL ────────────────────────────────
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712139.png", width=55)
    st.title("AI Tutor")
    st.markdown(f'<span class="badge">4.D SPŠOL</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # XP uživatele v sidebaru
    xp = get_user_xp(user_id)
    st.markdown(f"""
    <p style="font-family:'Space Mono',monospace; font-size:12px; color:#8899bb; margin-bottom:4px;">
    👤 {user['display_name']}
    </p>
    <span class="xp-badge">⚡ {xp} XP</span>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    sekce = st.selectbox("Sekce:", [
        "🏠 Domů",
        "🤖 Automatizace a Robotika",
        "📚 Český jazyk",
        "🃏 Flashkarty",
        "🏆 Leaderboard",
        "🗣️ AI Zkouška nanočisto",
        *(["⚙️ Admin panel"] if is_admin else [])
    ])

    st.markdown("---")
    if st.button("Odhlásit se"):
        logout()

    st.markdown(f"""
    <p style="font-family:'Space Mono',monospace; font-size:11px; color:#3a4a66;
       text-transform:uppercase; letter-spacing:0.08em; line-height:2;">
    v3.0 — Gemini 2.5 Flash
    </p>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SEKCE: DOMŮ
# ══════════════════════════════════════════════
if sekce == "🏠 Domů":
    col1, col2 = st.columns([1, 3], gap="large")
    with col1:
        st.markdown("<br><br>", unsafe_allow_html=True)
        logo_path = "obsah/obrazky/logo_spssol.png"
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.markdown("""
            <div style="width:100px;height:100px;border-radius:50%;
                background:linear-gradient(135deg,#00c8ff,#7c3aed);
                display:flex;align-items:center;justify-content:center;
                font-size:2.5rem;margin:20px auto;">🎓</div>
            """, unsafe_allow_html=True)
    with col2:
        xp_total = get_user_xp(user_id)
        st.markdown(f"""
        <span class="badge">Maturita 2026</span>
        <span class="badge" style="color:#ffd700;background:rgba(255,215,0,0.1);border-color:rgba(255,215,0,0.3);">⚡ {xp_total} XP</span>
        <br><br>
        <span class="hero-title">Vítej zpátky,<br>{user['display_name'].split()[0]}!</span>
        <p style="color:#566a8a;font-style:italic;margin-top:12px;padding-left:16px;border-left:2px solid rgba(0,200,255,0.3);">
        "Maturita se ptát nebude, jak moc jste spali. Pojďme to dát!"
        </p>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    cards = [
        ("📚", "#00c8ff", "Materiály", "25 okruhů automatizace + česká literatura"),
        ("🃏", "#7c3aed", "Flashkarty", "Opakuj klíčové pojmy se spaced repetition"),
        ("🗣️", "#f43f5e", "AI Zkouška", "Simulace ústní maturity s AI komisí"),
        ("🏆", "#ffd700", "Leaderboard", "Soutěž se spolužáky o nejvíc XP"),
    ]
    for col, (icon, color, title, desc) in zip([c1,c2,c3,c4], cards):
        with col:
            st.markdown(f"""
            <div class="card" style="--accent:{color};">
                <span style="font-size:2rem;">{icon}</span>
                <div style="font-family:'Syne',sans-serif;font-weight:700;color:#fff;margin:8px 0 4px;">{title}</div>
                <p style="font-size:13px;color:#566a8a;margin:0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SEKCE: FLASHKARTY
# ══════════════════════════════════════════════
elif sekce == "🃏 Flashkarty":

    st.markdown('<span class="badge">Flashkarty</span>', unsafe_allow_html=True)
    st.markdown("<h1 style='margin-top:8px;'>Opakování s kartičkami</h1>", unsafe_allow_html=True)
    st.markdown("""
    <p style="color:#566a8a;">Procházej kartičky a hodnoť se. Systém ti bude ukazovat obtížné karty častěji.
    Za každou správnou odpověď získáš XP!</p>
    """, unsafe_allow_html=True)

    # ── Výběr předmětu a okruhu ──
    col_l, col_r = st.columns([1, 2])
    with col_l:
        predmet_vyber = st.selectbox("Předmět:", ["automatizace", "cestina"],
            format_func=lambda x: "🤖 Automatizace" if x == "automatizace" else "📚 Český jazyk")

    # Načti dostupné okruhy
    try:
        okruhy_r = supabase.table("flashcards").select("okruh").eq("predmet", predmet_vyber).execute()
        okruhy = sorted(list(set(r["okruh"] for r in okruhy_r.data)))
    except:
        okruhy = []

    with col_r:
        if okruhy:
            okruh_vyber = st.selectbox("Okruh:", ["Vše"] + okruhy)
        else:
            st.warning("Zatím nejsou přidány žádné flashkarty. Přidej je v Admin panelu.")
            okruh_vyber = None

    st.markdown("---")

    # Načti karty
    if okruhy:
        try:
            q = supabase.table("flashcards").select("*").eq("predmet", predmet_vyber)
            if okruh_vyber and okruh_vyber != "Vše":
                q = q.eq("okruh", okruh_vyber)
            karty_r = q.execute()
            karty = karty_r.data
        except:
            karty = []

        # Reset při změně okruhu
        klic = f"{predmet_vyber}_{okruh_vyber}"
        if st.session_state.flash_okruh != klic:
            st.session_state.flash_okruh = klic
            st.session_state.flash_index = 0
            st.session_state.flash_zobrazit_odpoved = False
            st.session_state.flash_karty = karty
            st.session_state.flash_session_stats = {"znam": 0, "tezke": 0, "neznam": 0}

        karty = st.session_state.flash_karty

        if not karty:
            st.info("Pro tento výběr nejsou flashkarty.")
        else:
            idx = st.session_state.flash_index % len(karty)
            karta = karty[idx]
            stats = st.session_state.flash_session_stats

            # Progress bar
            progress = idx / len(karty)
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                <span style="font-family:'Space Mono',monospace;font-size:12px;color:#566a8a;">
                    Karta {idx+1} / {len(karty)}
                </span>
                <span style="font-family:'Space Mono',monospace;font-size:12px;">
                    <span style="color:#4ade80;">✓ {stats['znam']}</span> &nbsp;
                    <span style="color:#facc15;">~ {stats['tezke']}</span> &nbsp;
                    <span style="color:#f87171;">✗ {stats['neznam']}</span>
                </span>
            </div>
            """, unsafe_allow_html=True)
            st.progress(progress)

            # Karta — přední strana
            obtiznost_barva = {"1": "#4ade80", "2": "#facc15", "3": "#f87171"}.get(str(karta.get("obtiznost", 1)), "#00c8ff")
            obtiznost_text = {"1": "Lehká", "2": "Střední", "3": "Těžká"}.get(str(karta.get("obtiznost", 1)), "")
            st.markdown(f"""
            <div class="flashcard-front">
                <div>
                    <div style="font-family:'Space Mono',monospace;font-size:11px;color:{obtiznost_barva};
                         text-transform:uppercase;letter-spacing:0.1em;margin-bottom:16px;">
                        {obtiznost_text} · {karta['okruh']}
                    </div>
                    <div class="flashcard-question">{karta['otazka']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Zobrazit odpověď
            if not st.session_state.flash_zobrazit_odpoved:
                if st.button("💡 Zobrazit odpověď"):
                    st.session_state.flash_zobrazit_odpoved = True
                    st.rerun()
            else:
                st.markdown(f"""
                <div class="flashcard-answer">
                    <div style="font-family:'Space Mono',monospace;font-size:11px;color:#4ade80;
                         text-transform:uppercase;letter-spacing:0.1em;margin-bottom:12px;">Odpověď</div>
                    <div class="flashcard-answer-text">{karta['odpoved']}</div>
                </div>
                """, unsafe_allow_html=True)

                # Hodnocení — 3 tlačítka
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center;color:#566a8a;font-size:13px;'>Jak ti to šlo?</p>", unsafe_allow_html=True)
                col_a, col_b, col_c = st.columns(3, gap="medium")

                def ohodnotit(hodnoceni: str, xp_gain: int):
                    # Ulož progress
                    try:
                        existing = supabase.table("flashcard_progress")\
                            .select("id")\
                            .eq("user_id", user_id)\
                            .eq("flashcard_id", karta["id"])\
                            .execute()
                        if existing.data:
                            update_data = {"hodnoceni": hodnoceni, "posledni_opak": datetime.now().isoformat()}
                            if hodnoceni == "znam":
                                update_data["pocet_spravne"] = existing.data[0].get("pocet_spravne", 0) + 1
                            else:
                                update_data["pocet_spatne"] = existing.data[0].get("pocet_spatne", 0) + 1
                            supabase.table("flashcard_progress").update(update_data).eq("id", existing.data[0]["id"]).execute()
                        else:
                            supabase.table("flashcard_progress").insert({
                                "user_id": user_id, "flashcard_id": karta["id"],
                                "hodnoceni": hodnoceni,
                                "pocet_spravne": 1 if hodnoceni == "znam" else 0,
                                "pocet_spatne": 0 if hodnoceni == "znam" else 1
                            }).execute()
                        if xp_gain > 0:
                            pridat_xp(user_id, f"flashkarta_{hodnoceni}", xp_gain)
                    except:
                        pass
                    st.session_state.flash_session_stats[hodnoceni] += 1
                    st.session_state.flash_index += 1
                    st.session_state.flash_zobrazit_odpoved = False

                with col_a:
                    if st.button("✅ Znám to!", key="flash_znam"):
                        ohodnotit("znam", XP_FLASHKARTA_ZNAM)
                        st.rerun()
                with col_b:
                    if st.button("😅 Skoro", key="flash_tezke"):
                        ohodnotit("tezke", XP_FLASHKARTA_TEZKE)
                        st.rerun()
                with col_c:
                    if st.button("❌ Neznám", key="flash_neznam"):
                        ohodnotit("neznam", 0)
                        st.rerun()

            # Pokud projde všechny karty
            if st.session_state.flash_index >= len(karty) and not st.session_state.flash_zobrazit_odpoved:
                st.balloons()
                celkem_xp = stats["znam"] * XP_FLASHKARTA_ZNAM + stats["tezke"] * XP_FLASHKARTA_TEZKE
                st.markdown(f"""
                <div class="card" style="--accent:#ffd700;text-align:center;">
                    <div style="font-size:3rem;margin-bottom:12px;">🎉</div>
                    <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;color:#fff;">
                        Dokončil jsi celou sadu!
                    </div>
                    <p style="color:#566a8a;margin:8px 0 16px;">
                        ✅ {stats['znam']} znám &nbsp;|&nbsp;
                        😅 {stats['tezke']} skoro &nbsp;|&nbsp;
                        ❌ {stats['neznam']} neznám
                    </p>
                    <span class="xp-badge">+{celkem_xp} XP získáno!</span>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🔄 Znovu od začátku"):
                    st.session_state.flash_index = 0
                    st.session_state.flash_session_stats = {"znam": 0, "tezke": 0, "neznam": 0}
                    st.rerun()

# ══════════════════════════════════════════════
# SEKCE: LEADERBOARD
# ══════════════════════════════════════════════
elif sekce == "🏆 Leaderboard":

    st.markdown('<span class="badge">Soutěž</span>', unsafe_allow_html=True)
    st.markdown("<h1 style='margin-top:8px;'>Leaderboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#566a8a;'>Kdo se nejvíc připravuje na maturitu? 🏆</p>", unsafe_allow_html=True)
    st.markdown("---")

    try:
        users_r = supabase.table("users").select("id, display_name, username").eq("is_admin", False).execute()
        xp_r = supabase.table("xp_log").select("user_id, xp_ziskano").execute()

        xp_by_user = {}
        aktivita_by_user = {}
        for row in xp_r.data:
            uid = row["user_id"]
            xp_by_user[uid] = xp_by_user.get(uid, 0) + row["xp_ziskano"]
            aktivita_by_user[uid] = aktivita_by_user.get(uid, 0) + 1

        rows = []
        for u in users_r.data:
            rows.append({
                "display_name": u["display_name"],
                "username": u["username"],
                "celkove_xp": xp_by_user.get(u["id"], 0),
                "pocet_aktivit": aktivita_by_user.get(u["id"], 0)
            })
        rows.sort(key=lambda x: x["celkove_xp"], reverse=True)

        if not rows:
            st.info("Zatím žádná data. Začni procházet flashkarty a sbírej XP!")
        else:
            medals = {1: ("🥇", "rank-1"), 2: ("🥈", "rank-2"), 3: ("🥉", "rank-3")}
            for i, row in enumerate(rows, 1):
                medal, cls = medals.get(i, ("", ""))
                je_ja = "border-color: rgba(0,200,255,0.5) !important;" if row["username"] == user["username"] else ""
                st.markdown(f"""
                <div class="lb-row" style="{je_ja}">
                    <div class="lb-rank {cls}">{medal or f'#{i}'}</div>
                    <div class="lb-name">{row['display_name']}
                        {'<span style="font-size:11px;color:#00c8ff;margin-left:8px;">(ty)</span>' if row["username"] == user["username"] else ''}
                    </div>
                    <div style="font-size:12px;color:#566a8a;font-family:\'Space Mono\',monospace;margin-right:16px;">
                        {row['pocet_aktivit']} aktivit
                    </div>
                    <div class="lb-xp">⚡ {row['celkove_xp']} XP</div>
                </div>
                """, unsafe_allow_html=True)

            # XP systém — vysvětlivky
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div class="card" style="--accent:#ffd700;">
                <div style="font-family:'Syne',sans-serif;font-weight:700;color:#fff;margin-bottom:12px;">⚡ Jak získat XP?</div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                    <div style="font-size:13px;color:#a8bbd8;">✅ Flashkarta „Znám to"</div>
                    <div style="font-family:'Space Mono',monospace;font-size:13px;color:#ffd700;">+5 XP</div>
                    <div style="font-size:13px;color:#a8bbd8;">😅 Flashkarta „Skoro"</div>
                    <div style="font-family:'Space Mono',monospace;font-size:13px;color:#ffd700;">+2 XP</div>
                    <div style="font-size:13px;color:#a8bbd8;">📝 Správná odpověď v kvízu</div>
                    <div style="font-family:'Space Mono',monospace;font-size:13px;color:#ffd700;">+10 XP</div>
                    <div style="font-size:13px;color:#a8bbd8;">🗣️ Dokončená AI zkouška</div>
                    <div style="font-family:'Space Mono',monospace;font-size:13px;color:#ffd700;">+30 XP</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Chyba načítání leaderboardu: {e}")

# ══════════════════════════════════════════════
# SEKCE: AI ZKOUŠKA NANOČISTO
# ══════════════════════════════════════════════
elif sekce == "🗣️ AI Zkouška nanočisto":

    st.markdown('<span class="badge">Simulace</span>', unsafe_allow_html=True)
    st.markdown("<h1 style='margin-top:8px;'>AI Zkouška nanočisto</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#566a8a;'>AI hraje roli maturitní komise. Odpovídej jako u skutečné zkoušky.</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Výběr předmětu a okruhu
    col_l, col_r = st.columns(2)
    with col_l:
        zkouska_predmet = st.selectbox("Předmět zkoušky:", ["🤖 Automatizace a Robotika", "📚 Český jazyk"])
    with col_r:
        if "Automatizace" in zkouska_predmet:
            seznam = [f"{i}. {n}" for i, n in enumerate([
                "Číselné soustavy","Kódy a kódování","Logické funkce 1","Logické funkce 2",
                "Logické členy","Kombinační logické obvody 1","Kombinační logické obvody 2",
                "Sekvenční logické obvody 1","Sekvenční logické obvody 2","Paměti"
            ], 1)]
        else:
            seznam = ["Robinson Crusoe","Antigona","Romeo a Julie","Lakomec","Máj","Havran","Revizor","Malý princ","R.U.R.","Audience"]
        zkouska_okruh = st.selectbox("Okruh / Dílo:", seznam)

    # Chat interface
    if st.session_state.chat_okruh != zkouska_okruh:
        st.session_state.chat_messages = []
        st.session_state.chat_okruh = zkouska_okruh

        # Načti materiál
        if "Automatizace" in zkouska_predmet:
            cislo = zkouska_okruh.split(".")[0]
            cesta = f"obsah/{cislo}.md"
        else:
            cesta = None

        material = ""
        if cesta and os.path.exists(cesta):
            with open(cesta, "r", encoding="utf-8") as f:
                material = f.read()

        system_prompt = f"""Jsi přísná, ale spravedlivá maturitní komise na střední průmyslové škole v Olomouci.
Zkoušíš studenta z tématu: {zkouska_okruh} (předmět: {zkouska_predmet}).

{'Podkladový materiál: ' + material[:3000] if material else ''}

PRAVIDLA:
- Začni úvodní otázkou k tématu
- Po každé odpovědi studenta polož doplňující otázku nebo ho pochval a posuň dál
- Po 4-5 výměnách ukonči zkoušku a dej hodnocení (1-5) s komentářem co bylo dobré a co špatné
- Buď náročný, neptej se na triviality
- Mluv česky, formálně ale lidsky
- NIKDY neprozrazuj odpovědi předem

Zahaj zkoušku první otázkou."""

        with st.spinner("Komise se připravuje..."):
            try:
                resp = model.generate_content(system_prompt)
                uvod = resp.text
                st.session_state.chat_messages = [{"role": "assistant", "content": uvod}]
            except Exception as e:
                st.error(f"Chyba: {e}")

    # Zobraz chat
    for msg in st.session_state.chat_messages:
        if msg["role"] == "assistant":
            st.markdown(f"""
            <div class="card" style="--accent:#f43f5e;margin-bottom:8px;">
                <div style="font-family:'Space Mono',monospace;font-size:11px;color:#f43f5e;
                     text-transform:uppercase;margin-bottom:8px;">🎓 Komise</div>
                <p style="margin:0;color:#e0eaff;">{msg['content']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="card" style="--accent:#00c8ff;margin-bottom:8px;margin-left:40px;">
                <div style="font-family:'Space Mono',monospace;font-size:11px;color:#00c8ff;
                     text-transform:uppercase;margin-bottom:8px;">👤 Ty</div>
                <p style="margin:0;color:#e0eaff;">{msg['content']}</p>
            </div>
            """, unsafe_allow_html=True)

    # Input pro odpověď
    if st.session_state.chat_messages:
        with st.form("zkouska_form", clear_on_submit=True):
            odpoved_studenta = st.text_area("Tvoje odpověď:", height=100,
                placeholder="Piš jako bys mluvil u tabule...")
            odeslat = st.form_submit_button("Odpovědět →")

        if odeslat and odpoved_studenta.strip():
            st.session_state.chat_messages.append({"role": "user", "content": odpoved_studenta})

            # Připrav kontext pro Gemini
            konverzace = "\n".join([
                f"{'Komise' if m['role']=='assistant' else 'Student'}: {m['content']}"
                for m in st.session_state.chat_messages
            ])
            prompt = f"""Pokračuj jako maturitní komise. Dosavadní průběh zkoušky:

{konverzace}

Pokud jsi zkoušel/a již 4-5 kol otázek, ukonči zkoušku a dej hodnocení s konrétním číslem (1=výborně, 5=nedostatečně) a komentářem."""

            with st.spinner("Komise přemýšlí..."):
                try:
                    resp = model.generate_content(prompt)
                    komise_odpoved = resp.text
                    st.session_state.chat_messages.append({"role": "assistant", "content": komise_odpoved})

                    # XP za dokončení zkoušky
                    if any(x in komise_odpoved.lower() for x in ["hodnocení", "hodnotím", "výborně", "chvalitebně", "dobrý", "dostatečně", "nedostatečně"]):
                        pridat_xp(user_id, "zkouska_dokoncena", XP_ZKOUSKA)

                    st.rerun()
                except Exception as e:
                    st.error(f"Chyba: {e}")

        if st.button("🔄 Začít novou zkoušku"):
            st.session_state.chat_messages = []
            st.session_state.chat_okruh = None
            st.rerun()

# ══════════════════════════════════════════════
# SEKCE: ADMIN PANEL
# ══════════════════════════════════════════════
elif sekce == "⚙️ Admin panel" and is_admin:

    st.markdown('<span class="badge">Admin</span>', unsafe_allow_html=True)
    st.markdown("<h1 style='margin-top:8px;'>Admin panel</h1>", unsafe_allow_html=True)
    st.markdown("---")

    tab_zaci, tab_karty, tab_stats = st.tabs(["👥  Žáci", "🃏  Přidat flashkarty", "📊  Statistiky"])

    # ── Správa žáků ──
    with tab_zaci:
        st.subheader("Přidat nového žáka")
        with st.form("pridat_zaka"):
            col1, col2 = st.columns(2)
            with col1:
                novy_username = st.text_input("Username (přihlašovací jméno)", placeholder="novak_jan")
                novy_display = st.text_input("Zobrazované jméno", placeholder="Jan Novák")
            with col2:
                novy_heslo = st.text_input("Heslo", type="password")
                novy_admin = st.checkbox("Admin účet")
            if st.form_submit_button("➕ Přidat žáka"):
                try:
                    supabase.table("users").insert({
                        "username": novy_username,
                        "password_hash": hash_password(novy_heslo),
                        "display_name": novy_display,
                        "is_admin": novy_admin
                    }).execute()
                    st.success(f"Žák {novy_display} přidán!")
                except Exception as e:
                    st.error(f"Chyba: {e}")

        st.markdown("---")
        st.subheader("Seznam žáků")
        try:
            uzivatele = supabase.table("users").select("username, display_name, is_admin, created_at").execute()
            for u in uzivatele.data:
                role = "👑 Admin" if u["is_admin"] else "👤 Žák"
                st.markdown(f"`{u['username']}` — **{u['display_name']}** ({role})")
        except Exception as e:
            st.error(f"Chyba: {e}")

    # ── Přidat flashkarty ──
    with tab_karty:
        st.subheader("Přidat novou flashkartu")
        with st.form("nova_karta"):
            col1, col2 = st.columns(2)
            with col1:
                k_predmet = st.selectbox("Předmět:", ["automatizace", "cestina"])
                k_okruh = st.text_input("Okruh:", placeholder="1. Číselné soustavy")
            with col2:
                k_obtiznost = st.selectbox("Obtížnost:", [1, 2, 3],
                    format_func=lambda x: {1:"Lehká",2:"Střední",3:"Těžká"}[x])
            k_otazka = st.text_area("Otázka (přední strana):", height=80)
            k_odpoved = st.text_area("Odpověď (zadní strana):", height=100)
            if st.form_submit_button("➕ Přidat kartu"):
                try:
                    supabase.table("flashcards").insert({
                        "predmet": k_predmet, "okruh": k_okruh,
                        "otazka": k_otazka, "odpoved": k_odpoved,
                        "obtiznost": k_obtiznost
                    }).execute()
                    st.success("Karta přidána!")
                except Exception as e:
                    st.error(f"Chyba: {e}")

        st.markdown("---")
        st.subheader("Hromadný import (JSON)")
        st.markdown("""
        <div class="card" style="--accent:#7c3aed;">
        <p style="font-size:13px;color:#8899bb;margin:0;">Formát JSON pro import:</p>
        <pre style="font-family:'Space Mono',monospace;font-size:12px;color:#a8bbd8;margin-top:8px;">[
  {"predmet":"automatizace","okruh":"1. Číselné soustavy",
   "otazka":"Otázka?","odpoved":"Odpověď.","obtiznost":2}
]</pre>
        </div>
        """, unsafe_allow_html=True)
        json_import = st.text_area("Vlož JSON:", height=150)
        if st.button("📥 Importovat"):
            try:
                data = json.loads(json_import)
                supabase.table("flashcards").insert(data).execute()
                st.success(f"Importováno {len(data)} karet!")
            except Exception as e:
                st.error(f"Chyba: {e}")

    # ── Statistiky ──
    with tab_stats:
        st.subheader("Aktivita třídy")
        try:
            lb = supabase.table("leaderboard").select("*").execute()
            for row in lb.data:
                xp_val = row["celkove_xp"]
                max_xp = max((r["celkove_xp"] for r in lb.data), default=1)
                pct = int(xp_val / max_xp * 100) if max_xp > 0 else 0
                st.markdown(f"""
                <div style="margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                        <span style="color:#e0eaff;font-size:14px;">{row['display_name']}</span>
                        <span style="font-family:'Space Mono',monospace;font-size:12px;color:#ffd700;">⚡ {xp_val} XP</span>
                    </div>
                    <div style="background:#1a2035;border-radius:4px;height:6px;">
                        <div style="background:linear-gradient(90deg,#00c8ff,#7c3aed);width:{pct}%;height:100%;border-radius:4px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Chyba: {e}")

# ══════════════════════════════════════════════
# SEKCE: AUTOMATIZACE (původní funkcionalita)
# ══════════════════════════════════════════════
elif sekce == "🤖 Automatizace a Robotika":

    seznam_otazek = {f"{i}. {n}": f"{i}.md" for i, n in enumerate([
        "Číselné soustavy","Kódy a kódování","Logické funkce 1","Logické funkce 2",
        "Logické členy","Kombinační logické obvody 1","Kombinační logické obvody 2",
        "Sekvenční logické obvody 1","Sekvenční logické obvody 2","Paměti",
        "Měření proudu","Měření napětí","Měření odporu","Mechatronika",
        "Mechatronický výrobek","Senzory v mechatronických soustavách I",
        "Senzory v mechatronických soustavách II","Akční členy mechatronických soustav",
        "Řízení mechatronických soustav","Mechatronické systémy",
        "Programovatelné logické automaty","Hardware SIEMENS SIMATIC řady S7",
        "Mechatronika PLC-Konfigurace","Základní programové bloky",
        "Téma maturitní otázky 25"
    ], 1)}

    vybrana = st.selectbox("Zvol maturitní otázku:", list(seznam_otazek.keys()))

    if st.session_state.kviz_tema != vybrana:
        st.session_state.kviz_data = None
        st.session_state.kviz_tema = vybrana
        st.session_state.vyhodnotene = False

    cislo = vybrana.split(".")[0]
    nazev = ".".join(vybrana.split(".")[1:]).strip()
    st.markdown(f'<span class="badge">Okruh {cislo}</span><h1 style="margin-top:8px;">{nazev}</h1>', unsafe_allow_html=True)

    tab_t, tab_k, tab_z = st.tabs(["📚  Učební text", "📝  Kvíz", "🗣️  Jít k tabuli"])
    cesta = f"obsah/{seznam_otazek[vybrana]}"
    text_otazky = ""

    with tab_t:
        st.markdown("<br>", unsafe_allow_html=True)
        try:
            with open(cesta, "r", encoding="utf-8") as f:
                text_otazky = f.read()
            st.markdown(text_otazky)
        except FileNotFoundError:
            st.warning(f"Soubor `{cesta}` neexistuje.")

    with tab_k:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.kviz_data is None:
            if st.button("⚡ Vygenerovat kvíz"):
                if not text_otazky:
                    st.error("Nejprve vlož materiál.")
                else:
                    with st.spinner("Gemini analyzuje učivo..."):
                        instrukce = f"""Vytvoř 3 testové otázky z tohoto textu: {text_otazky}
Lomítka escapuj jako \\\\. Odpověz POUZE v JSON:
[{{"otazka":"?","moznosti":["A)","B)","C)"],"spravna_odpoved":"A)","vysvetleni":"..."}}]"""
                        try:
                            r = model.generate_content(instrukce)
                            t = r.text.strip().replace('```json','').replace('```','')
                            t = t.replace(r'\"','QUOT').replace('\\','\\\\').replace('QUOT',r'\"')
                            st.session_state.kviz_data = json.loads(t)
                            st.session_state.vyhodnotene = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Chyba: {e}")

        if st.session_state.kviz_data:
            if not st.session_state.vyhodnotene:
                with st.form("kviz_f"):
                    odpovede = []
                    for i, q in enumerate(st.session_state.kviz_data):
                        st.write(f"**{i+1}. {q['otazka']}**")
                        odpovede.append(st.radio("", q['moznosti'], key=f"q{i}"))
                        st.markdown("---")
                    if st.form_submit_button("✅ Zkontrolovat"):
                        st.session_state.kviz_odpovede = odpovede
                        st.session_state.vyhodnotene = True
                        st.rerun()

            if st.session_state.vyhodnotene:
                odpovede = st.session_state.get("kviz_odpovede", [])
                skore = 0
                for i, q in enumerate(st.session_state.kviz_data):
                    uzivatelova = odpovede[i] if i < len(odpovede) else ""
                    if uzivatelova == q['spravna_odpoved']:
                        skore += 1
                        pridat_xp(user_id, "kviz_spravne", XP_KVIZ_SPRAVNE)
                        st.success(f"✅ **{q['otazka']}**\nTvoje odpověď: {uzivatelova}")
                    else:
                        st.error(f"❌ **{q['otazka']}**\nTvoje odpověď: {uzivatelova}")
                        st.success(f"✔️ Správná odpověď: {q['spravna_odpoved']}")
                    st.info(f"💡 {q['vysvetleni']}")
                st.markdown(f"**Výsledek: {skore}/{len(st.session_state.kviz_data)}**")
                if st.button("🔄 Nový kvíz"):
                    st.session_state.kviz_data = None
                    st.session_state.kviz_odpovede = []
                    st.session_state.vyhodnotene = False
                    st.rerun()

    with tab_z:
        st.markdown('<div class="card" style="--accent:#f43f5e;"><p>Přejdi do sekce <strong>🗣️ AI Zkouška nanočisto</strong> v levém menu.</p></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SEKCE: ČESKÝ JAZYK (původní funkcionalita)
# ══════════════════════════════════════════════
elif sekce == "📚 Český jazyk":

    if "vybrana_kniha" not in st.session_state:
        st.session_state.vybrana_kniha = None

    knihovna = {
        "Defoe: Robinson Crusoe": "cj_robinson.md",
        "Komenský: Labyrint světa a ráj srdce": "cj_labyrint.md",
        "Sofoklés: Antigona": "cj_antigona.md",
        "Shakespeare: Romeo a Julie": "cj_romeo.md",
        "Moliére: Lakomec": "cj_lakomec.md",
        "Boccaccio: Dekameron": "cj_dekameron.md",
        "Goldoni: Sluha dvou pánů": "cj_sluha.md",
        "Puškin: Evžen Oněgin": "cj_onegin.md",
        "Hugo: Chrám Matky Boží v Paříži": "cj_chram.md",
        "Poe: Havran a jiné básně": "cj_havran.md",
        "Balzac: Otec Goriot": "cj_goriot.md",
        "Maupassant: Kulička": "cj_kulicka.md",
        "Verne: Dvacet tisíc mil pod mořem": "cj_verne.md",
        "Wilde: Obraz Doriana Graye": "cj_dorian.md",
        "Gogol: Revizor": "cj_revizor.md",
        "Čelakovský: Ohlas písní ruských": "cj_celakovský.md",
        "Mácha: Máj": "cj_maj.md",
        "Havlíček Borovský: Tyrolské elegie": "cj_tyrolske.md",
        "Erben: Kytice": "cj_kytice.md",
        "Mrštíkovi: Maryša": "cj_marysa.md",
        "Čech: Nový epochální výlet pana Broučka": "cj_broucek.md",
        "Němcová: Divá Bára": "cj_divabara.md",
        "Neruda: Povídky malostranské": "cj_neruda.md",
        "Jirásek: Staré pověsti české": "cj_jirasek.md",
        "Baudelaire: Květy zla": "cj_kvetyzla.md",
        "Remarque: Na západní frontě klid": "cj_remarque.md",
        "Rolland: Petr a Lucie": "cj_petralucie.md",
        "Hemingway: Stařec a moře": "cj_hemingway.md",
        "Bradbury: 451 stupňů Fahrenheita": "cj_bradbury.md",
        "Tolkien: Hobit": "cj_hobit.md",
        "Kafka: Proměna": "cj_kafka.md",
        "Fitzgerald: Velký Gatsby": "cj_gatsby.md",
        "Orwell: Farma zvířat": "cj_farma.md",
        "Golding: Pán much": "cj_panmuch.md",
        "Saint-Exupéry: Malý princ": "cj_maly_princ.md",
        "Kesey: Vyhoďme ho z kola ven": "cj_kesey.md",
        "Nesbo: Syn": "cj_nesbo.md",
        "Styron: Sophiina volba": "cj_sophie.md",
        "Merle: Smrt je mým řemeslem": "cj_merle.md",
        "Dürenmatt: Návštěva staré dámy": "cj_durenmatt.md",
        "Kerouac: Na cestě": "cj_kerouac.md",
        "Shaw: Pygmalion": "cj_pygmalion.md",
        "Nabokov: Lolita": "cj_lolita.md",
        "Havel: Audience": "cj_audience.md",
        "Bezruč: Slezské písně": "cj_bezruc.md",
        "Wolker: Těžká hodina": "cj_wolker.md",
        "Nezval: Edison": "cj_nezval.md",
        "Seifert: Na vlnách TSF": "cj_seifert.md",
        "Tučková: Vyhnání Gerty Schnirch": "cj_gerta.md",
        "Dyk: Krysař": "cj_krysar.md",
        "Hašek: Osudy dobrého vojáka Švejka": "cj_svejk.md",
        "John: Memento": "cj_memento.md",
        "Čapek: R.U.R.": "cj_rur.md",
        "Jirotka: Saturnin": "cj_saturnin.md",
        "Vančura: Rozmarné léto": "cj_vancura.md",
        "Škvorecký: Tankový prapor": "cj_skvorecky.md",
        "Fuks: Spalovač mrtvol": "cj_fuks.md",
        "Lustig: Modlitba pro Kateřinu Horovitzovou": "cj_lustig.md",
        "Olbracht: Nikola Šuhaj loupežník": "cj_olbracht.md",
        "Hrabal: Ostře sledované vlaky": "cj_hrabal.md",
        "Pavel: Smrt krásných srnců": "cj_pavel.md",
        "Viewegh: Účastníci zájezdu": "cj_viewegh.md",
        "Otčenášek: Romeo, Julie a tma": "cj_otcenasek.md",
        "Čapek: Bílá nemoc": "cj_bilanemoc.md",
        "Poláček: Bylo nás pět": "cj_polacek.md",
    }

    kategorie = {
        "📜 Do konce 18. století": ["Defoe: Robinson Crusoe","Komenský: Labyrint světa a ráj srdce","Sofoklés: Antigona","Shakespeare: Romeo a Julie","Moliére: Lakomec","Boccaccio: Dekameron","Goldoni: Sluha dvou pánů"],
        "🏛️ Literatura 19. století": ["Puškin: Evžen Oněgin","Hugo: Chrám Matky Boží v Paříži","Poe: Havran a jiné básně","Balzac: Otec Goriot","Maupassant: Kulička","Verne: Dvacet tisíc mil pod mořem","Wilde: Obraz Doriana Graye","Gogol: Revizor","Čelakovský: Ohlas písní ruských","Mácha: Máj","Havlíček Borovský: Tyrolské elegie","Erben: Kytice","Mrštíkovi: Maryša","Čech: Nový epochální výlet pana Broučka","Němcová: Divá Bára","Neruda: Povídky malostranské","Jirásek: Staré pověsti české"],
        "🌍 Světová 20.–21. stol.": ["Baudelaire: Květy zla","Remarque: Na západní frontě klid","Rolland: Petr a Lucie","Hemingway: Stařec a moře","Bradbury: 451 stupňů Fahrenheita","Tolkien: Hobit","Kafka: Proměna","Fitzgerald: Velký Gatsby","Orwell: Farma zvířat","Golding: Pán much","Saint-Exupéry: Malý princ","Kesey: Vyhoďme ho z kola ven","Nesbo: Syn","Styron: Sophiina volba","Merle: Smrt je mým řemeslem","Dürenmatt: Návštěva staré dámy","Kerouac: Na cestě","Shaw: Pygmalion","Nabokov: Lolita"],
        "🇨🇿 Česká 20.–21. stol.": ["Havel: Audience","Bezruč: Slezské písně","Wolker: Těžká hodina","Nezval: Edison","Seifert: Na vlnách TSF","Tučková: Vyhnání Gerty Schnirch","Dyk: Krysař","Hašek: Osudy dobrého vojáka Švejka","John: Memento","Čapek: R.U.R.","Jirotka: Saturnin","Vančura: Rozmarné léto","Škvorecký: Tankový prapor","Fuks: Spalovač mrtvol","Lustig: Modlitba pro Kateřinu Horovitzovou","Olbracht: Nikola Šuhaj loupežník","Hrabal: Ostře sledované vlaky","Pavel: Smrt krásných srnců","Viewegh: Účastníci zájezdu","Otčenášek: Romeo, Julie a tma","Čapek: Bílá nemoc","Poláček: Bylo nás pět"],
    }

    if st.session_state.vybrana_kniha is None:
        st.markdown('<span class="badge">Český jazyk</span><h1 style="margin-top:8px;">Literární knihovna</h1>', unsafe_allow_html=True)
        st.markdown("---")
        btn_idx = 0
        for kat, knihy in kategorie.items():
            st.markdown(f'<p style="font-family:\'Space Mono\',monospace;font-size:11px;text-transform:uppercase;letter-spacing:0.1em;color:#00c8ff;margin:28px 0 12px;">{kat}</p>', unsafe_allow_html=True)
            cols = st.columns(3, gap="medium")
            for i, k in enumerate(knihy):
                with cols[i % 3]:
                    if st.button(f"📖 {k}", key=f"b_{btn_idx}", use_container_width=True):
                        st.session_state.vybrana_kniha = k
                        st.session_state.kviz_data_cj = None
                        st.rerun()
                    btn_idx += 1
    else:
        if st.button("⬅️ Zpět"):
            st.session_state.vybrana_kniha = None
            st.rerun()
        st.markdown(f'<span class="badge">Rozbor</span><h1 style="margin-top:8px;">{st.session_state.vybrana_kniha}</h1>', unsafe_allow_html=True)

        tab_r, tab_kc, tab_zc = st.tabs(["📚  Rozbor", "📝  Kvíz", "🗣️  Zkouška"])
        soubor = knihovna[st.session_state.vybrana_kniha]
        cesta_cj = f"obsah/{soubor}"
        text_r = ""

        with tab_r:
            st.markdown("<br>", unsafe_allow_html=True)
            try:
                with open(cesta_cj, "r", encoding="utf-8") as f:
                    text_r = f.read()
                st.markdown(text_r)
            except FileNotFoundError:
                st.warning(f"Soubor `{cesta_cj}` neexistuje.")

        with tab_kc:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.session_state.kviz_data_cj is None:
                if st.button("⚡ Vygenerovat kvíz"):
                    if not text_r:
                        st.error("Nejprve vlož rozbor.")
                    else:
                        with st.spinner("Gemini tvoří otázky..."):
                            instrukce = f"""Vytvoř 3 otázky z tohoto literárního rozboru: {text_r}
Zaměř se na postavy, žánr, autora. Lomítka escapuj. Odpověz POUZE v JSON:
[{{"otazka":"?","moznosti":["A)","B)","C)"],"spravna_odpoved":"A)","vysvetleni":"..."}}]"""
                            try:
                                r = model.generate_content(instrukce)
                                t = r.text.strip().replace('```json','').replace('```','')
                                t = t.replace(r'\"','QUOT').replace('\\','\\\\').replace('QUOT',r'\"')
                                st.session_state.kviz_data_cj = json.loads(t)
                                st.session_state.vyhodnotene_cj = False
                                st.rerun()
                            except Exception as e:
                                st.error(f"Chyba: {e}")

            if st.session_state.kviz_data_cj:
                with st.form("kviz_cj"):
                    odpovede = []
                    for i, q in enumerate(st.session_state.kviz_data_cj):
                        st.write(f"**{i+1}. {q['otazka']}**")
                        odpovede.append(st.radio("", q['moznosti'], key=f"cj_{i}"))
                        st.markdown("---")
                    if st.form_submit_button("✅ Odevzdat"):
                        st.session_state.vyhodnotene_cj = True

                if st.session_state.vyhodnotene_cj:
                    for i, q in enumerate(st.session_state.kviz_data_cj):
                        if odpovede[i] == q['spravna_odpoved']:
                            pridat_xp(user_id, "kviz_cj_spravne", XP_KVIZ_SPRAVNE)
                            st.success(f"✅ {odpovede[i]}")
                        else:
                            st.error(f"❌ {odpovede[i]}")
                            st.success(f"✔️ Správně: {q['spravna_odpoved']}")
                        st.info(f"💡 {q['vysvetleni']}")
                    if st.button("🔄 Nový kvíz"):
                        st.session_state.kviz_data_cj = None
                        st.rerun()

        with tab_zc:
            st.markdown('<div class="card" style="--accent:#f43f5e;"><p>Přejdi do sekce <strong>🗣️ AI Zkouška nanočisto</strong> v levém menu.</p></div>', unsafe_allow_html=True)
