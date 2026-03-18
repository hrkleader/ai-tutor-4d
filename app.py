import streamlit as st
import json
import os
import hashlib
from datetime import datetime
from supabase import create_client, Client
from groq import Groq

# ─── KONFIGURACE ───────────────────────────────────────────────
st.set_page_config(
    page_title="AI Tutor 4.D",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]
GROQ_KEY     = st.secrets["GROQ_KEY"]

XP_FLASHKARTA_ZNAM  = 5
XP_FLASHKARTA_TEZKE = 2
XP_KVIZ_SPRAVNE     = 10
XP_ZKOUSKA          = 30

# ─── SUPABASE ──────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# ─── GROQ ──────────────────────────────────────────────────────
groq_client = Groq(api_key=GROQ_KEY)

def groq_generate(prompt: str) -> str:
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
    )
    return response.choices[0].message.content

# ─── HELPERS ───────────────────────────────────────────────────
def hash_password(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()

def pridat_xp(user_id: str, akce: str, xp: int):
    try:
        supabase.table("xp_log").insert({"user_id": user_id, "akce": akce, "xp_ziskano": xp}).execute()
    except:
        pass

def get_user_xp(user_id: str) -> int:
    try:
        r = supabase.table("xp_log").select("xp_ziskano").eq("user_id", user_id).execute()
        return sum(row["xp_ziskano"] for row in r.data)
    except:
        return 0

def log_login(user_id: str):
    try:
        # Získej IP z headers
        ip = "neznámá"
        try:
            headers = st.context.headers
            ip = headers.get("x-forwarded-for", headers.get("x-real-ip", "neznámá"))
            if "," in ip:
                ip = ip.split(",")[0].strip()
        except:
            pass
        supabase.table("login_log").insert({
            "user_id": user_id,
            "ip_adresa": ip,
            "cas": datetime.now().isoformat()
        }).execute()
    except:
        pass

def generuj_kviz(text: str, predmet: str = "odborny") -> list | None:
    if predmet == "cestina":
        instrukce = f"""Jsi češtinář připravující studenty k maturitě. Vytvoř 3 testové otázky z tohoto literárního rozboru.
Zaměř se na postavy, děj, literární žánr nebo autora.
Text: {text[:4000]}
Odpověz VÝHRADNĚ v JSON bez markdown:
[{{"otazka":"?","moznosti":["A) ...","B) ...","C) ..."],"spravna_odpoved":"A) ...","vysvetleni":"..."}}]"""
    else:
        instrukce = f"""Jsi přísný středoškolský učitel. Vytvoř 3 testové otázky z tohoto textu.
Text: {text[:4000]}
Odpověz VÝHRADNĚ v JSON bez markdown:
[{{"otazka":"?","moznosti":["A) ...","B) ...","C) ..."],"spravna_odpoved":"A) ...","vysvetleni":"..."}}]"""
    try:
        r_text = groq_generate(instrukce)
        t = r_text.strip()
        # Vyčisti markdown bloky
        if "```json" in t:
            t = t.split("```json")[1].split("```")[0]
        elif t.startswith("```"):
            t = t.split("```")[1]
            if t.startswith("json"):
                t = t[4:]
        # Najdi JSON pole
        start = t.find("[")
        end = t.rfind("]") + 1
        if start != -1 and end > start:
            t = t[start:end]
        t = t.strip()
        return json.loads(t)
    except Exception as e:
        import streamlit as _st
        _st.error(f"Detail chyby: {e}")
        return None

# ─── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

#MainMenu, footer { visibility: hidden; }

/* ─── OPRAVA SIDEBAR TOGGLE ─── */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    background: #0d1120 !important;
    border: 1px solid rgba(0,200,255,0.25) !important;
    border-radius: 0 8px 8px 0 !important;
    color: #00c8ff !important;
}

/* ─── OPRAVA KLÁVESNICE NA MOBILU ─── */
[data-baseweb="select"] input,
[data-baseweb="select"] [contenteditable],
.stSelectbox input {
    font-size: 16px !important;
    pointer-events: none !important;
    caret-color: transparent !important;
}
input[type="text"], input[type="password"], textarea {
    font-size: 16px !important;
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
[data-testid="stSidebar"] .stMarkdown p { color:#8899bb !important; font-size:13px; font-family:'Space Mono',monospace !important; }
[data-testid="stSidebar"] h1 { color:#fff !important; font-family:'Syne',sans-serif !important; font-size:22px !important; }
[data-testid="stSidebar"] hr { border-color:rgba(0,200,255,0.15) !important; }
[data-testid="stSidebar"] .stSelectbox > div > div {
    background:#151c30 !important; border:1px solid rgba(0,200,255,0.2) !important;
    color:#e0eaff !important; border-radius:8px !important;
}
h1,h2,h3 { font-family:'Syne',sans-serif !important; color:#fff !important; }
h1 { font-size:2.2rem !important; font-weight:800 !important; }
h2 { font-size:1.5rem !important; font-weight:700 !important; }
p, li { color:#a8bbd8 !important; font-size:15px; line-height:1.7; }
.hero-title {
    font-family:'Syne',sans-serif; font-weight:800; font-size:3rem; line-height:1.05;
    background:linear-gradient(135deg,#00c8ff 0%,#7c3aed 60%,#f43f5e 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}
.badge {
    display:inline-block; font-family:'Space Mono',monospace; font-size:11px;
    color:#00c8ff; background:rgba(0,200,255,0.1); border:1px solid rgba(0,200,255,0.25);
    border-radius:20px; padding:3px 12px; letter-spacing:0.08em; text-transform:uppercase; margin-right:8px;
}
.card {
    background:linear-gradient(135deg,#111827,#0d1525);
    border:1px solid rgba(0,200,255,0.15); border-radius:16px; padding:24px;
    margin-bottom:12px; position:relative; overflow:hidden;
}
.card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg,transparent,var(--accent,#00c8ff),transparent);
}
.stTabs [data-baseweb="tab-list"] {
    gap:4px; background:#0d1120; border-radius:12px; padding:6px;
    border:1px solid rgba(0,200,255,0.1);
}
.stTabs [data-baseweb="tab"] {
    font-family:'Space Mono',monospace !important; font-size:12px !important;
    text-transform:uppercase; letter-spacing:0.08em; color:#566a8a !important;
    background:transparent !important; border-radius:8px !important;
    padding:10px 16px !important; height:auto !important; border:none !important;
}
.stTabs [aria-selected="true"] { background:rgba(0,200,255,0.12) !important; color:#00c8ff !important; }
.stButton > button {
    font-family:'Space Mono',monospace !important; font-size:12px !important;
    text-transform:uppercase; letter-spacing:0.08em;
    background:linear-gradient(135deg,#00c8ff15,#7c3aed15) !important;
    color:#00c8ff !important; border:1px solid rgba(0,200,255,0.35) !important;
    border-radius:10px !important; padding:10px 20px !important; width:100%;
    transition:all 0.2s !important;
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
.stTextInput input, .stTextArea textarea {
    background:#111827 !important; border:1px solid rgba(0,200,255,0.25) !important;
    color:#e0eaff !important; border-radius:10px !important;
}
.stTextInput label, .stSelectbox label, .stTextArea label {
    color:#8899bb !important; font-size:12px; text-transform:uppercase;
    letter-spacing:0.07em; font-family:'Space Mono',monospace !important;
}
.stSelectbox > div > div {
    background:#111827 !important; border:1px solid rgba(0,200,255,0.25) !important;
    color:#e0eaff !important; border-radius:10px !important;
}
hr { border:none; border-top:1px solid rgba(0,200,255,0.1) !important; margin:24px 0 !important; }
.stRadio label { color:#a8bbd8 !important; font-size:14px !important; }
.stSpinner > div { border-top-color:#00c8ff !important; }
.xp-badge {
    font-family:'Space Mono',monospace; font-size:13px;
    color:#ffd700; background:rgba(255,215,0,0.1);
    border:1px solid rgba(255,215,0,0.3); border-radius:20px; padding:4px 14px; display:inline-block;
}
.flashcard-front {
    background:linear-gradient(135deg,#111827,#1a2035);
    border:2px solid rgba(0,200,255,0.3); border-radius:20px;
    padding:48px 40px; text-align:center; min-height:200px;
    display:flex; align-items:center; justify-content:center; margin:20px 0;
}
.flashcard-question { font-family:'Syne',sans-serif; font-size:1.5rem; font-weight:700; color:#fff; line-height:1.4; }
.flashcard-answer {
    background:linear-gradient(135deg,#0d1a0d,#111827);
    border:2px solid rgba(0,255,150,0.3); border-radius:20px;
    padding:32px 40px; text-align:center; margin:12px 0;
}
.flashcard-answer-text { font-family:'DM Sans',sans-serif; font-size:1.1rem; color:#a8f0c8; line-height:1.6; }
.lb-row {
    display:flex; align-items:center; gap:16px;
    background:#111827; border:1px solid rgba(0,200,255,0.1);
    border-radius:12px; padding:14px 20px; margin-bottom:8px;
}
.lb-rank { font-family:'Space Mono',monospace; font-size:18px; font-weight:700; min-width:36px; }
.lb-name { font-family:'Syne',sans-serif; font-size:16px; font-weight:600; color:#fff; flex:1; }
.lb-xp { font-family:'Space Mono',monospace; font-size:14px; color:#ffd700; }
.rank-1 { color:#ffd700; }
.rank-2 { color:#c0c0c0; }
.rank-3 { color:#cd7f32; }
.login-wrap { max-width:420px; margin:80px auto 0; }
.login-title {
    font-family:'Syne',sans-serif; font-size:2.2rem; font-weight:800;
    background:linear-gradient(135deg,#00c8ff,#7c3aed);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; text-align:center; margin-bottom:8px;
}
.ip-warning { background:rgba(244,63,94,0.1); border:1px solid rgba(244,63,94,0.3); border-radius:10px; padding:12px 16px; margin:4px 0; }
.ip-ok { background:rgba(74,222,128,0.1); border:1px solid rgba(74,222,128,0.3); border-radius:10px; padding:12px 16px; margin:4px 0; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════
if "user" not in st.session_state:
    st.session_state.user = None

def login(username: str, password: str) -> bool:
    try:
        ph = hash_password(password)
        r = supabase.table("users").select("*").eq("username", username).eq("password_hash", ph).execute()
        if r.data:
            u = r.data[0]
            if u.get("zablokovany", False):
                st.error("Tento účet byl zablokován. Kontaktuj správce.")
                return False
            st.session_state.user = u
            log_login(u["id"])
            return True
    except Exception as e:
        st.error(f"Chyba připojení k databázi: {e}")
    return False

def logout():
    st.session_state.clear()
    st.rerun()

# ── PŘIHLAŠOVACÍ OBRAZOVKA ──────────────────────
if st.session_state.user is None:
    st.markdown('<div class="login-wrap"><div class="login-title">AI Tutor 4.D</div><p style="text-align:center;color:#566a8a;font-family:\'Space Mono\',monospace;font-size:12px;letter-spacing:0.1em;text-transform:uppercase;">SPŠOL · Maturita 2026</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Přihlašovací jméno")
            password = st.text_input("Heslo", type="password")
            if st.form_submit_button("Přihlásit se →"):
                if login(username, password):
                    st.rerun()
                else:
                    st.error("Špatné jméno nebo heslo.")
    st.stop()

# ══════════════════════════════════════════════
# PŘIHLÁŠEN
# ══════════════════════════════════════════════
user    = st.session_state.user
user_id = user["id"]
is_admin = user.get("is_admin", False)

# Inicializace session state
defaults = {
    "kviz_data": None, "kviz_tema": None, "vyhodnotene": False, "kviz_odpovede": [],
    "kviz_data_cj": None, "vyhodnotene_cj": False, "kviz_odpovede_cj": [],
    "vybrana_kniha": None,
    "flash_index": 0, "flash_zobrazit_odpoved": False, "flash_okruh": None,
    "flash_karty": [], "flash_session_stats": {"znam":0,"tezke":0,"neznam":0},
    "chat_messages": [], "chat_okruh": None,
    "slohovka_tema": None, "slohovka_utvar": None, "slohovka_hodnoceni": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── BOČNÍ PANEL ─────────────────────────────────
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712139.png", width=55)
    st.title("AI Tutor")
    st.markdown('<span class="badge">4.D SPŠOL</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    xp = get_user_xp(user_id)
    st.markdown(f'<p style="font-family:\'Space Mono\',monospace;font-size:12px;color:#8899bb;margin-bottom:4px;">👤 {user["display_name"]}</p><span class="xp-badge">⚡ {xp} XP</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    menu_items = ["🏠 Domů","🤖 Automatizace","📚 Český jazyk","✍️ Slohovka","🃏 Flashkarty","🏆 Leaderboard","🗣️ AI Zkouška"]
    if is_admin:
        menu_items.append("⚙️ Admin panel")
    sekce = st.selectbox("Sekce:", menu_items)
    st.markdown("---")
    if st.button("Odhlásit se"):
        logout()
    st.markdown('<p style="font-family:\'Space Mono\',monospace;font-size:11px;color:#3a4a66;text-transform:uppercase;letter-spacing:0.08em;line-height:2;">v3.1 — Gemini 2.0</p>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# POMOCNÁ FUNKCE — VYKRESLENÍ KVÍZU
# ══════════════════════════════════════════════
def vykresli_kviz(kviz_key: str, odpovede_key: str, vyhodnotene_key: str, form_key: str, xp_akce: str):
    """Univerzální komponenta kvízu — opravuje bug se ztrátou odpovědí."""
    kviz = st.session_state[kviz_key]
    if not kviz:
        return

    if not st.session_state[vyhodnotene_key]:
        with st.form(form_key):
            tmp_odpovede = []
            for i, q in enumerate(kviz):
                st.markdown(f"**Otázka {i+1}:** {q['otazka']}")
                tmp_odpovede.append(
                    st.radio("", q['moznosti'], key=f"{form_key}_q{i}", label_visibility="collapsed")
                )
                st.markdown("---")
            if st.form_submit_button("✅ Zkontrolovat odpovědi"):
                # KLÍČOVÁ OPRAVA: uložit odpovědi PŘED rerunem
                st.session_state[odpovede_key] = list(tmp_odpovede)
                st.session_state[vyhodnotene_key] = True
                st.rerun()
    else:
        odpovede = st.session_state.get(odpovede_key, [])
        skore = 0
        for i, q in enumerate(kviz):
            uzivatelova = odpovede[i] if i < len(odpovede) else ""
            otazka     = q.get('otazka') or q.get('question') or q.get('otázka') or f'Otázka {i+1}'
            spravna    = q.get('spravna_odpoved') or q.get('correct_answer') or q.get('spravna odpoved') or ''
            je_spravne = uzivatelova.strip() == spravna.strip()
            if je_spravne:
                skore += 1
                pridat_xp(user_id, xp_akce, XP_KVIZ_SPRAVNE)
                st.success(f"✅ **{otazka}**\nTvoje odpověď: {uzivatelova}")
            else:
                st.error(f"❌ **{otazka}**\nTvoje odpověď: {uzivatelova}")
                st.success(f"✔️ Správná odpověď: {spravna}")
            vysvetleni = q.get('vysvetleni') or q.get('vysvětlení') or q.get('explanation') or q.get('vysvetlení') or ""
            if vysvetleni:
                st.info(f"💡 {vysvetleni}")
        st.markdown(f"### Výsledek: {skore} / {len(kviz)}")
        if skore == len(kviz):
            st.balloons()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Nový kvíz", key=f"{form_key}_reset"):
                st.session_state[kviz_key] = None
                st.session_state[odpovede_key] = []
                st.session_state[vyhodnotene_key] = False
                st.rerun()

# ══════════════════════════════════════════════
# SEKCE: DOMŮ
# ══════════════════════════════════════════════
if sekce == "🏠 Domů":
    col1, col2 = st.columns([1,3], gap="large")
    with col1:
        st.markdown("<br><br>", unsafe_allow_html=True)
        logo = "obsah/obrazky/logo_spssol.png"
        if os.path.exists(logo):
            st.image(logo, use_container_width=True)
        else:
            st.markdown('<div style="width:100px;height:100px;border-radius:50%;background:linear-gradient(135deg,#00c8ff,#7c3aed);display:flex;align-items:center;justify-content:center;font-size:2.5rem;margin:20px auto;">🎓</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <span class="badge">Maturita 2026</span>
        <span class="badge" style="color:#ffd700;background:rgba(255,215,0,0.1);border-color:rgba(255,215,0,0.3);">⚡ {xp} XP</span>
        <br><br>
        <span class="hero-title">Vítej zpátky,<br>{user['display_name'].split()[0]}!</span>
        <p style="color:#566a8a;font-style:italic;margin-top:12px;padding-left:16px;border-left:2px solid rgba(0,200,255,0.3);">
        "Maturita se ptát nebude, jak moc jste spali. Pojďme to dát!"
        </p>
        """, unsafe_allow_html=True)
    st.markdown("---")
    c1,c2,c3,c4,c5 = st.columns(5, gap="small")
    for col, (icon, color, title, desc) in zip([c1,c2,c3,c4,c5], [
        ("📚","#00c8ff","Materiály","25 okruhů automatizace"),
        ("✍️","#f43f5e","Slohovka","AI hodnotí tvůj text"),
        ("🃏","#7c3aed","Flashkarty","Spaced repetition"),
        ("🗣️","#f43f5e","AI Zkouška","Simulace maturity"),
        ("🏆","#ffd700","Leaderboard","Soutěž třídy"),
    ]):
        with col:
            st.markdown(f'<div class="card" style="--accent:{color};"><span style="font-size:1.8rem;">{icon}</span><div style="font-family:\'Syne\',sans-serif;font-weight:700;color:#fff;margin:8px 0 4px;font-size:0.95rem;">{title}</div><p style="font-size:12px;color:#566a8a;margin:0;">{desc}</p></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SEKCE: AUTOMATIZACE
# ══════════════════════════════════════════════
elif sekce == "🤖 Automatizace":
    nazvy = ["Číselné soustavy","Kódy a kódování","Logické funkce 1","Logické funkce 2",
             "Logické členy","Kombinační logické obvody 1","Kombinační logické obvody 2",
             "Sekvenční logické obvody 1","Sekvenční logické obvody 2","Paměti",
             "Měření proudu","Měření napětí","Měření odporu","Mechatronika",
             "Mechatronický výrobek","Senzory v mechatronických soustavách I",
             "Senzory v mechatronických soustavách II","Akční členy mechatronických soustav",
             "Řízení mechatronických soustav","Mechatronické systémy",
             "Programovatelné logické automaty","Hardware SIEMENS SIMATIC řady S7",
             "Mechatronika PLC-Konfigurace","Základní programové bloky","Maturitní otázka 25"]
    seznam = {f"{i}. {n}": f"{i}.md" for i,n in enumerate(nazvy,1)}

    vybrana = st.selectbox("Zvol maturitní otázku:", list(seznam.keys()))
    if st.session_state.kviz_tema != vybrana:
        st.session_state.kviz_data = None
        st.session_state.kviz_tema = vybrana
        st.session_state.vyhodnotene = False
        st.session_state.kviz_odpovede = []

    cislo = vybrana.split(".")[0]
    nazev = ".".join(vybrana.split(".")[1:]).strip()
    st.markdown(f'<span class="badge">Okruh {cislo}</span><h1 style="margin-top:8px;">{nazev}</h1>', unsafe_allow_html=True)

    tab_t, tab_k, tab_z = st.tabs(["📚  Učební text","📝  Kvíz","🗣️  K tabuli"])
    cesta = f"obsah/{seznam[vybrana]}"
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
            st.markdown('<div class="card" style="--accent:#7c3aed;"><div style="font-family:\'Syne\',sans-serif;font-weight:700;color:#fff;margin-bottom:8px;">📝 Kvíz z tohoto okruhu</div><p style="color:#566a8a;margin:0;font-size:13px;">AI vygeneruje 3 otázky přesně z tohoto materiálu.</p></div>', unsafe_allow_html=True)
            if st.button("⚡ Vygenerovat kvíz"):
                if not text_otazky:
                    st.error("Nejprve vlož materiál do složky obsah/.")
                else:
                    with st.spinner("Gemini analyzuje učivo..."):
                        kviz = generuj_kviz(text_otazky, "odborny")
                        if kviz:
                            st.session_state.kviz_data = kviz
                            st.session_state.vyhodnotene = False
                            st.session_state.kviz_odpovede = []
                            st.rerun()
                        else:
                            st.error("Nepodařilo se vygenerovat kvíz. Zkus to znovu.")
        else:
            vykresli_kviz("kviz_data","kviz_odpovede","vyhodnotene","kviz_auto","kviz_auto_spravne")

    with tab_z:
        st.markdown('<div class="card" style="--accent:#f43f5e;"><p>Přejdi do sekce <strong>🗣️ AI Zkouška</strong> v levém menu.</p></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SEKCE: ČESKÝ JAZYK
# ══════════════════════════════════════════════
elif sekce == "📚 Český jazyk":
    knihovna = {
        "Defoe: Robinson Crusoe":"cj_robinson.md","Komenský: Labyrint světa a ráj srdce":"cj_labyrint.md",
        "Sofoklés: Antigona":"cj_antigona.md","Shakespeare: Romeo a Julie":"cj_romeo.md",
        "Moliére: Lakomec":"cj_lakomec.md","Boccaccio: Dekameron":"cj_dekameron.md",
        "Goldoni: Sluha dvou pánů":"cj_sluha.md","Puškin: Evžen Oněgin":"cj_onegin.md",
        "Hugo: Chrám Matky Boží v Paříži":"cj_chram.md","Poe: Havran a jiné básně":"cj_havran.md",
        "Balzac: Otec Goriot":"cj_goriot.md","Maupassant: Kulička":"cj_kulicka.md",
        "Verne: Dvacet tisíc mil pod mořem":"cj_verne.md","Wilde: Obraz Doriana Graye":"cj_dorian.md",
        "Gogol: Revizor":"cj_revizor.md","Čelakovský: Ohlas písní ruských":"cj_celakovský.md",
        "Mácha: Máj":"cj_maj.md","Havlíček Borovský: Tyrolské elegie":"cj_tyrolske.md",
        "Erben: Kytice":"cj_kytice.md","Mrštíkovi: Maryša":"cj_marysa.md",
        "Čech: Nový epochální výlet pana Broučka":"cj_broucek.md","Němcová: Divá Bára":"cj_divabara.md",
        "Neruda: Povídky malostranské":"cj_neruda.md","Jirásek: Staré pověsti české":"cj_jirasek.md",
        "Baudelaire: Květy zla":"cj_kvetyzla.md","Remarque: Na západní frontě klid":"cj_remarque.md",
        "Rolland: Petr a Lucie":"cj_petralucie.md","Hemingway: Stařec a moře":"cj_hemingway.md",
        "Bradbury: 451 stupňů Fahrenheita":"cj_bradbury.md","Tolkien: Hobit":"cj_hobit.md",
        "Kafka: Proměna":"cj_kafka.md","Fitzgerald: Velký Gatsby":"cj_gatsby.md",
        "Orwell: Farma zvířat":"cj_farma.md","Golding: Pán much":"cj_panmuch.md",
        "Saint-Exupéry: Malý princ":"cj_maly_princ.md","Kesey: Vyhoďme ho z kola ven":"cj_kesey.md",
        "Nesbo: Syn":"cj_nesbo.md","Styron: Sophiina volba":"cj_sophie.md",
        "Merle: Smrt je mým řemeslem":"cj_merle.md","Dürenmatt: Návštěva staré dámy":"cj_durenmatt.md",
        "Kerouac: Na cestě":"cj_kerouac.md","Shaw: Pygmalion":"cj_pygmalion.md",
        "Nabokov: Lolita":"cj_lolita.md","Havel: Audience":"cj_audience.md",
        "Bezruč: Slezské písně":"cj_bezruc.md","Wolker: Těžká hodina":"cj_wolker.md",
        "Nezval: Edison":"cj_nezval.md","Seifert: Na vlnách TSF":"cj_seifert.md",
        "Tučková: Vyhnání Gerty Schnirch":"cj_gerta.md","Dyk: Krysař":"cj_krysar.md",
        "Hašek: Osudy dobrého vojáka Švejka":"cj_svejk.md","John: Memento":"cj_memento.md",
        "Čapek: R.U.R.":"cj_rur.md","Jirotka: Saturnin":"cj_saturnin.md",
        "Vančura: Rozmarné léto":"cj_vancura.md","Škvorecký: Tankový prapor":"cj_skvorecky.md",
        "Fuks: Spalovač mrtvol":"cj_fuks.md","Lustig: Modlitba pro Kateřinu Horovitzovou":"cj_lustig.md",
        "Olbracht: Nikola Šuhaj loupežník":"cj_olbracht.md","Hrabal: Ostře sledované vlaky":"cj_hrabal.md",
        "Pavel: Smrt krásných srnců":"cj_pavel.md","Viewegh: Účastníci zájezdu":"cj_viewegh.md",
        "Otčenášek: Romeo, Julie a tma":"cj_otcenasek.md","Čapek: Bílá nemoc":"cj_bilanemoc.md",
        "Poláček: Bylo nás pět":"cj_polacek.md",
    }
    kategorie = {
        "📜 Do konce 18. stol.":["Defoe: Robinson Crusoe","Komenský: Labyrint světa a ráj srdce","Sofoklés: Antigona","Shakespeare: Romeo a Julie","Moliére: Lakomec","Boccaccio: Dekameron","Goldoni: Sluha dvou pánů"],
        "🏛️ Literatura 19. stol.":["Puškin: Evžen Oněgin","Hugo: Chrám Matky Boží v Paříži","Poe: Havran a jiné básně","Balzac: Otec Goriot","Maupassant: Kulička","Verne: Dvacet tisíc mil pod mořem","Wilde: Obraz Doriana Graye","Gogol: Revizor","Čelakovský: Ohlas písní ruských","Mácha: Máj","Havlíček Borovský: Tyrolské elegie","Erben: Kytice","Mrštíkovi: Maryša","Čech: Nový epochální výlet pana Broučka","Němcová: Divá Bára","Neruda: Povídky malostranské","Jirásek: Staré pověsti české"],
        "🌍 Světová 20.–21. stol.":["Baudelaire: Květy zla","Remarque: Na západní frontě klid","Rolland: Petr a Lucie","Hemingway: Stařec a moře","Bradbury: 451 stupňů Fahrenheita","Tolkien: Hobit","Kafka: Proměna","Fitzgerald: Velký Gatsby","Orwell: Farma zvířat","Golding: Pán much","Saint-Exupéry: Malý princ","Kesey: Vyhoďme ho z kola ven","Nesbo: Syn","Styron: Sophiina volba","Merle: Smrt je mým řemeslem","Dürenmatt: Návštěva staré dámy","Kerouac: Na cestě","Shaw: Pygmalion","Nabokov: Lolita"],
        "🇨🇿 Česká 20.–21. stol.":["Havel: Audience","Bezruč: Slezské písně","Wolker: Těžká hodina","Nezval: Edison","Seifert: Na vlnách TSF","Tučková: Vyhnání Gerty Schnirch","Dyk: Krysař","Hašek: Osudy dobrého vojáka Švejka","John: Memento","Čapek: R.U.R.","Jirotka: Saturnin","Vančura: Rozmarné léto","Škvorecký: Tankový prapor","Fuks: Spalovač mrtvol","Lustig: Modlitba pro Kateřinu Horovitzovou","Olbracht: Nikola Šuhaj loupežník","Hrabal: Ostře sledované vlaky","Pavel: Smrt krásných srnců","Viewegh: Účastníci zájezdu","Otčenášek: Romeo, Julie a tma","Čapek: Bílá nemoc","Poláček: Bylo nás pět"],
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
                        st.session_state.vyhodnotene_cj = False
                        st.session_state.kviz_odpovede_cj = []
                        st.rerun()
                    btn_idx += 1
    else:
        if st.button("⬅️ Zpět do knihovny"):
            st.session_state.vybrana_kniha = None
            st.rerun()
        st.markdown(f'<span class="badge">Rozbor</span><h1 style="margin-top:8px;">{st.session_state.vybrana_kniha}</h1>', unsafe_allow_html=True)
        tab_r, tab_kc, tab_zc = st.tabs(["📚  Rozbor","📝  Kvíz","🗣️  Zkouška"])
        cesta_cj = f"obsah/{knihovna[st.session_state.vybrana_kniha]}"
        text_r = ""

        with tab_r:
            st.markdown("<br>", unsafe_allow_html=True)
            try:
                with open(cesta_cj,"r",encoding="utf-8") as f:
                    text_r = f.read()
                st.markdown(text_r)
            except FileNotFoundError:
                st.warning(f"Soubor `{cesta_cj}` ještě neexistuje.")

        with tab_kc:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.session_state.kviz_data_cj is None:
                if st.button("⚡ Vygenerovat kvíz k dílu"):
                    if not text_r:
                        st.error("Nejprve vlož rozbor.")
                    else:
                        with st.spinner("Gemini tvoří literární otázky..."):
                            kviz = generuj_kviz(text_r, "cestina")
                            if kviz:
                                st.session_state.kviz_data_cj = kviz
                                st.session_state.vyhodnotene_cj = False
                                st.session_state.kviz_odpovede_cj = []
                                st.rerun()
                            else:
                                st.error("Nepodařilo se vygenerovat kvíz.")
            else:
                vykresli_kviz("kviz_data_cj","kviz_odpovede_cj","vyhodnotene_cj","kviz_cj","kviz_cj_spravne")

        with tab_zc:
            st.markdown('<div class="card" style="--accent:#f43f5e;"><p>Přejdi do sekce <strong>🗣️ AI Zkouška</strong> v levém menu.</p></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SEKCE: SLOHOVKA
# ══════════════════════════════════════════════
elif sekce == "✍️ Slohovka":
    st.markdown('<span class="badge">Český jazyk</span><h1 style="margin-top:8px;">Příprava na slohovku</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#566a8a;'>Vygeneruj téma, napiš text a AI ho ohodnotí jako učitel u maturity.</p>", unsafe_allow_html=True)
    st.markdown("---")

    UTVARY = {
        "Úvaha": "Zamyšlení nad tématem, vlastní názor podpořený argumenty. Struktura: teze → argumenty → závěr.",
        "Popis": "Objektivní zachycení předmětu, osoby nebo děje. Přesný, věcný jazyk.",
        "Charakteristika": "Vystižení vlastností osoby nebo literární postavy. Vnější + vnitřní charakteristika.",
        "Vypravování": "Zachycení děje s přímou řečí, dynamika, napětí. Ich nebo er-forma.",
        "Životopis": "Chronologický přehled života osoby. Objektivní, faktografický styl.",
        "Fejeton": "Kratší publicistický útvar s humorem a ironií. Aktuální téma.",
    }

    tab_tema, tab_hodnoceni, tab_rady = st.tabs(["🎲  Vygenerovat téma","📝  Odevzdat text","💡  Rady k útvarům"])

    with tab_tema:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            utvar = st.selectbox("Slohový útvar:", list(UTVARY.keys()))
        with col2:
            obtiznost = st.selectbox("Obtížnost:", ["Lehká","Střední","Těžká"])

        if st.button("🎲 Vygenerovat maturitní téma"):
            with st.spinner("AI vymýšlí téma..."):
                try:
                    prompt = f"""Vygeneruj 1 maturitní slohové téma pro útvar: {utvar}.
Obtížnost: {obtiznost}.
Téma musí být konkrétní, zajímavé a vhodné pro středoškoláka.
Uveď jen téma (1-2 věty), žádný další text."""
                    r_text = groq_generate(prompt)
                    st.session_state.slohovka_tema = r_text.strip()
                    st.session_state.slohovka_utvar = utvar
                    st.rerun()
                except Exception as e:
                    st.error(f"Chyba: {e}")

        if st.session_state.slohovka_tema:
            st.markdown(f"""
            <div class="card" style="--accent:#f43f5e;">
                <div style="font-family:'Space Mono',monospace;font-size:11px;color:#f43f5e;text-transform:uppercase;margin-bottom:12px;">
                    🎯 Tvoje téma — {st.session_state.slohovka_utvar}
                </div>
                <div style="font-family:'Syne',sans-serif;font-size:1.2rem;font-weight:700;color:#fff;">
                    {st.session_state.slohovka_tema}
                </div>
                <p style="color:#566a8a;font-size:12px;margin-top:12px;margin-bottom:0;">
                    {UTVARY.get(st.session_state.slohovka_utvar,'')}
                </p>
            </div>
            """, unsafe_allow_html=True)

    with tab_hodnoceni:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.slohovka_tema:
            st.markdown(f'<p style="color:#566a8a;font-size:13px;">Téma: <strong style="color:#e0eaff;">{st.session_state.slohovka_tema}</strong></p>', unsafe_allow_html=True)
        else:
            st.info("Nejprve vygeneruj téma v záložce vlevo.")

        with st.form("slohovka_form"):
            utvar_hodnoceni = st.selectbox("Útvar:", list(UTVARY.keys()), key="sh_utvar")
            text_studenta = st.text_area("Napiš svůj text zde:", height=300, placeholder="Začni psát svůj slohový útvar...")
            if st.form_submit_button("📤 Odeslat k hodnocení"):
                if len(text_studenta.strip()) < 100:
                    st.error("Text je příliš krátký. Napiš alespoň 100 znaků.")
                else:
                    with st.spinner("AI hodnotí tvůj text..."):
                        try:
                            tema_info = f"Téma: {st.session_state.slohovka_tema}" if st.session_state.slohovka_tema else ""
                            prompt = f"""Jsi zkušený učitel češtiny hodnotící maturitní slohovou práci.
{tema_info}
Útvar: {utvar_hodnoceni}

Text studenta:
{text_studenta}

Ohodnoť práci podle těchto kritérií:
1. **Splnění útvarových požadavků** (0-5 bodů)
2. **Kompozice a struktura** (0-5 bodů)
3. **Jazyková správnost** (0-5 bodů)
4. **Stylistika a vyjadřování** (0-5 bodů)
5. **Obsah a myšlenky** (0-5 bodů)

Na konci uveď:
- Celkové skóre (X/25)
- Odpovídající maturitní hodnocení (výborně/chvalitebně/dobře/dostatečně/nedostatečně)
- 3 konkrétní rady co zlepšit
- 1 věc co se povedla

Buď přísný ale spravedlivý. Piš česky."""
                            r_text = groq_generate(prompt)
                            st.session_state.slohovka_hodnoceni = r_text
                            pridat_xp(user_id, "slohovka_hodnocena", 15)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Chyba: {e}")

        if st.session_state.slohovka_hodnoceni:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<span class="badge" style="color:#4ade80;background:rgba(74,222,128,0.1);border-color:rgba(74,222,128,0.3);">Hodnocení AI</span>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="card" style="--accent:#4ade80;margin-top:12px;">
                <div style="color:#e0eaff;line-height:1.8;">{st.session_state.slohovka_hodnoceni.replace(chr(10),'<br>')}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔄 Nové hodnocení"):
                st.session_state.slohovka_hodnoceni = None
                st.rerun()

    with tab_rady:
        st.markdown("<br>", unsafe_allow_html=True)
        for utvar_nazev, popis in UTVARY.items():
            st.markdown(f"""
            <div class="card" style="--accent:#7c3aed;margin-bottom:8px;">
                <div style="font-family:'Syne',sans-serif;font-weight:700;color:#fff;margin-bottom:6px;">{utvar_nazev}</div>
                <p style="color:#8899bb;font-size:13px;margin:0;">{popis}</p>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# SEKCE: FLASHKARTY
# ══════════════════════════════════════════════
elif sekce == "🃏 Flashkarty":
    st.markdown('<span class="badge">Flashkarty</span><h1 style="margin-top:8px;">Opakování s kartičkami</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#566a8a;'>Za každou správnou kartu získáš XP!</p>", unsafe_allow_html=True)

    col_l, col_r = st.columns([1,2])
    with col_l:
        predmet_vyber = st.selectbox("Předmět:", ["automatizace","cestina"],
            format_func=lambda x: "🤖 Automatizace" if x=="automatizace" else "📚 Český jazyk")
    try:
        okruhy_r = supabase.table("flashcards").select("okruh").eq("predmet",predmet_vyber).execute()
        okruhy = sorted(list(set(r["okruh"] for r in okruhy_r.data)))
    except:
        okruhy = []
    with col_r:
        okruh_vyber = st.selectbox("Okruh:", ["Vše"] + okruhy) if okruhy else st.selectbox("Okruh:", ["Vše"])

    st.markdown("---")

    if okruhy:
        try:
            q = supabase.table("flashcards").select("*").eq("predmet",predmet_vyber)
            if okruh_vyber and okruh_vyber != "Vše":
                q = q.eq("okruh",okruh_vyber)
            karty = q.execute().data
        except:
            karty = []

        klic = f"{predmet_vyber}_{okruh_vyber}"
        if st.session_state.flash_okruh != klic:
            st.session_state.flash_okruh = klic
            st.session_state.flash_index = 0
            st.session_state.flash_zobrazit_odpoved = False
            st.session_state.flash_karty = karty
            st.session_state.flash_session_stats = {"znam":0,"tezke":0,"neznam":0}

        karty = st.session_state.flash_karty
        if not karty:
            st.info("Pro tento výběr nejsou flashkarty. Přidej je v Admin panelu.")
        else:
            idx = st.session_state.flash_index % len(karty)
            karta = karty[idx]
            stats = st.session_state.flash_session_stats

            st.markdown(f'<div style="display:flex;justify-content:space-between;margin-bottom:8px;"><span style="font-family:\'Space Mono\',monospace;font-size:12px;color:#566a8a;">Karta {idx+1} / {len(karty)}</span><span style="font-family:\'Space Mono\',monospace;font-size:12px;"><span style="color:#4ade80;">✓ {stats["znam"]}</span> &nbsp;<span style="color:#facc15;">~ {stats["tezke"]}</span> &nbsp;<span style="color:#f87171;">✗ {stats["neznam"]}</span></span></div>', unsafe_allow_html=True)
            st.progress(idx / len(karty))

            obtiznost_barva = {"1":"#4ade80","2":"#facc15","3":"#f87171"}.get(str(karta.get("obtiznost",1)),"#00c8ff")
            obtiznost_text = {"1":"Lehká","2":"Střední","3":"Těžká"}.get(str(karta.get("obtiznost",1)),"")
            st.markdown(f'<div class="flashcard-front"><div><div style="font-family:\'Space Mono\',monospace;font-size:11px;color:{obtiznost_barva};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:16px;">{obtiznost_text} · {karta["okruh"]}</div><div class="flashcard-question">{karta["otazka"]}</div></div></div>', unsafe_allow_html=True)

            if not st.session_state.flash_zobrazit_odpoved:
                if st.button("💡 Zobrazit odpověď"):
                    st.session_state.flash_zobrazit_odpoved = True
                    st.rerun()
            else:
                st.markdown(f'<div class="flashcard-answer"><div style="font-family:\'Space Mono\',monospace;font-size:11px;color:#4ade80;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:12px;">Odpověď</div><div class="flashcard-answer-text">{karta["odpoved"]}</div></div>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center;color:#566a8a;font-size:13px;'>Jak ti to šlo?</p>", unsafe_allow_html=True)
                ca, cb, cc = st.columns(3, gap="medium")

                def ohodnotit(hodnoceni, xp_gain):
                    try:
                        ex = supabase.table("flashcard_progress").select("id,pocet_spravne,pocet_spatne").eq("user_id",user_id).eq("flashcard_id",karta["id"]).execute()
                        if ex.data:
                            upd = {"hodnoceni":hodnoceni,"posledni_opak":datetime.now().isoformat()}
                            if hodnoceni=="znam": upd["pocet_spravne"]=ex.data[0].get("pocet_spravne",0)+1
                            else: upd["pocet_spatne"]=ex.data[0].get("pocet_spatne",0)+1
                            supabase.table("flashcard_progress").update(upd).eq("id",ex.data[0]["id"]).execute()
                        else:
                            supabase.table("flashcard_progress").insert({"user_id":user_id,"flashcard_id":karta["id"],"hodnoceni":hodnoceni,"pocet_spravne":1 if hodnoceni=="znam" else 0,"pocet_spatne":0 if hodnoceni=="znam" else 1}).execute()
                        if xp_gain > 0: pridat_xp(user_id,f"flashkarta_{hodnoceni}",xp_gain)
                    except: pass
                    st.session_state.flash_session_stats[hodnoceni]+=1
                    st.session_state.flash_index+=1
                    st.session_state.flash_zobrazit_odpoved=False

                with ca:
                    if st.button("✅ Znám to!", key="fz"): ohodnotit("znam",XP_FLASHKARTA_ZNAM); st.rerun()
                with cb:
                    if st.button("😅 Skoro", key="ft"): ohodnotit("tezke",XP_FLASHKARTA_TEZKE); st.rerun()
                with cc:
                    if st.button("❌ Neznám", key="fn"): ohodnotit("neznam",0); st.rerun()

            if st.session_state.flash_index >= len(karty) and not st.session_state.flash_zobrazit_odpoved:
                st.balloons()
                celkem_xp = stats["znam"]*XP_FLASHKARTA_ZNAM+stats["tezke"]*XP_FLASHKARTA_TEZKE
                st.markdown(f'<div class="card" style="--accent:#ffd700;text-align:center;"><div style="font-size:3rem;margin-bottom:12px;">🎉</div><div style="font-family:\'Syne\',sans-serif;font-size:1.4rem;font-weight:800;color:#fff;">Dokončil jsi celou sadu!</div><p style="color:#566a8a;margin:8px 0 16px;">✅ {stats["znam"]} znám &nbsp;|&nbsp; 😅 {stats["tezke"]} skoro &nbsp;|&nbsp; ❌ {stats["neznam"]} neznám</p><span class="xp-badge">+{celkem_xp} XP získáno!</span></div>', unsafe_allow_html=True)
                if st.button("🔄 Znovu od začátku"):
                    st.session_state.flash_index=0
                    st.session_state.flash_session_stats={"znam":0,"tezke":0,"neznam":0}
                    st.rerun()
    else:
        st.warning("Zatím nejsou přidány žádné flashkarty. Přidej je v Admin panelu.")

# ══════════════════════════════════════════════
# SEKCE: LEADERBOARD
# ══════════════════════════════════════════════
elif sekce == "🏆 Leaderboard":
    st.markdown('<span class="badge">Soutěž</span><h1 style="margin-top:8px;">Leaderboard</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#566a8a;'>Kdo se nejvíc připravuje na maturitu? 🏆</p>", unsafe_allow_html=True)
    st.markdown("---")
    try:
        users_r = supabase.table("users").select("id,display_name,username").eq("is_admin",False).execute()
        xp_r = supabase.table("xp_log").select("user_id,xp_ziskano").execute()
        xp_by = {}
        akt_by = {}
        for row in xp_r.data:
            uid = row["user_id"]
            xp_by[uid] = xp_by.get(uid,0) + row["xp_ziskano"]
            akt_by[uid] = akt_by.get(uid,0) + 1
        rows = sorted([{"display_name":u["display_name"],"username":u["username"],"celkove_xp":xp_by.get(u["id"],0),"pocet_aktivit":akt_by.get(u["id"],0)} for u in users_r.data], key=lambda x: x["celkove_xp"], reverse=True)

        if not rows:
            st.info("Zatím žádná data. Začni sbírat XP!")
        else:
            medals = {1:("🥇","rank-1"),2:("🥈","rank-2"),3:("🥉","rank-3")}
            for i, row in enumerate(rows, 1):
                medal, cls = medals.get(i,("",""))
                je_ja = "border-color:rgba(0,200,255,0.5)!important;" if row["username"]==user["username"] else ""
                ja_tag = '<span style="font-size:11px;color:#00c8ff;margin-left:8px;">(ty)</span>' if row["username"]==user["username"] else ""
                st.markdown(f'<div class="lb-row" style="{je_ja}"><div class="lb-rank {cls}">{medal or f"#{i}"}</div><div class="lb-name">{row["display_name"]}{ja_tag}</div><div style="font-size:12px;color:#566a8a;font-family:\'Space Mono\',monospace;margin-right:16px;">{row["pocet_aktivit"]} aktivit</div><div class="lb-xp">⚡ {row["celkove_xp"]} XP</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="card" style="--accent:#ffd700;"><div style="font-family:\'Syne\',sans-serif;font-weight:700;color:#fff;margin-bottom:12px;">⚡ Jak získat XP?</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;"><div style="font-size:13px;color:#a8bbd8;">✅ Flashkarta „Znám to"</div><div style="font-family:\'Space Mono\',monospace;font-size:13px;color:#ffd700;">+5 XP</div><div style="font-size:13px;color:#a8bbd8;">😅 Flashkarta „Skoro"</div><div style="font-family:\'Space Mono\',monospace;font-size:13px;color:#ffd700;">+2 XP</div><div style="font-size:13px;color:#a8bbd8;">📝 Správná odpověď v kvízu</div><div style="font-family:\'Space Mono\',monospace;font-size:13px;color:#ffd700;">+10 XP</div><div style="font-size:13px;color:#a8bbd8;">🗣️ Dokončená AI zkouška</div><div style="font-family:\'Space Mono\',monospace;font-size:13px;color:#ffd700;">+30 XP</div><div style="font-size:13px;color:#a8bbd8;">✍️ Odevzdaná slohovka</div><div style="font-family:\'Space Mono\',monospace;font-size:13px;color:#ffd700;">+15 XP</div></div></div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Chyba: {e}")

# ══════════════════════════════════════════════
# SEKCE: AI ZKOUŠKA
# ══════════════════════════════════════════════
elif sekce == "🗣️ AI Zkouška":
    st.markdown('<span class="badge">Simulace</span><h1 style="margin-top:8px;">AI Zkouška nanočisto</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#566a8a;'>AI hraje roli maturitní komise. Odpovídej jako u skutečné zkoušky.</p>", unsafe_allow_html=True)
    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        zkouska_predmet = st.selectbox("Předmět:", ["🤖 Automatizace a Robotika","📚 Český jazyk"])
    with col_r:
        if "Automatizace" in zkouska_predmet:
            seznam_z = [f"{i}. {n}" for i,n in enumerate(["Číselné soustavy","Kódy a kódování","Logické funkce 1","Logické funkce 2","Logické členy","Kombinační logické obvody 1","Kombinační logické obvody 2","Sekvenční logické obvody 1","Sekvenční logické obvody 2","Paměti"],1)]
        else:
            seznam_z = ["Robinson Crusoe","Antigona","Romeo a Julie","Lakomec","Máj","Havran","Revizor","Malý princ","R.U.R.","Audience","Kafka: Proměna","Orwell: Farma zvířat"]
        zkouska_okruh = st.selectbox("Okruh / Dílo:", seznam_z)

    if st.session_state.chat_okruh != zkouska_okruh:
        st.session_state.chat_messages = []
        st.session_state.chat_okruh = zkouska_okruh
        material = ""
        if "Automatizace" in zkouska_predmet:
            cislo = zkouska_okruh.split(".")[0]
            cesta_z = f"obsah/{cislo}.md"
            if os.path.exists(cesta_z):
                with open(cesta_z,"r",encoding="utf-8") as f:
                    material = f.read()[:3000]
        system_prompt = f"""Jsi přísná, ale spravedlivá maturitní komise na SPŠOL v Olomouci.
Zkoušíš studenta z tématu: {zkouska_okruh} (předmět: {zkouska_predmet}).
{'Podkladový materiál: ' + material if material else ''}
PRAVIDLA: Začni úvodní otázkou. Po každé odpovědi polož doplňující otázku. Po 4-5 výměnách ukonči zkoušku a dej hodnocení 1-5 s komentářem. Buď náročný. Mluv česky, formálně. NIKDY neprozrazuj odpovědi předem.
Zahaj zkoušku první otázkou."""
        with st.spinner("Komise se připravuje..."):
            try:
                uvod = groq_generate(system_prompt)
                st.session_state.chat_messages = [{"role":"assistant","content":uvod}]
            except Exception as e:
                st.error(f"Chyba: {e}")

    for msg in st.session_state.chat_messages:
        if msg["role"] == "assistant":
            st.markdown(f'<div class="card" style="--accent:#f43f5e;margin-bottom:8px;"><div style="font-family:\'Space Mono\',monospace;font-size:11px;color:#f43f5e;text-transform:uppercase;margin-bottom:8px;">🎓 Komise</div><p style="margin:0;color:#e0eaff;">{msg["content"]}</p></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="card" style="--accent:#00c8ff;margin-bottom:8px;margin-left:40px;"><div style="font-family:\'Space Mono\',monospace;font-size:11px;color:#00c8ff;text-transform:uppercase;margin-bottom:8px;">👤 Ty</div><p style="margin:0;color:#e0eaff;">{msg["content"]}</p></div>', unsafe_allow_html=True)

    if st.session_state.chat_messages:
        with st.form("zkouska_form", clear_on_submit=True):
            odpoved_s = st.text_area("Tvoje odpověď:", height=100, placeholder="Piš jako bys mluvil u tabule...")
            if st.form_submit_button("Odpovědět →"):
                if odpoved_s.strip():
                    st.session_state.chat_messages.append({"role":"user","content":odpoved_s})
                    konverzace = "\n".join([f"{'Komise' if m['role']=='assistant' else 'Student'}: {m['content']}" for m in st.session_state.chat_messages])
                    prompt_k = f"Pokračuj jako maturitní komise.\n{konverzace}\nPokud bylo 4-5 kol, ukonči zkoušku a dej hodnocení (číslo 1-5) s komentářem."
                    with st.spinner("Komise přemýšlí..."):
                        try:
                            komise_odpoved = groq_generate(prompt_k)
                            odpoved_komise = uvod
                            st.session_state.chat_messages.append({"role":"assistant","content":odpoved_komise})
                            if any(x in odpoved_komise.lower() for x in ["hodnocení","hodnotím","výborně","chvalitebně","dobrý","dostatečně","nedostatečně"]):
                                pridat_xp(user_id,"zkouska_dokoncena",XP_ZKOUSKA)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Chyba: {e}")
        if st.button("🔄 Nová zkouška"):
            st.session_state.chat_messages = []
            st.session_state.chat_okruh = None
            st.rerun()

# ══════════════════════════════════════════════
# SEKCE: ADMIN PANEL
# ══════════════════════════════════════════════
elif sekce == "⚙️ Admin panel" and is_admin:
    st.markdown('<span class="badge">Admin</span><h1 style="margin-top:8px;">Admin panel</h1>', unsafe_allow_html=True)
    st.markdown("---")
    tab_zaci, tab_ip, tab_karty, tab_stats = st.tabs(["👥  Žáci","🔍  IP Monitoring","🃏  Flashkarty","📊  Statistiky"])

    # ── ŽÁCI ──
    with tab_zaci:
        st.subheader("Přidat nového žáka")
        with st.form("pridat_zaka"):
            c1,c2 = st.columns(2)
            with c1:
                nu = st.text_input("Username", placeholder="novak_jan")
                nd = st.text_input("Zobrazované jméno", placeholder="Jan Novák")
            with c2:
                nh = st.text_input("Heslo", type="password")
                na = st.checkbox("Admin účet")
            if st.form_submit_button("➕ Přidat žáka"):
                try:
                    supabase.table("users").insert({"username":nu,"password_hash":hash_password(nh),"display_name":nd,"is_admin":na}).execute()
                    st.success(f"Žák {nd} přidán!")
                except Exception as e:
                    st.error(f"Chyba: {e}")

        st.markdown("---")
        st.subheader("Seznam žáků")
        try:
            uzivatele = supabase.table("users").select("id,username,display_name,is_admin,zablokovany").execute()
            for u in uzivatele.data:
                col_info, col_btn = st.columns([4,1])
                with col_info:
                    role = "👑 Admin" if u["is_admin"] else "👤 Žák"
                    zablokovany = " 🔴 ZABLOKOVÁN" if u.get("zablokovany") else ""
                    st.markdown(f"`{u['username']}` — **{u['display_name']}** ({role}){zablokovany}")
                with col_btn:
                    if not u["is_admin"]:
                        if u.get("zablokovany"):
                            if st.button("✅ Odblokovat", key=f"unblock_{u['id']}"):
                                supabase.table("users").update({"zablokovany":False}).eq("id",u["id"]).execute()
                                st.rerun()
                        else:
                            if st.button("🚫 Blokovat", key=f"block_{u['id']}"):
                                supabase.table("users").update({"zablokovany":True}).eq("id",u["id"]).execute()
                                st.rerun()
        except Exception as e:
            st.error(f"Chyba: {e}")

    # ── IP MONITORING ──
    with tab_ip:
        st.subheader("Přihlášení a IP adresy")
        st.markdown("<p style='color:#566a8a;font-size:13px;'>Více než 3 různé IP adresy na jeden účet = podezření ze sdílení loginu.</p>", unsafe_allow_html=True)
        try:
            # Nejdřív zkus jestli tabulka existuje
            log_r = supabase.table("login_log").select("user_id,ip_adresa,cas").order("cas",desc=True).execute()
            users_r = supabase.table("users").select("id,display_name,username").execute()
            users_map = {u["id"]:u for u in users_r.data}

            # Seskup podle uživatele
            by_user = {}
            for row in log_r.data:
                uid = row["user_id"]
                if uid not in by_user:
                    by_user[uid] = {"ip_set":set(),"logy":[]}
                by_user[uid]["ip_set"].add(row["ip_adresa"])
                by_user[uid]["logy"].append(row)

            if not by_user:
                st.info("Zatím žádné záznamy přihlášení.")
            else:
                for uid, data in by_user.items():
                    u_info = users_map.get(uid, {"display_name":"Neznámý","username":"?"})
                    pocet_ip = len(data["ip_set"])
                    posledni = data["logy"][0]["cas"][:16].replace("T"," ") if data["logy"] else "?"

                    css_class = "ip-warning" if pocet_ip > 2 else "ip-ok"
                    warning = "⚠️ Podezřelé — více IP!" if pocet_ip > 2 else "✅ OK"

                    st.markdown(f"""
                    <div class="{css_class}">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                                <strong style="color:#fff;">{u_info['display_name']}</strong>
                                <span style="font-family:'Space Mono',monospace;font-size:11px;color:#566a8a;margin-left:8px;">@{u_info['username']}</span>
                            </div>
                            <div style="text-align:right;">
                                <span style="font-family:'Space Mono',monospace;font-size:12px;">{warning}</span><br>
                                <span style="font-size:11px;color:#566a8a;">{pocet_ip} různých IP · poslední: {posledni}</span>
                            </div>
                        </div>
                        <div style="margin-top:8px;font-family:'Space Mono',monospace;font-size:11px;color:#566a8a;">
                            IP adresy: {', '.join(data['ip_set'])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Tabulka login_log neexistuje. Spusť SQL v Supabase:\n\n`CREATE TABLE login_log (id uuid primary key default gen_random_uuid(), user_id uuid references users(id) on delete cascade, ip_adresa text, cas timestamp default now());`")

    # ── FLASHKARTY ──
    with tab_karty:
        st.subheader("Přidat novou flashkartu")
        with st.form("nova_karta"):
            c1,c2 = st.columns(2)
            with c1:
                kp = st.selectbox("Předmět:", ["automatizace","cestina"])
                ko = st.text_input("Okruh:", placeholder="1. Číselné soustavy")
            with c2:
                kob = st.selectbox("Obtížnost:", [1,2,3], format_func=lambda x:{1:"Lehká",2:"Střední",3:"Těžká"}[x])
            kq = st.text_area("Otázka:", height=80)
            ka = st.text_area("Odpověď:", height=100)
            if st.form_submit_button("➕ Přidat kartu"):
                try:
                    supabase.table("flashcards").insert({"predmet":kp,"okruh":ko,"otazka":kq,"odpoved":ka,"obtiznost":kob}).execute()
                    st.success("Karta přidána!")
                except Exception as e:
                    st.error(f"Chyba: {e}")

        st.markdown("---")
        st.subheader("Hromadný import (JSON)")
        json_import = st.text_area("Vlož JSON:", height=120, placeholder='[{"predmet":"automatizace","okruh":"1. Číselné soustavy","otazka":"?","odpoved":"...","obtiznost":2}]')
        if st.button("📥 Importovat"):
            try:
                data = json.loads(json_import)
                supabase.table("flashcards").insert(data).execute()
                st.success(f"Importováno {len(data)} karet!")
            except Exception as e:
                st.error(f"Chyba: {e}")

    # ── STATISTIKY ──
    with tab_stats:
        st.subheader("Aktivita třídy")
        try:
            users_r = supabase.table("users").select("id,display_name").eq("is_admin",False).execute()
            xp_r = supabase.table("xp_log").select("user_id,xp_ziskano").execute()
            xp_by = {}
            for row in xp_r.data:
                xp_by[row["user_id"]] = xp_by.get(row["user_id"],0)+row["xp_ziskano"]
            sorted_users = sorted(users_r.data, key=lambda u: xp_by.get(u["id"],0), reverse=True)
            max_xp = max((xp_by.get(u["id"],0) for u in sorted_users), default=1)
            for u in sorted_users:
                xp_val = xp_by.get(u["id"],0)
                pct = int(xp_val/max_xp*100) if max_xp>0 else 0
                st.markdown(f'<div style="margin-bottom:10px;"><div style="display:flex;justify-content:space-between;margin-bottom:4px;"><span style="color:#e0eaff;font-size:14px;">{u["display_name"]}</span><span style="font-family:\'Space Mono\',monospace;font-size:12px;color:#ffd700;">⚡ {xp_val} XP</span></div><div style="background:#1a2035;border-radius:4px;height:6px;"><div style="background:linear-gradient(90deg,#00c8ff,#7c3aed);width:{pct}%;height:100%;border-radius:4px;"></div></div></div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Chyba: {e}")
