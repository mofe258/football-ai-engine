"""
================================================================================
PERSONAL BET — INSTITUTIONAL SPORTS PREDICTION & BETTING INTELLIGENCE PLATFORM
================================================================================
"""

import os
import sys
import time
import types
import requests
import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Any

# =====================================================================
# IMPORT BRIDGE (Handles root vs core/ file locations seamlessly)
# =====================================================================
for mod_name in ['database', 'adapters', 'prediction', 'backtesting']:
    try:
        mod = __import__(mod_name)
        if 'core' not in sys.modules:
            sys.modules['core'] = types.ModuleType('core')
        sys.modules[f'core.{mod_name}'] = mod
    except ImportError:
        pass

try:
    from database import init_db, get_connection
    from adapters import CanonicalFixtureService, APIFootballAdapter, TheOddsAPIAdapter, TelegramTipsterAdapter
    from prediction import DixonColesEngine, MarketPricingEngine
    from backtesting import BacktestService
except ImportError:
    from core.database import init_db, get_connection
    from core.adapters import CanonicalFixtureService, APIFootballAdapter, TheOddsAPIAdapter, TelegramTipsterAdapter
    from core.prediction import DixonColesEngine, MarketPricingEngine
    from core.backtesting import BacktestService

from football_engine import build_or_load_pipeline

# Ensure DB initialized
init_db()

st.set_page_config(
    page_title="Personal Bet — Sports Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def render_html(html_str: str):
    sanitized = " ".join(line.strip() for line in html_str.splitlines() if line.strip())
    if hasattr(st, "html"):
        st.html(sanitized)
    else:
        st.markdown(sanitized, unsafe_allow_html=True)


render_html("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Plus Jakarta Sans", sans-serif !important;
        background-color: #030305 !important;
        background-image: 
            radial-gradient(circle at 10% 10%, rgba(255, 255, 255, 0.08) 0%, transparent 40%),
            radial-gradient(circle at 90% 20%, rgba(0, 240, 255, 0.12) 0%, transparent 50%),
            radial-gradient(circle at 50% 85%, rgba(255, 45, 85, 0.09) 0%, transparent 55%),
            radial-gradient(circle at 25% 65%, rgba(121, 40, 202, 0.1) 0%, transparent 45%) !important;
        background-attachment: fixed !important;
        color: #F8FAFC !important;
        letter-spacing: -0.02em;
        -webkit-font-smoothing: antialiased;
        overflow-x: hidden !important;
    }

    [data-testid="stHeader"] { background: transparent !important; }

    .block-container {
        padding-top: clamp(0.6rem, 2vw, 1.5rem) !important;
        padding-bottom: clamp(2rem, 4vw, 4rem) !important;
        max-width: 1260px !important;
    }

    /* ========================================================= */
    /* REDESIGNED APPLE VISIONOS LIQUID DOCK (ZERO TEXT WRAPPING)*/
    /* ========================================================= */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        scrollbar-width: none !important;
        gap: 8px !important;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 40%, rgba(10, 10, 18, 0.85) 100%) !important;
        backdrop-filter: blur(35px) saturate(200%) !important;
        -webkit-backdrop-filter: blur(35px) saturate(200%) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        border-radius: 9999px !important;
        padding: 6px 10px !important;
        box-shadow: 0 20px 50px -15px rgba(0, 0, 0, 0.9), inset 0 1.5px 1px 0 rgba(255, 255, 255, 0.4) !important;
        margin-bottom: 1.25rem !important;
        align-items: center !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"]::-webkit-scrollbar { display: none !important; }

    /* HIDE ALL RADIO BUTTON CIRCLES AND INPUTS COMPLETELY */
    div[data-testid="stRadio"] [data-baseweb="radio"] > div:first-child,
    div[data-testid="stRadio"] input[type="radio"],
    div[data-testid="stRadio"] svg {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
    }

    /* PREVENT TEXT FROM EVER CLUMPING OR BREAKING APART */
    div[data-testid="stRadio"] div[role="radiogroup"] label {
        flex: 0 0 auto !important;
        white-space: nowrap !important;
        word-break: keep-all !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 8px 18px !important;
        border-radius: 9999px !important;
        cursor: pointer !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        color: #94A3B8 !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        min-height: 38px !important;
        transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label *,
    div[data-testid="stRadio"] div[role="radiogroup"] label p,
    div[data-testid="stRadio"] div[role="radiogroup"] label span {
        white-space: nowrap !important;
        word-break: keep-all !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
        color: #FFFFFF !important;
        background: rgba(255, 255, 255, 0.08) !important;
        transform: translateY(-1px) !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0.06) 50%, rgba(0, 240, 255, 0.22) 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.45) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        box-shadow: 0 10px 25px -5px rgba(0, 240, 255, 0.35), inset 0 1.5px 1px 0 rgba(255, 255, 255, 0.8) !important;
        transform: scale(1.02) !important;
    }

    /* SPECULAR GLASS CARDS */
    .glass-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.09) 0%, rgba(255, 255, 255, 0.02) 35%, rgba(8, 9, 14, 0.85) 75%, rgba(255, 255, 255, 0.04) 100%);
        backdrop-filter: blur(30px) saturate(180%);
        -webkit-backdrop-filter: blur(30px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 26px;
        padding: clamp(1.2rem, 2vw, 1.8rem);
        margin-bottom: 1.25rem;
        box-shadow: 0 25px 50px -18px rgba(0, 0, 0, 0.85), inset 0 1.5px 1.5px 0 rgba(255, 255, 255, 0.65);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .triple-score-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin: 1.2rem 0;
    }
    .score-cell {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 18px;
        padding: 14px 16px;
        box-shadow: inset 0 1px 1px 0 rgba(255, 255, 255, 0.25);
    }
    .score-title {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        color: #94A3B8;
        margin-bottom: 4px;
        font-weight: 700;
    }
    .score-value {
        font-size: 1.35rem;
        font-weight: 900;
        letter-spacing: -0.03em;
    }
    .score-sub {
        font-size: 11px;
        color: #64748B;
        margin-top: 3px;
    }

    .pill-signal {
        padding: 5px 12px;
        border-radius: 9999px;
        font-weight: 800;
        font-size: 11.5px;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }
    .sig-green {
        background: rgba(0, 240, 255, 0.18);
        border: 1px solid rgba(0, 240, 255, 0.5);
        color: #00F0FF;
    }
    .sig-amber {
        background: rgba(255, 184, 0, 0.18);
        border: 1px solid rgba(255, 184, 0, 0.5);
        color: #FFB800;
    }
    .sig-red {
        background: rgba(255, 59, 48, 0.18);
        border: 1px solid rgba(255, 59, 48, 0.5);
        color: #FF6961;
    }

    @media (max-width: 768px) {
        .triple-score-grid { grid-template-columns: 1fr !important; gap: 8px !important; }
        .glass-card { border-radius: 20px !important; padding: 14px !important; }
    }
</style>
""")

@st.cache_resource(show_spinner=False)
def load_ml_engine():
    return build_or_load_pipeline(force_retrain=False)

def main():
    engine = load_ml_engine()

    # Brand Header
    render_html("""
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px; margin-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="background: linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0.05) 50%, rgba(0,240,255,0.3) 100%); border: 1px solid rgba(255,255,255,0.6); width: 34px; height: 34px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-weight: 900; color: #FFF; font-size: 16px; box-shadow: 0 8px 20px rgba(0, 240, 255, 0.3), inset 0 1.5px 1px rgba(255,255,255,0.9);">⚡</div>
            <span style="font-size: 22px; font-weight: 800; letter-spacing: -0.04em;">
                <span style="color: #FFFFFF;">Personal</span>
                <span style="background: linear-gradient(135deg, #00F0FF 0%, #0A84FF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Bet</span>
            </span>
        </div>
        <div style="color: #94A3B8; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; display: flex; align-items: center; gap: 6px;">
            <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #00F0FF; box-shadow: 0 0 10px #00F0FF;"></span>
            Institutional Sports Intelligence
        </div>
    </div>
    """)

    # Concise, elegant dock labels (Zero clumping, zero text wrapping)
    nav_tabs = [
        "⚡ Fixtures", "🔍 Analysis", "📊 Markets", "🤖 AI Predict",
        "🎯 Tipsters", "🛡️ Safe Slip", "📈 Kelly / EV", "⚖️ Odds Vig",
        "🎫 SportyBet", "📜 Backtest", "🔌 API Health"
    ]
    current_module = st.radio("Navigation:", nav_tabs, horizontal=True, label_visibility="collapsed")
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # 1. FIXTURES
    if current_module == "⚡ Fixtures":
        render_html("""
        <div style="padding: 0.8rem 0 0.4rem 0;">
            <div style="display: inline-flex; align-items: center; gap: 8px; padding: 5px 12px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 9999px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #00F0FF; margin-bottom: 0.5rem;">Verified Live Match Center</div>
            <h1 style="font-size: clamp(1.8rem, 3.5vw + 1rem, 2.8rem); font-weight: 800; letter-spacing: -0.04em; margin: 0 0 0.4rem 0; color: #FFFFFF;">Football Fixture Centre.</h1>
            <p style="color: #94A3B8; font-size: 13.5px; margin: 0;">Live canonical match schedules streaming across 26 global domestic leagues.</p>
        </div>
        """)
        schedule = CanonicalFixtureService.get_canonical_schedule()
        c_day, c_status = st.columns([2, 2])
        with c_day:
            day_pick = st.radio("Date Schedule:", ["Today", "Tomorrow"], horizontal=True)
        with c_status:
            status_filter = st.selectbox("Status Filter:", ["All Fixtures", "Confirmed Lineups Only", "Scheduled"])

        fixtures = schedule.get(day_pick, [])
        if status_filter == "Confirmed Lineups Only":
            fixtures = [f for f in fixtures if "Confirmed" in f["lineup_status"]]

        if not fixtures:
            render_html("""
            <div class="glass-card" style="text-align: center; padding: 3rem 1.5rem;">
                <h3 style="color: #94A3B8; margin-bottom: 6px;">No Live Matches Currently Scheduled</h3>
                <p style="color: #64748B; font-size: 13px; margin: 0;">No active fixtures found in the monitored leagues for this date. Check tomorrow or use the AI Predict simulator.</p>
            </div>
            """)
        else:
            for fix in fixtures:
                h, a, comp, ko, venue, l_status = fix["home"], fix["away"], fix["comp"], fix["kickoff"], fix["venue"], fix["lineup_status"]
                is_conf = "Confirmed" in l_status
                res = MarketPricingEngine.evaluate_markets(engine, h, a, is_conf)
                sig_name, sig_cls, sig_desc = res["decision"]

                # Cleanly formatted rounded numbers
                p1 = f"{res['p_1x2']['1']:.1f}%"
                px = f"{res['p_1x2']['X']:.1f}%"
                p2 = f"{res['p_1x2']['2']:.1f}%"
                ev_str = f"{res['ev']:+.1f}% EV"
                best_price = f"{res['odds_1x2']['1']:.2f}"

                render_html(f"""
                <div class="glass-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="color: #94A3B8; font-size: 11px; font-weight: 700; text-transform: uppercase;">🏆 {comp} &nbsp;•&nbsp; ⏰ {ko} &nbsp;•&nbsp; 📍 {venue}</span>
                        <span class="pill-signal {sig_cls}">{sig_name}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap;">
                        <h2 style="margin: 0; font-size: 1.5rem; font-weight: 800; color: #FFF;">{h} <span style="color: #64748B; font-weight: 400;">vs</span> {a}</h2>
                        <span style="font-size: 12px; color: {'#38ef7d' if is_conf else '#FFB800'}; font-weight: 700;">{l_status}</span>
                    </div>
                    <div class="triple-score-grid">
                        <div class="score-cell">
                            <div class="score-title">Score A: Outcome Probability</div>
                            <div class="score-value" style="color: #00F0FF;">{p1} &nbsp;<span style="font-size: 0.9rem; color: #94A3B8;">({h})</span></div>
                            <div class="score-sub">Draw: {px} &nbsp;•&nbsp; Away: {p2}</div>
                        </div>
                        <div class="score-cell">
                            <div class="score-title">Score B: Value vs Best Odds</div>
                            <div class="score-value" style="color: {'#38ef7d' if res['ev'] > 0 else '#FF6961'};">{ev_str}</div>
                            <div class="score-sub">Best Available Price: {best_price}</div>
