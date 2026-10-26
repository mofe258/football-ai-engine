"""
================================================================================
LIQUID GLASS AI SPORTS TERMINAL & MULTI-MARKET PREDICTION SUITE
================================================================================
"""

import os
import sys
import time
import requests
import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from scipy.stats import poisson
from typing import Dict, List, Any

# Import model pipeline bundle
from football_engine import build_or_load_pipeline


# =====================================================================
# 1. UI SYSTEM CONFIGURATION & INJECTED STYLESHEET
# =====================================================================

st.set_page_config(
    page_title="AI Sports Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Fluid Liquid Tokens, Typography, and Glassmorphic Components
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #06070a !important;
        background-image: 
            radial-gradient(circle at 8% 18%, rgba(255, 0, 122, 0.22) 0%, transparent 45%),
            radial-gradient(circle at 92% 28%, rgba(121, 40, 202, 0.28) 0%, transparent 50%),
            radial-gradient(circle at 50% 85%, rgba(255, 77, 77, 0.18) 0%, transparent 55%) !important;
        background-attachment: fixed !important;
        color: #F8FAFC !important;
        letter-spacing: -0.015em;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    .block-container {
        padding-top: clamp(1.5rem, 3vw, 3rem) !important;
        padding-bottom: clamp(2rem, 5vw, 5rem) !important;
        max-width: 1200px !important;
    }

    [data-testid="stSidebar"] {
        background: rgba(10, 12, 18, 0.8) !important;
        backdrop-filter: blur(24px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    .hero-container {
        padding: clamp(1.5rem, 4vw, 3.5rem) 0 clamp(1rem, 2vw, 2rem) 0;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #FF007A;
        margin-bottom: 1rem;
    }
    .hero-title {
        font-size: clamp(2.2rem, 5vw + 1rem, 4.4rem) !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em !important;
        line-height: 1.05 !important;
        margin: 0 0 1rem 0 !important;
        background: linear-gradient(180deg, #FFFFFF 0%, #A5B4FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        font-size: clamp(0.95rem, 1.2vw, 1.15rem);
        color: #8E9BAE;
        max-width: 680px;
        line-height: 1.6;
        margin: 0;
    }

    .liquid-card {
        background: rgba(18, 18, 28, 0.65);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: clamp(1.2rem, 2.5vw, 2rem);
        margin-bottom: 1.5rem;
        box-shadow: 0 12px 36px -12px rgba(0, 0, 0, 0.5), inset 0 1px 0 0 rgba(255, 255, 255, 0.08);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
    }
    .liquid-card:hover {
        transform: translateY(-3px) scale(1.002);
        border-color: rgba(255, 0, 122, 0.35);
        box-shadow: 0 24px 48px -18px rgba(255, 0, 122, 0.15), inset 0 1px 0 0 rgba(255, 255, 255, 0.18);
    }

    .metrics-bar {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 12px;
        margin: 1.25rem 0;
    }
    .metric-cell {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 14px 16px;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .metric-cell:hover {
        background: rgba(255, 255, 255, 0.04);
        border-color: rgba(255, 255, 255, 0.12);
    }
    .cell-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #717E92;
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 6px;
        font-weight: 600;
    }
    .cell-value {
        font-size: 1.15rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.02em;
    }
    .cell-sub {
        font-size: 11px;
        color: #8E9BAE;
        margin-top: 2px;
    }

    .pill-boom {
        background: linear-gradient(135deg, #FF007A 0%, #FF4D4D 100%);
        color: #FFFFFF !important;
        font-weight: 700;
        font-size: 12px;
        padding: 5px 12px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        box-shadow: 0 4px 14px rgba(255, 0, 122, 0.35);
    }
    .pill-safe {
        background: linear-gradient(135deg, #00F0FF 0%, #0066FF 100%);
        color: #06070A !important;
        font-weight: 700;
        font-size: 12px;
        padding: 5px 12px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        box-shadow: 0 4px 14px rgba(0, 240, 255, 0.25);
    }

    div[role="radiogroup"] {
        background: rgba(18, 18, 28, 0.5) !important;
        padding: 5px !important;
        border-radius: 9999px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        display: inline-flex !important;
    }
    div[role="radiogroup"] label {
        padding: 6px 18px !important;
        border-radius: 9999px !important;
        margin-right: 0 !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 8px 16px;
        color: #8E9BAE;
        font-size: 13px;
        font-weight: 500;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .stTabs [aria-selected="true"] {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #FFFFFF !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 14px !important;
        color: #CBD5E1 !important;
        font-size: 13px !important;
    }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# 2. INLINE SVGS ENGINE (1.5px STROKE SPECS)
# =====================================================================

ICONS = {
    "bolt": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>""",
    "fire": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>""",
    "shield": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>""",
    "crosshair": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="22" y1="12" x2="18" y2="12"/><line x1="6" y1="12" x2="2" y2="12"/><line x1="12" y1="6" x2="12" y2="2"/><line x1="12" y1="22" x2="12" y2="18"/></svg>""",
    "clock": """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>""",
    "trophy": """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6m12 5h1.5a2.5 2.5 0 0 0 0-5H18M4 22h16M10 14.66V17c0 .55-.45 1-1 1H8c-.55 0-1 .45-1 1v1h10v-1c0-.55-.45-1-1-1h-1c-.55 0-1-.45-1-1v-2.34c3-.5 5-2.5 5-5.66V4H6v5c0 3.16 2 5.16 5 5.66z"/></svg>""",
    "sparkles": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>"""
}


# =====================================================================
# 3. HIGH-SPEED PREDICTION & SCHEDULE ENGINE
# =====================================================================

@st.cache_resource(show_spinner=False)
def get_prediction_engine():
    return build_or_load_pipeline(force_retrain=False)

@st.cache_data(ttl=1800, show_spinner=False)
def get_cached_prediction(h: str, a: str) -> Dict[str, Any]:
    engine = get_prediction_engine()
    return engine.predict_fixture(h, a)

class RealTimeFixtureResearcher:
    LEAGUES = [
        ("eng.1", "Premier League"),
        ("uefa.champions", "Champions League"),
        ("uefa.europa", "Europa League"),
        ("esp.1", "La Liga"),
        ("ita.1", "Serie A"),
        ("ger.1", "Bundesliga"),
        ("fra.1", "Ligue 1")
    ]

    @staticmethod
    @st.cache_data(ttl=900, show_spinner=False)
    def fetch_fixtures(days_ahead: int = 2) -> Dict[str, List[Dict[str, Any]]]:
        grouped = {"Today": [], "Tomorrow": [], "Upcoming": []}
        headers = {"User-Agent": "Mozilla/5.0"}
        now = datetime.utcnow()
        date_map = {}
        for i in range(days_ahead + 1):
            dt = now + timedelta(days=i)
            key = "Today" if i == 0 else ("Tomorrow" if i == 1 else dt.strftime("%A (%b %d)"))
            date_map[dt.strftime("%Y%m%d")] = key

        for date_str, label in date_map.items():
            for code, name in RealTimeFixtureResearcher.LEAGUES:
                url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={date_str}"
                try:
                    res = requests.get(url, headers=headers, timeout=4)
                    if res.status_code == 200:
                        data = res.json()
                        for ev in data.get("events", []):
                            state = ev.get("status", {}).get("type", {}).get("state", "")
                            if state in ["pre", "in"]:
                                comps = ev.get("competitions", [{}])[0].get("competitors", [])
                                h, a = None, None
                                for c in comps:
                                    tname = c.get("team", {}).get("displayName") or c.get("team", {}).get("name")
                                    if c.get("homeAway") == "home":
                                        h = tname
                                    else:
                                        a = tname

                                raw_date = ev.get("date", "")
                                kickoff = raw_date
                                try:
                                    parsed = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M%z")
                                    kickoff = parsed.strftime("%H:%M UTC")
                                except Exception:
                                    pass

                                if h and a:
                                    target = grouped.get(label, grouped["Upcoming"])
                                    if not any(f["home"] == h and f["away"] == a for f in target):
                                        target.append({"home": h, "away": a, "comp": name, "kickoff": kickoff})
                except Exception:
                    continue
        return grouped


class CompleteMarketCalculator:
    @staticmethod
    def calculate(lambda_h: float, lambda_a: float, ml_probs: Dict[str, float]) -> Dict[str, Any]:
        p_home_ml = ml_probs["Home Win"] / 100.0
        p_draw_ml = ml_probs["Draw"] / 100.0
        p_away_ml = ml_probs["Away Win"] / 100.0

        max_g = 8
        ft_matrix = np.zeros((max_g, max_g))
        for i in range(max_g):
            for j in range(max_g):
                ft_matrix[i, j] = poisson.pmf(i, lambda_h) * poisson.pmf(j, lambda_a)
        ft_matrix /= np.sum(ft_matrix)

        denom = p_home_ml + p_away_ml + 1e-9
        p_dnb_h = p_home_ml / denom
        p_dnb_a = p_away_ml / denom
        p_o15 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if (i + j) > 1.5)
        p_o25 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if (i + j) > 2.5)
        p_u35 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if (i + j) < 3.5)
        p_btts = sum(ft_matrix[i, j] for i in range(1, max_g) for j in range(1, max_g))
        p_mg_13 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if 1 <= (i + j) <= 3)
        p_mg_24 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if 2 <= (i + j) <= 4)

        score_candidates = [((i, j), ft_matrix[i, j]) for i in range(5) for j in range(5)]
        score_candidates.sort(key=lambda x: x[1], reverse=True)
        top_score = f"{score_candidates[0][0][0]}-{score_candidates[0][0][1]}"
        top_score_p = score_candidates[0][1] * 100.0

        lambda_h_ht = lambda_h * 0.44
        lambda_a_ht = lambda_a * 0.44
        p_ht_o05 = 1.0 - (poisson.pmf(0, lambda_h_ht) * poisson.pmf(0, lambda_a_ht))

        return {
            "dnb": {"Home": round(p_dnb_h * 100, 1), "Away": round(p_dnb_a * 100, 1)},
            "totals": {
                "Over 1.5": round(p_o15 * 100, 1),
                "Over 2.5": round(p_o25 * 100, 1),
                "Under 3.5": round(p_u35 * 100, 1)
            },
            "btts": {"GG (Yes)": round(p_btts * 100, 1), "NG (No)": round((1.0 - p_btts) * 100, 1)},
            "multigoal": {"1-3 Goals": round(p_mg_13 * 100, 1), "2-4 Goals": round(p_mg_24 * 100, 1)},
            "top_score": (top_score, round(top_score_p, 1)),
            "ht_o05": round(p_ht_o05 * 100, 1)
        }


# =====================================================================
# 4. VIEW RENDERING (FLUID LIQUID GLASS INTERFACE)
# =====================================================================

def main():
    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-badge">{ICONS['sparkles']} Autonomous Intelligence Core</div>
        <h1 class="hero-title">Predictive Sports Engine.</h1>
        <p class="hero-subtitle">
            Synthesizing shifted rolling features, bivariate Poisson distributions, and real-time contextual news into high-probability betting selections.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_nav, col_btn = st.columns([4, 1])
    with col_nav:
        selected_mode = st.radio(
            "View Mode:",
            ["Active Fixtures", "Simulator Sandbox"],
            label_visibility="collapsed",
            horizontal=True
        )
    with col_btn:
        if st.button("Refresh Feed", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    if selected_mode == "Active Fixtures":
        with st.spinner("Streaming confirmed fixture schedules..."):
            grouped_matches = RealTimeFixtureResearcher.fetch_fixtures(days_ahead=2)

        total_games = sum(len(v) for v in grouped_matches.values())
        if total_games == 0:
            st.markdown("""
            <div class="liquid-card" style="text-align: center; padding: 4rem 2rem;">
                <h3 style="color: #8E9BAE; margin-bottom: 8px;">No Fixtures Scheduled</h3>
                <p style="color: #505B6E; margin: 0;">Monitored leagues are currently inactive today. Switch to the Simulator to analyze any club.</p>
            </div>
            """, unsafe_allow_html=True)
            return

        available_days = [k for k, v in grouped_matches.items() if len(v) > 0]
        selected_day = st.radio("Matchday:", available_days, horizontal=True)

        fixtures_to_show = grouped_matches[selected_day]

        for match in fixtures_to_show:
            h, a, comp, kickoff = match["home"], match["away"], match["comp"], match["kickoff"]

            rep = get_cached_prediction(h, a)
            calc = CompleteMarketCalculator.calculate(rep["xg"]["home_xg"], rep["xg"]["away_xg"], rep["1x2"])

            p_1x = rep["double_chance"]["1X (Home or Draw)"]
            p_x2 = rep["double_chance"]["X2 (Draw or Away)"]
            safe_pick = "1X Double Chance" if p_1x >= p_x2 else "X2 Double Chance"
            safe_prob = max(p_1x, p_x2)

            boom_pick = "Over 2.5 Goals" if calc["totals"]["Over 2.5"] >= 58 else (
                "Both Teams to Score (GG)" if calc["btts"]["GG (Yes)"] >= 58 else f"{h} Outright Win"
            )
            boom_prob = calc["totals"]["Over 2.5"] if "Over" in boom_pick else (
                calc["btts"]["GG (Yes)"] if "Both" in boom_pick else rep["1x2"]["Home Win"]
            )

            st.markdown(f"""
            <div class="liquid-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; gap: 8px; color: #8E9BAE; font-size: 12px; font-weight: 600; text-transform: uppercase;">
                        {ICONS['trophy']} {comp}
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px; color: #505B6E; font-size: 12px; font-weight: 500;">
                        {ICONS['clock']} {kickoff}
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 12px;">
                    <h2 style="font-size: clamp(1.4rem, 2.5vw, 2.1rem); font-weight: 800; letter-spacing: -0.03em; margin: 0; color: #FFFFFF;">
                        {h} <span style="background: linear-gradient(135deg, #FF007A 0%, #FF4D4D 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 300;">vs</span> {a}
                    </h2>
                    <div style="display: flex; gap: 8px;">
                        <span class="pill-safe">{ICONS['shield']} {safe_pick}</span>
                        <span class="pill-boom">{ICONS['fire']} {boom_pick}</span>
                    </div>
                </div>

                <div class="metrics-bar">
                    <div class="metric-cell">
                        <div class="cell-label">{ICONS['shield']} Banker Floor</div>
                        <div class="cell-value" style="color: #00F0FF;">{safe_prob:.1f}%</div>
                        <div class="cell-sub">{safe_pick}</div>
                    </div>
                    <div class="metric-cell">
                        <div class="cell-label">{ICONS['fire']} Boom Opportunity</div>
                        <div class="cell-value" style="color: #FF007A;">{boom_prob:.1f}%</div>
                        <div class="cell-sub">{boom_pick}</div>
                    </div>
                    <div class="metric-cell">
                        <div class="cell-label">{ICONS['crosshair']} Sniper Score</div>
                        <div class="cell-value">{calc['top_score'][0]}</div>
                        <div class="cell-sub">{calc['top_score'][1]}% probability</div>
                    </div>
                    <div class="metric-cell">
                        <div class="cell-label">{ICONS['bolt']} Model Confidence</div>
                        <div class="cell-value">{rep['confidence']}<span style="font-size: 0.8rem; color: #717E92;">/10</span></div>
                        <div class="cell-sub">Entropy calibrated</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"Inspect Complete Market Catalog for {h} vs {a}"):
                t1, t2, t3, t4 = st.tabs(["Match Winner & DNB", "Goals & Totals", "Half-Time", "Multi-Goal & Acca"])

                with t1:
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**1X2 Moneyline**<br>1: `{rep['1x2']['Home Win']}%`<br>X: `{rep['1x2']['Draw']}%`<br>2: `{rep['1x2']['Away Win']}%`", unsafe_allow_html=True)
                    c2.markdown(f"**Draw No Bet (DNB)**<br>{h}: `{calc['dnb']['Home']}%`<br>{a}: `{calc['dnb']['Away']}%`", unsafe_allow_html=True)
                    c3.markdown(f"**Double Chance**<br>1X: `{rep['double_chance']['1X (Home or Draw)']}%`<br>X2: `{rep['double_chance']['X2 (Draw or Away)']}%`", unsafe_allow_html=True)

                with t2:
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Goal Thresholds**<br>Over 1.5: `{calc['totals']['Over 1.5']}%`<br>Over 2.5: `{calc['totals']['Over 2.5']}%`<br>Under 3.5: `{calc['totals']['Under 3.5']}%`", unsafe_allow_html=True)
                    c2.markdown(f"**BTTS (GG/NG)**<br>GG (Yes): `{calc['btts']['GG (Yes)']}%`<br>NG (No): `{calc['btts']['NG (No)']}%`", unsafe_allow_html=True)
                    c3.markdown(f"**Expected Goals (xG)**<br>{h}: `{rep['xg']['home_xg']}` xG<br>{a}: `{rep['xg']['away_xg']}` xG", unsafe_allow_html=True)

                with t3:
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**First Half Over 0.5**<br>Probability: `{calc['ht_o05']}%`", unsafe_allow_html=True)
                    c2.markdown(f"**Top Model Scorelines**<br>Rank 1: `{calc['top_score'][0]}` ({calc['top_score'][1]}%)", unsafe_allow_html=True)

                with t4:
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**Multi-Goal Ranges**<br>1-3 Goals: `{calc['multigoal']['1-3 Goals']}%`<br>2-4 Goals: `{calc['multigoal']['2-4 Goals']}%`", unsafe_allow_html=True)
                    c2.markdown(f"**High-Probability Acca Leg**<br>1X & Over 1.5: `{round(safe_prob * calc['totals']['Over 1.5'] / 100, 1)}%`", unsafe_allow_html=True)

            st.write("")

    elif selected_mode == "Simulator Sandbox":
        st.markdown("""
        <div class="liquid-card">
            <h3 style="margin-top:0; color: #FFFFFF;">On-Demand Club Simulator</h3>
            <p style="color: #8E9BAE; font-size: 13px;">Execute XGBoost time-series matrices on any matchup worldwide.</p>
        </div>
        """, unsafe_allow_html=True)

        sc1, sc2 = st.columns(2)
        with sc1:
            home_sim = st.text_input("Home Club", value="Arsenal")
        with sc2:
            away_sim = st.text_input("Away Club", value="Chelsea")

        if st.button("Generate Match Simulation", type="primary", use_container_width=True):
            with st.spinner("Processing Poisson distribution tensors..."):
                rep = get_cached_prediction(home_sim, away_sim)
                calc = CompleteMarketCalculator.calculate(rep["xg"]["home_xg"], rep["xg"]["away_xg"], rep["1x2"])

            st.markdown(f"""
            <div class="liquid-card" style="margin-top: 1.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <span class="pill-boom">{ICONS['bolt']} Simulation Output</span>
                    <span style="font-size: 12px; color: #8E9BAE;">Confidence: {rep['confidence']}/10</span>
                </div>
                <h2 style="margin: 0 0 1rem 0; color: #FFFFFF;">{home_sim} vs {away_sim}</h2>
                <div class="metrics-bar">
                    <div class="metric-cell">
                        <div class="cell-label">Primary Selection</div>
                        <div class="cell-value" style="color: #00F0FF;">{rep['1x2']['Selection']}</div>
                    </div>
                    <div class="metric-cell">
                        <div class="cell-label">Over 2.5 Goals</div>
                        <div class="cell-value">{calc['totals']['Over 2.5']}%</div>
                    </div>
                    <div class="metric-cell">
                        <div class="cell-label">Both Teams to Score</div>
                        <div class="cell-value">{calc['btts']['GG (Yes)']}%</div>
                    </div>
                    <div class="metric-cell">
                        <div class="cell-label">Exact Score</div>
                        <div class="cell-value" style="color: #FF007A;">{calc['top_score'][0]}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
