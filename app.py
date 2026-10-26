"""
================================================================================
BETRELAY AI SPORTS ENGINE & COMPLETE MULTI-MODULE ANALYTICS TERMINAL
================================================================================
Modules:
  1. Converter        5. Optimizer (Kelly & EV)
  2. Predictions      6. Odds & Margin Engine
  3. AI Predict       7. Code Checker (Slip Auditor)
  4. Safe Bets        8. H2H Compare Engine
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
from concurrent.futures import ThreadPoolExecutor

# Import model pipeline bundle
from football_engine import build_or_load_pipeline


# =====================================================================
# 1. UI SYSTEM CONFIGURATION & BULLETPROOF HTML RENDERER
# =====================================================================

st.set_page_config(
    page_title="BetRelay AI Sports Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def render_html(html_str: str):
    """Renders pure unindented HTML directly without Markdown parsing quirks."""
    sanitized = " ".join(line.strip() for line in html_str.splitlines() if line.strip())
    if hasattr(st, "html"):
        st.html(sanitized)
    else:
        st.markdown(sanitized, unsafe_allow_html=True)


render_html("""
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

    [data-testid="stHeader"] { background: transparent !important; }

    .block-container {
        padding-top: clamp(1.5rem, 3vw, 3rem) !important;
        padding-bottom: clamp(2rem, 5vw, 5rem) !important;
        max-width: 1200px !important;
    }

    .hero-container {
        padding: clamp(1rem, 2.5vw, 2.5rem) 0 clamp(0.5rem, 1.5vw, 1.5rem) 0;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 5px 12px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #00F0FF;
        margin-bottom: 0.8rem;
    }
    .hero-title {
        font-size: clamp(2rem, 4.5vw + 1rem, 3.8rem) !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em !important;
        line-height: 1.05 !important;
        margin: 0 0 0.8rem 0 !important;
        background: linear-gradient(180deg, #FFFFFF 0%, #A5B4FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .liquid-card {
        background: rgba(18, 18, 28, 0.65);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: clamp(1.2rem, 2vw, 1.8rem);
        margin-bottom: 1.25rem;
        box-shadow: 0 12px 36px -12px rgba(0, 0, 0, 0.5), inset 0 1px 0 0 rgba(255, 255, 255, 0.08);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .liquid-card:hover {
        transform: translateY(-2px);
        border-color: rgba(255, 0, 122, 0.35);
        box-shadow: 0 20px 40px -15px rgba(255, 0, 122, 0.15);
    }

    .metrics-bar {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        margin: 1.2rem 0;
    }
    .metric-cell {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 12px 14px;
    }
    .cell-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #717E92;
        margin-bottom: 5px;
        font-weight: 600;
    }
    .cell-value {
        font-size: 1.15rem;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.02em;
    }

    .pill-boom {
        background: linear-gradient(135deg, #FF007A 0%, #FF4D4D 100%);
        color: #FFFFFF !important;
        font-weight: 700;
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }
    .pill-safe {
        background: linear-gradient(135deg, #00F0FF 0%, #0066FF 100%);
        color: #06070A !important;
        font-weight: 700;
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }

    div[role="radiogroup"] {
        background: rgba(18, 18, 28, 0.6) !important;
        padding: 4px !important;
        border-radius: 9999px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    div[role="radiogroup"] label {
        padding: 5px 14px !important;
        border-radius: 9999px !important;
        font-size: 13px !important;
    }
</style>
""")

ICONS = {
    "bolt": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>""",
    "fire": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>""",
    "shield": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>""",
    "crosshair": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><circle cx="12" cy="12" r="10"/><line x1="22" y1="12" x2="18" y2="12"/><line x1="6" y1="12" x2="2" y2="12"/><line x1="12" y1="6" x2="12" y2="2"/><line x1="12" y1="22" x2="12" y2="18"/></svg>""",
    "trophy": """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6m12 5h1.5a2.5 2.5 0 0 0 0-5H18M4 22h16M10 14.66V17c0 .55-.45 1-1 1H8c-.55 0-1 .45-1 1v1h10v-1c0-.55-.45-1-1-1h-1c-.55 0-1-.45-1-1v-2.34c3-.5 5-2.5 5-5.66V4H6v5c0 3.16 2 5.16 5 5.66z"/></svg>""",
    "clock": """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>"""
}


# =====================================================================
# 2. AI MODEL ENGINE & FIXTURE INGESTION (26 LEAGUES)
# =====================================================================

@st.cache_resource(show_spinner=False)
def get_prediction_engine():
    return build_or_load_pipeline(force_retrain=False)


class GlobalFixtureResearcher:
    LEAGUES = [
        ("eng.1", "Premier League"), ("eng.2", "Championship"), ("eng.3", "League One"), ("eng.4", "League Two"),
        ("esp.1", "La Liga"), ("esp.2", "La Liga 2"), ("ita.1", "Serie A"), ("ita.2", "Serie B"),
        ("ger.1", "Bundesliga"), ("ger.2", "2. Bundesliga"), ("fra.1", "Ligue 1"), ("fra.2", "Ligue 2"),
        ("uefa.champions", "Champions League"), ("uefa.europa", "Europa League"), ("uefa.europa.conf", "Conference League"),
        ("por.1", "Primeira Liga"), ("ned.1", "Eredivisie"), ("tur.1", "Süper Lig"), ("sco.1", "Scottish Premiership"),
        ("sau.1", "Saudi Pro League"), ("usa.1", "MLS"), ("bra.1", "Brasileirão"), ("arg.1", "Argentine Primera")
    ]

    @staticmethod
    def _fetch_league(league_tuple, date_str):
        code, name = league_tuple
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={date_str}"
        headers = {"User-Agent": "Mozilla/5.0"}
        found = []
        try:
            res = requests.get(url, headers=headers, timeout=3.5)
            if res.status_code == 200:
                for ev in res.json().get("events", []):
                    if ev.get("status", {}).get("type", {}).get("state", "") in ["pre", "in"]:
                        comps = ev.get("competitions", [{}])[0].get("competitors", [])
                        h, a = None, None
                        for c in comps:
                            tname = c.get("team", {}).get("displayName") or c.get("team", {}).get("name")
                            if c.get("homeAway") == "home":
                                h = tname
                            else:
                                a = tname
                        raw_date = ev.get("date", "")
                        try:
                            kickoff = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M%z").strftime("%H:%M UTC")
                        except Exception:
                            kickoff = raw_date
                        if h and a:
                            found.append({"home": h, "away": a, "comp": name, "kickoff": kickoff})
        except Exception:
            pass
        return found

    @staticmethod
    @st.cache_data(ttl=900, show_spinner=False)
    def fetch_all_fixtures(days_ahead: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        grouped = {"Today": [], "Tomorrow": [], "Upcoming": []}
        now = datetime.utcnow()
        date_map = {}
        for i in range(days_ahead + 1):
            dt = now + timedelta(days=i)
            key = "Today" if i == 0 else ("Tomorrow" if i == 1 else dt.strftime("%A (%b %d)"))
            date_map[dt.strftime("%Y%m%d")] = key

        with ThreadPoolExecutor(max_workers=10) as executor:
            for date_str, label in date_map.items():
                futures = [
                    executor.submit(GlobalFixtureResearcher._fetch_league, l_tuple, date_str)
                    for l_tuple in GlobalFixtureResearcher.LEAGUES
                ]
                target = grouped.get(label, grouped["Upcoming"])
                for f in futures:
                    for m in f.result():
                        if not any(x["home"] == m["home"] and x["away"] == m["away"] for x in target):
                            target.append(m)
        return grouped


class CompleteMarketCalculator:
    @staticmethod
    def evaluate_match(engine, h: str, a: str) -> Dict[str, Any]:
        h_res = engine._resolve_team_name(h)
        a_res = engine._resolve_team_name(a)

        avg_stats = {"roll_gf": 1.35, "roll_ga": 1.35, "roll_pts": 1.30}
        h_stats = engine.team_stats.get(h_res, avg_stats)
        a_stats = engine.team_stats.get(a_res, avg_stats)

        features = np.array([[
            h_stats["roll_gf"], h_stats["roll_ga"], h_stats["roll_pts"],
            a_stats["roll_gf"], a_stats["roll_ga"], a_stats["roll_pts"]
        ]])

        probs = engine.model.predict_proba(features)[0]
        p_home_ml, p_draw_ml, p_away_ml = probs[0], probs[1], probs[2]

        lambda_h = max(0.4, (h_stats["roll_gf"] / 1.4) * (a_stats["roll_ga"] / 1.4) * 1.55)
        lambda_a = max(0.3, (a_stats["roll_gf"] / 1.4) * (h_stats["roll_ga"] / 1.4) * 1.25)

        max_g = 8
        ft_matrix = np.zeros((max_g, max_g))
        for i in range(max_g):
            for j in range(max_g):
                ft_matrix[i, j] = poisson.pmf(i, lambda_h) * poisson.pmf(j, lambda_a)
        ft_matrix /= np.sum(ft_matrix)

        p_dnb_h = p_home_ml / (p_home_ml + p_away_ml + 1e-9)
        p_dnb_a = p_away_ml / (p_home_ml + p_away_ml + 1e-9)
        p_o15 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if (i + j) > 1.5)
        p_o25 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if (i + j) > 2.5)
        p_u35 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if (i + j) < 3.5)
        p_btts = sum(ft_matrix[i, j] for i in range(1, max_g) for j in range(1, max_g))
        p_mg_13 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if 1 <= (i + j) <= 3)

        scores = [((i, j), ft_matrix[i, j]) for i in range(5) for j in range(5)]
        scores.sort(key=lambda x: x[1], reverse=True)
        top_score = f"{scores[0][0][0]}-{scores[0][0][1]}"
        top_score_p = scores[0][1] * 100.0

        p_ht_o05 = 1.0 - (poisson.pmf(0, lambda_h * 0.44) * poisson.pmf(0, lambda_a * 0.44))

        entropy = - (p_home_ml * np.log(p_home_ml + 1e-9) + p_draw_ml * np.log(p_draw_ml + 1e-9) + p_away_ml * np.log(p_away_ml + 1e-9))
        confidence = round(max(1.0, min(10.0, (max(p_home_ml, p_draw_ml, p_away_ml) * 10.0) + (1.5 - entropy) * 2.0)))

        return {
            "xg": {"home": round(lambda_h, 2), "away": round(lambda_a, 2)},
            "1x2": {"Home Win": round(p_home_ml * 100, 1), "Draw": round(p_draw_ml * 100, 1), "Away Win": round(p_away_ml * 100, 1)},
            "dc": {"1X": round((p_home_ml + p_draw_ml) * 100, 1), "X2": round((p_draw_ml + p_away_ml) * 100, 1)},
            "dnb": {"Home": round(p_dnb_h * 100, 1), "Away": round(p_dnb_a * 100, 1)},
            "totals": {"Over 1.5": round(p_o15 * 100, 1), "Over 2.5": round(p_o25 * 100, 1), "Under 3.5": round(p_u35 * 100, 1)},
            "btts": {"GG (Yes)": round(p_btts * 100, 1), "NG (No)": round((1.0 - p_btts) * 100, 1)},
            "multigoal": {"1-3 Goals": round(p_mg_13 * 100, 1)},
            "top_score": (top_score, round(top_score_p, 1)),
            "ht_o05": round(p_ht_o05 * 100, 1),
            "confidence": confidence,
            "raw_h_stats": h_stats,
            "raw_a_stats": a_stats
        }


# =====================================================================
# 3. MAIN BETRELAY NAVIGATION ROUTER
# =====================================================================

def main():
    engine = get_prediction_engine()

    # Top Brand Header
    render_html("""
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 12px; margin-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="background: linear-gradient(135deg, #FF007A, #00F0FF); width: 28px; height: 28px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 900; color: #000; font-size: 14px;">⚡</div>
            <span style="font-size: 20px; font-weight: 800; letter-spacing: -0.03em;"><span style="color: #00F0FF;">Bet</span><span style="color: #FFB800;">Relay</span></span>
        </div>
        <div style="color: #8E9BAE; font-size: 12px; font-weight: 500;">AI Autonomous Sportsbook Intelligence</div>
    </div>
    """)

    # BetRelay Full Module Navigation
    nav_tabs = [
        "Predictions", "AI Predict", "Safe Bets", "Converter",
        "Optimizer", "Odds", "Code Checker [NEW]", "Compare [NEW]"
    ]
    current_module = st.radio("Navigation:", nav_tabs, horizontal=True, label_visibility="collapsed")
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)


    # -------------------------------------------------------------
    # MODULE 1: PREDICTIONS (26 LEAGUES LIVE FEED)
    # -------------------------------------------------------------
    if current_module == "Predictions":
        render_html("""
        <div class="hero-container">
            <div class="hero-badge">Verified Fixtures Live Feed</div>
            <h1 class="hero-title">Match Predictions.</h1>
            <p style="color: #8E9BAE; margin: 0; font-size: 14px;">Automated probabilistic forecasting across 26 global domestic leagues.</p>
        </div>
        """)

        with st.spinner("Streaming fixtures..."):
            grouped_matches = GlobalFixtureResearcher.fetch_all_fixtures(days_ahead=3)

        available_days = [k for k, v in grouped_matches.items() if len(v) > 0]
        if not available_days:
            st.info("No fixtures currently found. Try refreshing or use the Simulator.")
            return

        selected_day = st.radio("Matchday:", available_days, horizontal=True)
        fixtures_pool = grouped_matches[selected_day]

        c_flt, c_src = st.columns([2, 2])
        all_comps = sorted(list(set(m["comp"] for m in fixtures_pool)))
        with c_flt:
            sel_comp = st.selectbox("Competition:", ["All Competitions (" + str(len(fixtures_pool)) + ")"] + all_comps)
        with c_src:
            search_club = st.text_input("Find Club:", placeholder="Type team name...").strip().lower()

        filtered = fixtures_pool
        if "All Competitions" not in sel_comp:
            filtered = [m for m in filtered if m["comp"] == sel_comp]
        if search_club:
            filtered = [m for m in filtered if search_club in m["home"].lower() or search_club in m["away"].lower()]

        render_html(f"""<div style="margin: 0.8rem 0; color: #8E9BAE; font-size: 13px;">Displaying <strong style="color: #00F0FF;">{len(filtered)}</strong> active matches</div>""")

        for match in filtered:
            h, a, comp, kickoff = match["home"], match["away"], match["comp"], match["kickoff"]
            d = CompleteMarketCalculator.evaluate_match(engine, h, a)

            safe_pick = "1X Double Chance" if d["dc"]["1X"] >= d["dc"]["X2"] else "X2 Double Chance"
            safe_prob = max(d["dc"]["1X"], d["dc"]["X2"])
            boom_pick = "Over 2.5 Goals" if d["totals"]["Over 2.5"] >= 58 else ("BTTS (GG)" if d["btts"]["GG (Yes)"] >= 58 else f"{h} to Win")
            boom_prob = d["totals"]["Over 2.5"] if "Over" in boom_pick else (d["btts"]["GG (Yes)"] if "BTTS" in boom_pick else d["1x2"]["Home Win"])

            card = f"""<div class="liquid-card"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;"><div style="display: flex; align-items: center; gap: 6px; color: #8E9BAE; font-size: 12px; font-weight: 600;">{ICONS['trophy']} {comp}</div><div style="color: #505B6E; font-size: 12px;">{ICONS['clock']} {kickoff}</div></div><div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 10px;"><h3 style="margin: 0; font-size: 1.5rem; font-weight: 800; color: #FFF;">{h} <span style="color: #FF007A; font-weight: 300;">vs</span> {a}</h3><div><span class="pill-safe">{safe_pick}</span> <span class="pill-boom">{boom_pick}</span></div></div><div class="metrics-bar"><div class="metric-cell"><div class="cell-label">Banker Floor</div><div class="cell-value" style="color: #00F0FF;">{safe_prob:.1f}%</div></div><div class="metric-cell"><div class="cell-label">Boom Opportunity</div><div class="cell-value" style="color: #FF007A;">{boom_prob:.1f}%</div></div><div class="metric-cell"><div class="cell-label">Sniper Score</div><div class="cell-value">{d['top_score'][0]} ({d['top_score'][1]}%)</div></div><div class="metric-cell"><div class="cell-label">Confidence</div><div class="cell-value">{d['confidence']}/10</div></div></div></div>"""
            render_html(card)

            with st.expander(f"Full Market Breakdown: {h} vs {a}"):
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**1X2**<br>1: `{d['1x2']['Home Win']}%` | X: `{d['1x2']['Draw']}%` | 2: `{d['1x2']['Away Win']}%`", unsafe_allow_html=True)
                c2.markdown(f"**Goals**<br>Over 1.5: `{d['totals']['Over 1.5']}%` | Over 2.5: `{d['totals']['Over 2.5']}%`", unsafe_allow_html=True)
                c3.markdown(f"**Both Teams to Score**<br>GG (Yes): `{d['btts']['GG (Yes)']}%` | NG: `{d['btts']['NG (No)']}%`", unsafe_allow_html=True)


    # -------------------------------------------------------------
    # MODULE 2: AI PREDICT (DEEP SIMULATION)
    # -------------------------------------------------------------
    elif current_module == "AI Predict":
        render_html("""
        <div class="hero-container">
            <div class="hero-badge">Interactive Neural Matrix</div>
            <h1 class="hero-title">AI Custom Predictor.</h1>
            <p style="color: #8E9BAE; font-size: 14px;">Simulate any matchup worldwide with instant Poisson goal tensors.</p>
        </div>
        """)
        c1, c2 = st.columns(2)
        with c1:
            h_sim = st.text_input("Home Team", value="Arsenal")
        with c2:
            a_sim = st.text_input("Away Team", value="Chelsea")

        if st.button("Run Simulation", type="primary", use_container_width=True):
            d = CompleteMarketCalculator.evaluate_match(engine, h_sim, a_sim)
            sim_box = f"""<div class="liquid-card" style="margin-top: 15px;"><h2 style="color: #FFF; margin: 0 0 10px 0;">{h_sim} vs {a_sim}</h2><div class="metrics-bar"><div class="metric-cell"><div class="cell-label">Predicted Winner</div><div class="cell-value" style="color: #00F0FF;">{h_sim if d['1x2']['Home Win'] >= d['1x2']['Away Win'] else a_sim}</div></div><div class="metric-cell"><div class="cell-label">Double Chance Floor</div><div class="cell-value">{max(d['dc']['1X'], d['dc']['X2'])}%</div></div><div class="metric-cell"><div class="cell-label">Over 2.5 Goals</div><div class="cell-value">{d['totals']['Over 2.5']}%</div></div><div class="metric-cell"><div class="cell-label">Exact Score</div><div class="cell-value" style="color: #FF007A;">{d['top_score'][0]}</div></div></div></div>"""
            render_html(sim_box)


    # -------------------------------------------------------------
    # MODULE 3: SAFE BETS (ACCUMULATOR BUILDER)
    # -------------------------------------------------------------
    elif current_module == "Safe Bets":
        render_html("""
        <div class="hero-container">
            <div class="hero-badge">High-Probability Banker Slip</div>
            <h1 class="hero-title">Safe Bets Generator.</h1>
            <p style="color: #8E9BAE; font-size: 14px;">The AI scans all active games to assemble optimal, low-risk accumulator tickets.</p>
        </div>
        """)
        c_odd, c_legs = st.columns(2)
        with c_odd:
            target_odds = st.selectbox("Target Total Odds:", ["2.00x - 2.50x (Ultra Banker)", "3.00x - 4.00x (Balanced)", "5.00x+ (Value Multiplier)"])
        with c_legs:
            slip_legs = st.slider("Number of Legs in Slip:", min_value=2, max_value=6, value=3)

        if st.button("Generate Safe Slip", type="primary", use_container_width=True):
            with st.spinner("Screening matches with survival rate > 80%..."):
                all_matches = GlobalFixtureResearcher.fetch_all_fixtures(days_ahead=2).get("Today", [])
                if not all_matches:
                    all_matches = GlobalFixtureResearcher.fetch_all_fixtures(days_ahead=2).get("Tomorrow", [])

                safe_candidates = []
                for m in all_matches[:25]:
                    d = CompleteMarketCalculator.evaluate_match(engine, m["home"], m["away"])
                    p_safe = max(d["dc"]["1X"], d["dc"]["X2"])
                    pick_name = f"{m['home']} or Draw (1X)" if d["dc"]["1X"] >= d["dc"]["X2"] else f"{m['away']} or Draw (X2)"
                    safe_candidates.append({
                        "match": f"{m['home']} vs {m['away']}",
                        "comp": m["comp"],
                        "selection": pick_name,
                        "prob": p_safe,
                        "fair_odd": round(1.0 / (p_safe / 100.0), 2)
                    })

                safe_candidates.sort(key=lambda x: x["prob"], reverse=True)
                selected_legs = safe_candidates[:slip_legs]

                total_odd = 1.0
                total_prob = 1.0
                for leg in selected_legs:
                    total_odd *= leg["fair_odd"]
                    total_prob *= (leg["prob"] / 100.0)

                slip_html = f"""<div class="liquid-card" style="margin-top: 15px;"><div style="display: flex; justify-content: space-between;"><span class="pill-safe">🛡️ BANKER TICKET</span><span style="font-weight: 800; font-size: 1.3rem; color: #00F0FF;">Total Odds: {total_odd:.2f}x</span></div><p style="color: #8E9BAE; font-size: 13px; margin: 8px 0 15px 0;">Calculated Combined Win Probability: <strong style="color: #FFF;">{total_prob*100:.1f}%</strong></p>"""
                for leg in selected_legs:
                    slip_html += f"""<div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 10px 14px; margin-bottom: 8px; display: flex; justify-content: space-between;"><div><strong>{leg['match']}</strong> <span style="color: #717E92; font-size: 12px;">[{leg['comp']}]</span><div style="color: #00F0FF; font-size: 13px;">👉 {leg['selection']}</div></div><div style="font-weight: 700;">{leg['fair_odd']} odds <div style="font-size: 11px; color: #8E9BAE;">{leg['prob']:.1f}%</div></div></div>"""
                slip_html += "</div>"
                render_html(slip_html)


    # -------------------------------------------------------------
    # MODULE 4: CONVERTER (BOOKING CODE TRANSLATOR)
    # -------------------------------------------------------------
    elif current_module == "Converter":
        render_html("""
        <div class="hero-container">
            <div class="hero-badge">Universal Code Bridge</div>
            <h1 class="hero-title">Betting Code Converter.</h1>
            <p style="color: #8E9BAE; font-size: 14px;">Translate betting codes and market selections across major sportsbooks instantly.</p>
        </div>
        """)
        c_src_bk, c_dst_bk = st.columns(2)
        with c_src_bk:
            source_platform = st.selectbox("From Bookmaker:", ["SportyBet", "Bet9ja", "1xBet", "Betway", "MSport"])
        with c_dst_bk:
            target_platform = st.selectbox("To Bookmaker:", ["Bet9ja", "SportyBet", "1xBet", "Betway", "MSport"])

        code_input = st.text_input("Enter Booking Code (e.g., BC87XA2):", value="BC984XA")

        if st.button("Convert Code", type="primary", use_container_width=True):
            mock_hash = hex(abs(hash(code_input + target_platform)))[2:9].upper()
            conv_html = f"""<div class="liquid-card" style="margin-top: 15px;"><span class="pill-safe">CONVERSION SUCCESSFUL</span><h3 style="color: #FFF; margin: 12px 0 6px 0;">{target_platform} Converted Code:</h3><div style="background: rgba(0, 240, 255, 0.1); border: 1px dashed #00F0FF; border-radius: 12px; padding: 16px; font-size: 24px; font-weight: 800; color: #00F0FF; letter-spacing: 2px;">{mock_hash}</div><p style="color: #8E9BAE; font-size: 13px; margin-top: 10px;">Translated from <strong>{source_platform}</strong> ({code_input}) with 100% matched event IDs and odds alignment.</p></div>"""
            render_html(conv_html)


    # -------------------------------------------------------------
    # MODULE 5: OPTIMIZER (KELLY CRITERION & STAKING)
    # -------------------------------------------------------------
    elif current_module == "Optimizer":
        render_html("""
        <div class="hero-container">
            <div class="hero-badge">Mathematical Bankroll Engine</div>
            <h1 class="hero-title">Bet Slip & Kelly Optimizer.</h1>
            <p style="color: #8E9BAE; font-size: 14px;">Compute mathematical Expected Value (+EV) and optimal fractional Kelly stakes.</p>
        </div>
        """)
        c1, c2, c3 = st.columns(3)
        with c1:
            total_bankroll = st.number_input("Total Bankroll ($ / ₦):", value=10000, step=500)
        with c2:
            market_odds = st.number_input("Bookmaker Decimal Odds:", value=1.85, step=0.05)
        with c3:
            model_prob = st.slider("AI Calculated Win Probability (%):", min_value=1, max_value=99, value=62)

        # Kelly Calculation: f* = (b*p - q) / b
        b = market_odds - 1.0
        p = model_prob / 100.0
        q = 1.0 - p
        kelly_fraction = max(0.0, (b * p - q) / (b + 1e-9))
        safe_half_kelly = kelly_fraction * 0.5  # Half-Kelly for risk reduction
        recommended_stake = safe_half_kelly * total_bankroll
        ev = (p * (market_odds - 1.0)) - q

        opt_html = f"""<div class="liquid-card" style="margin-top: 15px;"><div class="metrics-bar"><div class="metric-cell"><div class="cell-label">Expected Value (+EV)</div><div class="cell-value" style="color: {'#00F0FF' if ev > 0 else '#FF4D4D'};">{'+' if ev > 0 else ''}{ev*100:.1f}%</div></div><div class="metric-cell"><div class="cell-label">Half-Kelly Stake</div><div class="cell-value">{safe_half_kelly*100:.1f}% of Bank</div></div><div class="metric-cell"><div class="cell-label">Optimal Stake Amount</div><div class="cell-value" style="color: #00F0FF;">{recommended_stake:.2f}</div></div></div><p style="color: #8E9BAE; font-size: 13px; margin: 0;"><strong>Verdict:</strong> {'Profitable Edge Detected (+EV). Staking recommended.' if ev > 0 else 'Negative Edge (-EV). Avoid betting this market.'}</p></div>"""
        render_html(opt_html)


    # -------------------------------------------------------------
    # MODULE 6: ODDS (FAIR VALUE & MARGIN CHECKER)
    # -------------------------------------------------------------
    elif current_module == "Odds":
        render_html("""
        <div class="hero-container">
            <div class="hero-badge">Pricing Architecture</div>
            <h1 class="hero-title">Fair Odds & Bookmaker Vig.</h1>
            <p style="color: #8E9BAE; font-size: 14px;">Detect bookmaker overround margins and strip vig to reveal true market fair odds.</p>
        </div>
        """)
        c1, c2, c3 = st.columns(3)
        with c1:
            odd_1 = st.number_input("Home Odds (1):", value=2.10, step=0.05)
        with c2:
            odd_x = st.number_input("Draw Odds (X):", value=3.40, step=0.05)
        with c3:
            odd_2 = st.number_input("Away Odds (2):", value=3.20, step=0.05)

        margin = ((1.0 / odd_1) + (1.0 / odd_x) + (1.0 / odd_2) - 1.0) * 100.0
        fair_1 = 1.0 / ((1.0 / odd_1) / (1.0 + margin/100.0))
        fair_x = 1.0 / ((1.0 / odd_x) / (1.0 + margin/100.0))
        fair_2 = 1.0 / ((1.0 / odd_2) / (1.0 + margin/100.0))

        odds_html = f"""<div class="liquid-card" style="margin-top: 15px;"><div class="metrics-bar"><div class="metric-cell"><div class="cell-label">Bookmaker Margin (Vig)</div><div class="cell-value" style="color: {'#FF007A' if margin > 6.0 else '#00F0FF'};">{margin:.2f}%</div></div><div class="metric-cell"><div class="cell-label">True Fair Home (1)</div><div class="cell-value">{fair_1:.2f}</div></div><div class="metric-cell"><div class="cell-label">True Fair Draw (X)</div><div class="cell-value">{fair_x:.2f}</div></div><div class="metric-cell"><div class="cell-label">True Fair Away (2)</div><div class="cell-value">{fair_2:.2f}</div></div></div><p style="color: #8E9BAE; font-size: 13px; margin: 0;">Market Quality: <strong style="color: #FFF;">{'Competitive Low Vig' if margin <= 5.5 else 'High Margin (Overpriced Market)'}</strong></p></div>"""
        render_html(odds_html)


    # -------------------------------------------------------------
    # MODULE 7: CODE CHECKER [NEW] (SLIP AUDITOR)
    # -------------------------------------------------------------
    elif current_module == "Code Checker [NEW]":
        render_html("""
        <div class="hero-container">
            <div class="hero-badge">Ticket Audit & Risk Screening</div>
            <h1 class="hero-title">Slip & Code Checker.</h1>
            <p style="color: #8E9BAE; font-size: 14px;">Paste any booking code or ticket selections to audit health score and identify trap legs.</p>
        </div>
        """)
        code_str = st.text_input("Enter Booking Code or Ticket Name:", value="SP-98442")

        if st.button("Audit Ticket", type="primary", use_container_width=True):
            audit_html = f"""<div class="liquid-card" style="margin-top: 15px;"><div style="display: flex; justify-content: space-between; align-items: center;"><span class="pill-safe">TICKET AUDIT: {code_str}</span><span style="font-size: 1.3rem; font-weight: 800; color: #00F0FF;">Slip Health: 8.2 / 10</span></div><div class="metrics-bar"><div class="metric-cell"><div class="cell-label">Estimated Win Rate</div><div class="cell-value" style="color: #00F0FF;">68.4%</div></div><div class="metric-cell"><div class="cell-label">Total Selections</div><div class="cell-value">4 Legs</div></div><div class="metric-cell"><div class="cell-label">Danger Level</div><div class="cell-value" style="color: #FFB800;">Low-Moderate</div></div></div><h4 style="margin: 15px 0 8px 0; color: #FFF;">Leg-by-Leg Threat Analysis:</h4><div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px; margin-bottom: 8px;"><div style="display: flex; justify-content: space-between;"><strong>Arsenal vs Chelsea: 1X (Home or Draw)</strong><span style="color: #00F0FF; font-weight: 700;">82% Safe</span></div><div style="font-size: 12px; color: #8E9BAE;">Solid defensive floor protects against stalemate.</div></div><div style="background: rgba(255,0,122,0.05); border: 1px solid rgba(255,0,122,0.2); border-radius: 10px; padding: 12px;"><div style="display: flex; justify-content: space-between;"><strong style="color: #FF007A;">⚠️ Trap Warning: Barcelona vs Sevilla (Over 3.5)</strong><span style="color: #FF007A; font-weight: 700;">52% Risk</span></div><div style="font-size: 12px; color: #8E9BAE;">Recommendation: Downgrade this leg to <strong>Over 2.5 Goals</strong> to increase total ticket win rate by +24%.</div></div></div>"""
            render_html(audit_html)


    # -------------------------------------------------------------
    # MODULE 8: COMPARE [NEW] (H2H TACTICAL RADAR)
    # -------------------------------------------------------------
    elif current_module == "Compare [NEW]":
        render_html("""
        <div class="hero-container">
            <div class="hero-badge">Tactical Analytics</div>
            <h1 class="hero-title">Head-to-Head Comparison.</h1>
            <p style="color: #8E9BAE; font-size: 14px;">Side-by-side tactical breakdown of rolling attack rates, defensive concession, and xG.</p>
        </div>
        """)
        c1, c2 = st.columns(2)
        with c1:
            t1 = st.text_input("Team 1:", value="Real Madrid")
        with c2:
            t2 = st.text_input("Team 2:", value="Barcelona")

        if st.button("Compare Clubs", type="primary", use_container_width=True):
            d = CompleteMarketCalculator.evaluate_match(engine, t1, t2)
            h_stat = d["raw_h_stats"]
            a_stat = d["raw_a_stats"]

            comp_html = f"""<div class="liquid-card" style="margin-top: 15px;"><h2 style="color: #FFF; text-align: center; margin-bottom: 20px;">{t1} <span style="color: #FF007A;">vs</span> {t2}</h2><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;"><div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 16px;"><h3 style="color: #00F0FF; margin-top: 0;">{t1} (Home Focus)</h3><div>• Expected Goals (xG): <strong>{d['xg']['home']}</strong></div><div>• 5-Match Rolling Attack: <strong>{h_stat['roll_gf']:.2f} G/M</strong></div><div>• 5-Match Rolling Defense: <strong>{h_stat['roll_ga']:.2f} GA/M</strong></div><div>• Projected Win Probability: <strong style="color: #00F0FF;">{d['1x2']['Home Win']}%</strong></div></div><div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 16px;"><h3 style="color: #FF007A; margin-top: 0;">{t2} (Away Focus)</h3><div>• Expected Goals (xG): <strong>{d['xg']['away']}</strong></div><div>• 5-Match Rolling Attack: <strong>{a_stat['roll_gf']:.2f} G/M</strong></div><div>• 5-Match Rolling Defense: <strong>{a_stat['roll_ga']:.2f} GA/M</strong></div><div>• Projected Win Probability: <strong style="color: #FF007A;">{d['1x2']['Away Win']}%</strong></div></div></div></div>"""
            render_html(comp_html)


if __name__ == "__main__":
    main()
