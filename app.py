"""
AI Budget Tracker — Streamlit Frontend
Backend by Arda Bölükbaşı & Kutay Özdemir
Run: streamlit run app.py
"""

import streamlit as st
import requests
import pandas as pd
import time

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BudgetAI · Tracker",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Backend URL ──────────────────────────────────────────────────────────────
API_BASE = "http://127.0.0.1:8000"   # Change if your FastAPI runs elsewhere

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;600;700&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: #050c1a !important;
    color: #e0e8f8 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Kill Streamlit chrome */
#MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], header { display: none !important; }

/* Full-width block container */
.block-container {
    max-width: 100% !important;
    padding: 0 3rem !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a1628; }
::-webkit-scrollbar-thumb { background: #1e3a6e; border-radius: 3px; }

/* ── Streamlit input overrides ── */
[data-testid="stTextInput"] input,
[data-testid="stTextInput"] input:focus {
    background: rgba(14,28,60,0.7) !important;
    border: 1px solid rgba(56,100,210,0.4) !important;
    border-radius: 10px !important;
    color: #e0e8f8 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.6rem 1rem !important;
    box-shadow: none !important;
    transition: border-color .2s;
}
[data-testid="stTextInput"] input:focus {
    border-color: rgba(56,100,210,0.9) !important;
    box-shadow: 0 0 0 3px rgba(56,100,210,0.15) !important;
}
[data-testid="stTextInput"] label {
    color: #8fa8d0 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
}

/* ── Streamlit native button (sidebar/misc) ── */
[data-testid="baseButton-secondary"] {
    background: transparent !important;
    border: 1px solid #1e3a6e !important;
    color: #8fa8d0 !important;
    border-radius: 8px !important;
}

/* ── Altair / Vega chart dark theme patch ── */
.vega-embed {
    background: transparent !important;
}
.vega-embed canvas {
    border-radius: 12px;
}

/* ── Spinner text ── */
[data-testid="stSpinner"] p {
    color: #8fa8d0 !important;
    font-size: 0.9rem !important;
}

/* ── Divider ── */
hr { border-color: rgba(56,100,210,0.2) !important; }

/* ── Tab styling ── */
[data-testid="stTabs"] [role="tab"] {
    color: #8fa8d0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    border-bottom: 2px solid transparent !important;
    padding-bottom: 8px !important;
    transition: color .2s;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #5b8dee !important;
    border-bottom-color: #5b8dee !important;
    background: transparent !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background: #5b8dee !important;
}
</style>
""", unsafe_allow_html=True)


# ─── Session State Defaults ────────────────────────────────────────────────────
for key, val in [("authenticated", False), ("user_id", ""), ("display_name", ""),
                  ("dashboard_data", None), ("view", "login")]:
    if key not in st.session_state:
        st.session_state[key] = val


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def api_register(user_id: str, display_name: str, email: str):
    try:
        r = requests.post(
            f"{API_BASE}/api/register-user",
            json={"user_id": user_id, "display_name": display_name, "email": email},
            timeout=10,
        )
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach the backend. Is FastAPI running?"
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return None, str(e)


def api_analyze(user_id: str, period: str = "month"):
    try:
        r = requests.get(
            f"{API_BASE}/api/analyze-spending",
            params={"user_id": user_id, "period": period},
            timeout=120,
        )
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach the backend. Is FastAPI running?"
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return None, str(e)


def format_currency(amount) -> str:
    try:
        return f"₺{float(amount):,.2f}"
    except (TypeError, ValueError):
        return str(amount)


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN / REGISTER VIEW
# ══════════════════════════════════════════════════════════════════════════════

def render_login():
    # ── Animated background canvas ──
    st.markdown("""
    <style>
    .login-bg {
        position: fixed; inset: 0; z-index: -1;
        background:
            radial-gradient(ellipse 80% 60% at 20% 10%, rgba(20,50,120,0.55) 0%, transparent 60%),
            radial-gradient(ellipse 60% 50% at 80% 80%, rgba(10,30,90,0.6) 0%, transparent 55%),
            #050c1a;
    }
    .login-card {
        background: rgba(10,20,50,0.75);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(56,100,210,0.25);
        border-radius: 24px;
        padding: 3rem 2.5rem;
        box-shadow:
            0 30px 80px rgba(0,0,10,0.6),
            inset 0 1px 0 rgba(255,255,255,0.07);
        max-width: 480px;
        margin: 0 auto;
    }
    .login-logo {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #5b8dee 0%, #a78bfa 60%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem;
    }
    .login-tagline {
        color: #8fa8d0;
        font-size: 0.9rem;
        margin-bottom: 2.5rem;
        letter-spacing: 0.02em;
    }
    .tab-btn {
        display: inline-block;
        padding: 0.45rem 1.4rem;
        border-radius: 8px;
        font-size: 0.88rem;
        font-weight: 600;
        cursor: pointer;
        transition: all .2s;
        letter-spacing: 0.03em;
    }
    .tab-active {
        background: linear-gradient(135deg, #3b65d4, #6244bb);
        color: #fff !important;
        box-shadow: 0 4px 16px rgba(59,101,212,0.4);
    }
    .tab-inactive {
        background: transparent;
        color: #8fa8d0;
        border: 1px solid rgba(56,100,210,0.25);
    }
    </style>
    <div class="login-bg"></div>
    """, unsafe_allow_html=True)

    # Center the card
    _, center, _ = st.columns([1, 1.1, 1])
    with center:
        st.markdown("""
        <div class="login-card">
          <div class="login-logo">💎 BudgetAI</div>
          <div class="login-tagline">Powered by Gemini · Plaid · Firebase</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Mode toggle
        tab1, tab2 = st.tabs(["🔑  Sign In", "✨  Create Account"])

        # ── SIGN IN ──
        with tab1:
            with st.form("login_form", clear_on_submit=False):
                uid = st.text_input("User ID", placeholder="e.g. user_abc123")
                submitted = st.form_submit_button("Sign In →", use_container_width=True)
                if submitted:
                    if not uid.strip():
                        st.error("Please enter your User ID.")
                    else:
                        st.session_state.user_id = uid.strip()
                        st.session_state.display_name = uid.strip()
                        st.session_state.authenticated = True
                        st.session_state.view = "dashboard"
                        st.rerun()

        # ── REGISTER ──
        with tab2:
            with st.form("register_form", clear_on_submit=False):
                r_uid   = st.text_input("User ID *",      placeholder="Unique identifier")
                r_name  = st.text_input("Display Name",   placeholder="Your name")
                r_email = st.text_input("Email",          placeholder="you@example.com")
                submitted = st.form_submit_button("Create Account →", use_container_width=True)
                if submitted:
                    if not r_uid.strip():
                        st.error("User ID is required.")
                    else:
                        with st.spinner("Registering…"):
                            data, err = api_register(r_uid.strip(), r_name.strip(), r_email.strip())
                        if err:
                            st.error(f"❌ {err}")
                        else:
                            st.success("Account created! Signing you in…")
                            time.sleep(1)
                            st.session_state.user_id = r_uid.strip()
                            st.session_state.display_name = r_name.strip() or r_uid.strip()
                            st.session_state.authenticated = True
                            st.session_state.view = "dashboard"
                            st.rerun()

        # ── Footer note ──
        st.markdown("""
        <div style="text-align:center;margin-top:1.8rem;color:#4a6090;font-size:0.78rem;">
            Backend by <strong style="color:#8fa8d0">Arda Bölükbaşı</strong>
            &amp; <strong style="color:#8fa8d0">Kutay Özdemir</strong>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD VIEW
# ══════════════════════════════════════════════════════════════════════════════

def render_dashboard():

    # ── Dashboard CSS ──
    st.markdown("""
    <style>
    .dash-bg {
        position: fixed; inset: 0; z-index: -1;
        background:
            radial-gradient(ellipse 70% 50% at 5% 0%, rgba(15,35,100,0.5) 0%, transparent 55%),
            radial-gradient(ellipse 50% 40% at 95% 100%, rgba(10,25,80,0.45) 0%, transparent 50%),
            #050c1a;
    }

    /* ── Topbar ── */
    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.2rem 0 1.4rem 0;
        border-bottom: 1px solid rgba(56,100,210,0.18);
        margin-bottom: 1.6rem;
    }
    .topbar-logo {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.45rem;
        font-weight: 700;
        background: linear-gradient(135deg, #5b8dee, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }
    .topbar-user {
        color: #8fa8d0;
        font-size: 0.88rem;
        display: flex;
        align-items: center;
        gap: .5rem;
    }
    .topbar-user span {
        background: rgba(56,100,210,0.18);
        border: 1px solid rgba(56,100,210,0.3);
        border-radius: 20px;
        padding: .25rem .9rem;
        font-weight: 600;
        color: #c0d4f8;
    }

    /* ── Sandbox Banner ── */
    .sandbox-banner {
        background: linear-gradient(90deg, rgba(230,130,0,0.18), rgba(230,100,0,0.12));
        border: 1px solid rgba(230,130,0,0.45);
        border-radius: 14px;
        padding: 0.9rem 1.4rem;
        margin-bottom: 1.4rem;
        display: flex;
        align-items: center;
        gap: 0.9rem;
        animation: pulse-orange 2.5s infinite;
    }
    @keyframes pulse-orange {
        0%,100% { box-shadow: 0 0 0 0 rgba(230,130,0,0); }
        50%      { box-shadow: 0 0 18px 4px rgba(230,130,0,0.18); }
    }
    .sandbox-icon { font-size: 1.4rem; }
    .sandbox-text { color: #f5a742; font-weight: 600; font-size: 0.92rem; }
    .sandbox-sub  { color: #c07a20; font-size: 0.8rem; margin-top: .1rem; }

    /* ── Metric Cards ── */
    .metric-card {
        border-radius: 20px;
        padding: 1.8rem 2rem;
        position: relative;
        overflow: hidden;
        min-height: 145px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 20px 50px rgba(0,0,0,0.45);
        transition: transform .25s, box-shadow .25s;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 30px 70px rgba(0,0,0,0.55);
    }
    .metric-card::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: inherit;
        background: inherit;
        opacity: 0;
    }
    .card-blue {
        background: linear-gradient(135deg, #1a3a8f 0%, #0f2060 60%, #081540 100%);
        border: 1px solid rgba(91,141,238,0.35);
    }
    .card-purple {
        background: linear-gradient(135deg, #2d1b6e 0%, #1a0f4a 60%, #0f0930 100%);
        border: 1px solid rgba(167,139,250,0.35);
    }
    .card-teal {
        background: linear-gradient(135deg, #0d4a5a 0%, #072d3a 60%, #041820 100%);
        border: 1px solid rgba(56,189,248,0.3);
    }
    .metric-label {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: rgba(200,220,255,0.55);
        display: flex;
        align-items: center;
        gap: .4rem;
    }
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.1rem;
        font-weight: 700;
        color: #e8f0ff;
        letter-spacing: -0.03em;
        line-height: 1;
    }
    .metric-sub {
        font-size: 0.78rem;
        color: rgba(160,190,240,0.5);
        margin-top: .3rem;
    }
    .card-glow-blue  { position:absolute; width:120px; height:120px; border-radius:50%;
                       background:rgba(91,141,238,0.18); filter:blur(35px);
                       bottom:-30px; right:-20px; pointer-events:none; }
    .card-glow-purple{ position:absolute; width:110px; height:110px; border-radius:50%;
                       background:rgba(167,139,250,0.18); filter:blur(35px);
                       bottom:-25px; right:-15px; pointer-events:none; }
    .card-glow-teal  { position:absolute; width:110px; height:110px; border-radius:50%;
                       background:rgba(56,189,248,0.15); filter:blur(35px);
                       bottom:-25px; right:-15px; pointer-events:none; }

    /* ── Section headers ── */
    .section-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.05rem;
        font-weight: 600;
        color: #c0d4f8;
        letter-spacing: -0.01em;
        margin-bottom: .8rem;
        display: flex;
        align-items: center;
        gap: .5rem;
    }
    .section-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(56,100,210,0.3), transparent);
        margin-left: .6rem;
    }

    /* ── Chart Container ── */
    .chart-wrap {
        background: rgba(10,20,50,0.65);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(56,100,210,0.2);
        border-radius: 20px;
        padding: 1.5rem 1.5rem 1rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.35);
    }

    /* ── Recent Transactions Row ── */
    .txn-row {
        background: rgba(14, 25, 60, 0.45);
        border: 1px solid rgba(56, 100, 210, 0.15);
        border-radius: 12px;
        padding: 0.9rem 1.2rem;
        margin-bottom: 0.6rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: transform 0.2s, background 0.2s;
    }
    .txn-row:hover {
        background: rgba(18, 32, 76, 0.65);
        transform: translateY(-2px);
    }
    .txn-left {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
    }
    .txn-merchant {
        font-family: 'Space Grotesk', sans-serif;
        color: #e2e8f0;
        font-size: 1.05rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .txn-date {
        color: #6e84a3;
        font-size: 0.85rem;
    }
    .txn-amount {
        font-family: 'Space Grotesk', sans-serif;
        color: #38bdf8;
        font-size: 1.15rem;
        font-weight: 700;
        background: rgba(56, 189, 248, 0.1);
        padding: 0.35rem 0.8rem;
        border-radius: 8px;
        border: 1px solid rgba(56, 189, 248, 0.2);
    }

    /* ── AI Advice Box ── */
    .ai-advice-box {
        background: linear-gradient(135deg,
            rgba(30,15,80,0.85) 0%,
            rgba(20,10,60,0.9) 50%,
            rgba(15,8,50,0.95) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(167,139,250,0.3);
        border-radius: 20px;
        padding: 1.8rem 2rem;
        box-shadow:
            0 20px 50px rgba(0,0,0,0.45),
            inset 0 1px 0 rgba(255,255,255,0.06),
            0 0 40px rgba(167,139,250,0.08);
        position: relative;
        overflow: hidden;
    }
    .ai-advice-box::before {
        content: '';
        position: absolute;
        top: -40px; right: -40px;
        width: 180px; height: 180px;
        border-radius: 50%;
        background: rgba(167,139,250,0.12);
        filter: blur(50px);
        pointer-events: none;
    }
    .ai-badge {
        display: inline-flex;
        align-items: center;
        gap: .4rem;
        background: linear-gradient(135deg, rgba(167,139,250,0.2), rgba(99,102,241,0.25));
        border: 1px solid rgba(167,139,250,0.35);
        border-radius: 20px;
        padding: .3rem .85rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: #c4b5fd;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }
    .ai-advice-text {
        color: #d4e0f8;
        font-size: 0.95rem;
        line-height: 1.75;
        font-weight: 400;
    }

    /* ── Category list ── */
    .cat-row {
        display: flex;
        align-items: center;
        gap: .85rem;
        padding: .65rem 0;
        border-bottom: 1px solid rgba(56,100,210,0.1);
    }
    .cat-row:last-child { border-bottom: none; }
    .cat-icon  { font-size: 1.3rem; width: 2rem; text-align: center; }
    .cat-name  { flex: 1; color: #b0c8f0; font-size: 0.88rem; font-weight: 500; }
    .cat-amount{ font-family: 'Space Grotesk', sans-serif; font-weight: 600;
                 color: #e0ecff; font-size: 0.95rem; }

    /* ── Logout button custom ── */
    .logout-btn {
        background: rgba(200,50,50,0.12);
        border: 1px solid rgba(200,50,50,0.3);
        border-radius: 10px;
        color: #f87171 !important;
        font-size: 0.82rem;
        padding: .35rem .9rem;
        cursor: pointer;
        transition: background .2s;
    }
    .logout-btn:hover { background: rgba(200,50,50,0.22); }

    /* ── Refresh button ── */
    [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #3b65d4, #6244bb) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-family: 'DM Sans', sans-serif !important;
        box-shadow: 0 4px 18px rgba(59,101,212,0.35) !important;
        transition: opacity .2s, transform .15s !important;
    }
    [data-testid="baseButton-primary"]:hover {
        opacity: 0.88 !important;
        transform: translateY(-1px) !important;
    }
    </style>
    <div class="dash-bg"></div>
    """, unsafe_allow_html=True)

    # We'll render the topbar after we ensure data is fetched
    uid = st.session_state.user_id

    # ── Fetch Data ──
    if st.session_state.dashboard_data is None:
        loading_placeholder = st.empty()
        
        # Özel CSS ile ortalanmış dönen yuvarlak ve yazılar
        loading_html = """
        <style>
        .loader-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 40vh;
        }
        .custom-spinner {
            width: 70px;
            height: 70px;
            border: 6px solid rgba(139, 92, 246, 0.2);
            border-radius: 50%;
            border-top-color: #8b5cf6;
            animation: spin 1s cubic-bezier(0.55, 0.085, 0.68, 0.53) infinite;
            margin-bottom: 25px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .loader-text {
            font-size: 1.3rem;
            color: #e2e8f0;
            text-align: center;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .loader-subtext {
            font-size: 1rem;
            color: #94a3b8;
            text-align: center;
        }
        </style>
        <div class="loader-container">
            <div class="custom-spinner"></div>
            <div class="loader-text">🤖 Gemini AI Bütçenizi Analiz Ediyor...</div>
            <div class="loader-subtext">
                Banka işlemleri çekiliyor...<br>
                Yapay Zeka ile kategorize ediliyor...<br>
                Firebase veritabanına işleniyor...
            </div>
        </div>
        """
        
        loading_placeholder.markdown(loading_html, unsafe_allow_html=True)
        
        resp, err = api_analyze(uid)
        
        # Yükleme bitince o UI parçasını sil
        loading_placeholder.empty()

        if err:
            st.error(f"❌ {err}")
            st.info("Make sure your FastAPI backend is running on **http://127.0.0.1:8000**")
            return
        # Backend döner: {"status": "success", "data": {...}}
        # İç "data" sözlüğünü çıkar, yoksa root'u kullan
        if isinstance(resp, dict) and "data" in resp:
            st.session_state.dashboard_data = resp["data"]
        else:
            st.session_state.dashboard_data = resp

    # ── Top Bar (Rendered only after data is loaded) ──
    uid   = st.session_state.user_id
    dname = st.session_state.display_name or uid

    col_logo, col_user, col_logout = st.columns([3, 4, 1])
    with col_logo:
        st.markdown('<div class="topbar-logo">💎 BudgetAI</div>', unsafe_allow_html=True)
    with col_user:
        st.markdown(f"""
        <div class="topbar-user" style="justify-content:flex-end;padding-top:.5rem;">
            <span>👤 {dname}</span>
        </div>
        """, unsafe_allow_html=True)
    with col_logout:
        if st.button("Sign Out", type="secondary", use_container_width=True):
            for k in ["authenticated", "user_id", "display_name", "dashboard_data"]:
                st.session_state[k] = False if k == "authenticated" else ""
            st.session_state.view = "login"
            st.rerun()

    st.markdown('<hr style="margin-bottom:1.4rem;">', unsafe_allow_html=True)

    data = st.session_state.dashboard_data

    # Ensure data is a dictionary (handles corrupted session state)
    if not isinstance(data, dict):
        st.error(f"❌ Invalid data format received from backend. Expected dictionary, got {type(data).__name__}.")
        if st.button("Refresh Data"):
            st.session_state.dashboard_data = None
            st.rerun()
        return

    # Normalize field names (backend uses total_spending, categories, ai_advice)
    total     = data.get("total_spending") or data.get("total_amount") or 0
    cats_raw  = data.get("categories") or data.get("category_breakdown") or []
    ai_advice = data.get("ai_advice") or ""
    src       = data.get("data_source", "sandbox")

    # ── Sandbox Banner ──
    if src in ("sandbox", "plaid_sandbox", "mock"):
        st.markdown("""
        <div class="sandbox-banner">
          <div class="sandbox-icon">⚠️</div>
          <div>
            <div class="sandbox-text">SANDBOX MODE ACTIVE — Mock Data</div>
            <div class="sandbox-sub">Connect a real bank account via Plaid to see live transactions.</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Metric Cards ──
    tx_count = len(cats_raw)
    avg_cat  = (total / tx_count) if tx_count else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="metric-card card-blue">
          <div class="card-glow-blue"></div>
          <div class="metric-label">💰 Total Spending</div>
          <div>
            <div class="metric-value">{format_currency(total)}</div>
            <div class="metric-sub">Current period</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card card-purple">
          <div class="card-glow-purple"></div>
          <div class="metric-label">📊 Categories Tracked</div>
          <div>
            <div class="metric-value">{tx_count}</div>
            <div class="metric-sub">Expense categories</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card card-teal">
          <div class="card-glow-teal"></div>
          <div class="metric-label">📈 Avg per Category</div>
          <div>
            <div class="metric-value">{format_currency(avg_cat)}</div>
            <div class="metric-sub">Period average</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Main Content: Chart + AI Advice ──
    left_col, right_col = st.columns([3, 2], gap="large")

    with left_col:
        st.markdown('<div class="section-title">📊 Spending by Category</div>', unsafe_allow_html=True)

        if cats_raw:
            # Build DataFrame — handle dict or list formats
            rows = []
            for item in cats_raw:
                if isinstance(item, dict):
                    icon  = item.get("icon", "")   or item.get("emoji", "")
                    name  = item.get("name", "")   or item.get("category", "Unknown")
                    amount= item.get("amount", 0)  or item.get("total", 0)
                    label = f"{icon} {name}".strip() if icon else name
                    rows.append({"Category": label, "Amount (₺)": float(amount)})
                else:
                    rows.append({"Category": str(item), "Amount (₺)": 0.0})

            df = pd.DataFrame(rows).sort_values("Amount (₺)", ascending=False)

            st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
            st.bar_chart(
                df.set_index("Category"),
                height=360,
                color="#5b8dee",
                use_container_width=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)

            # Category breakdown list
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-title">🗂️ Category Breakdown</div>', unsafe_allow_html=True)
            st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
            for row in rows:
                name, amt = row["Category"], row["Amount (₺)"]
                parts = name.split(" ", 1)
                icon_part = parts[0] if len(parts) > 1 else "💳"
                name_part = parts[1] if len(parts) > 1 else name
                st.markdown(f"""
                <div class="cat-row">
                  <div class="cat-icon">{icon_part}</div>
                  <div class="cat-name">{name_part}</div>
                  <div class="cat-amount">{format_currency(amt)}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No category data returned from backend.")

    with right_col:
        # ── AI Advice ──
        st.markdown('<div class="section-title">🤖 Gemini AI Advice</div>', unsafe_allow_html=True)
        advice_text = ai_advice if ai_advice else "No advice returned. Try refreshing."
        st.markdown(f"""
        <div class="ai-advice-box">
          <div class="ai-badge">✦ Gemini AI · Personalized Analysis</div>
          <div class="ai-advice-text">{advice_text}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Data Source badge ──
        if src in ("sandbox", "plaid_sandbox", "mock"):
            badge_color, badge_icon, badge_label = "#f5a742", "🔬", "PLAID SANDBOX"
        else:
            badge_color, badge_icon, badge_label = "#34d399", "🏦", "LIVE PLAID"
        st.markdown(f"""
        <div style="
            background: rgba(10,20,50,0.65);
            border: 1px solid rgba(56,100,210,0.2);
            border-radius:14px; padding:1rem 1.3rem;
            display:flex; align-items:center; gap:.7rem;
        ">
          <span style="font-size:1.5rem;">{badge_icon}</span>
          <div>
            <div style="font-size:.72rem;color:#8fa8d0;letter-spacing:.06em;font-weight:600;">DATA SOURCE</div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:1.05rem;font-weight:700;color:{badge_color};">{badge_label}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Refresh button ──
        if st.button("🔄  Refresh Analysis", type="primary", use_container_width=True):
            st.session_state.dashboard_data = None
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Raw JSON expander ──
        with st.expander("🔍 Raw API Response"):
            st.json(data)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Recent Transactions Module ──
    st.markdown('<div class="section-title">📋 Detaylı İşlem Geçmişi (Recent Transactions)</div>', unsafe_allow_html=True)
    
    transactions = data.get("transactions", [])
    if transactions:
        st.markdown('<div class="chart-wrap" style="padding-bottom: 1.5rem;">', unsafe_allow_html=True)
        for txn in transactions:
            merchant = txn.get("merchant_name", "Bilinmeyen İşlem")
            amt = txn.get("amount", 0)
            date = txn.get("date", "Tarih Yok")
            icon = txn.get("icon", "💳")
            
            st.markdown(f"""
            <div class="txn-row">
              <div class="txn-left">
                <div class="txn-merchant"><span style="font-size:1.2rem;">{icon}</span> {merchant}</div>
                <div class="txn-date">{date}</div>
              </div>
              <div class="txn-amount">{format_currency(amt)}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("ℹ️ Şu an için detaylı işlem geçmişi bulunmuyor.")

    # ── Footer ──
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;color:#2a3c60;font-size:0.78rem;padding-bottom:1.5rem;">
        BudgetAI · Backend by <strong style="color:#3d5a90">Arda Bölükbaşı</strong>
        &amp; Frontend by <strong style="color:#3d5a90">Kutay Özdemir & Arda Bölükbaşı</strong>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.authenticated and st.session_state.view == "dashboard":
    render_dashboard()
else:
    render_login()
