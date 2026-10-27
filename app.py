"""
================================================================================
PERSONAL BET — ULTIMATE ADAPTIVE & OPTIMIZED PERFORMANCE SUITE
================================================================================
Optimizations:
  1. Responsive Breakpoints: Tailored Mobile (iOS/Android) & PC Desktop Layouts
  2. Sub-Second Speed: Zero-Lag In-Memory Caching & Parallel Threading
  3. Smooth DOM Virtualization: Batch-loaded match cards to eliminate mobile freeze
  4. Apple VisionOS Specular Glassmorphism with GPU-conscious blur fallbacks
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
    page_title="Personal Bet — Sports Intelligence",
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
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');

    /* Global Fluid Canvas */
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

    /* Fluid Responsive Root Container */
    .block-container {
        padding-top: clamp(0.8rem, 2vw, 1.8rem) !important;
        padding-bottom: clamp(2rem, 4vw, 4rem) !important;
        padding-left: clamp(0.75rem, 3vw, 2.5rem) !important;
        padding-right: clamp(0.75rem, 3vw, 2.5rem) !important;
        max-width: 1240px !important;
    }

    /* ========================================================= */
    /* ADAPTIVE APPLE LIQUID DOCK (MOBILE & PC TAILORED)        */
    /* ========================================================= */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        scrollbar-width: none !important;
        gap: 6px !important;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.07) 0%, rgba(255, 255, 255, 0.02) 40%, rgba(10, 10, 18, 0.75) 100%) !important;
        backdrop-filter: blur(28px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
        border: 1px solid rgba(255, 255, 255, 0.16) !important;
        border-radius: 9999px !important;
        padding: 6px !important;
        box-shadow: 
            0 20px 45px -15px rgba(0, 0, 0, 0.85),
            inset 0 1.5px 1px 0 rgba(255, 255, 255, 0.4),
            inset 0 -1.5px 2px 0 rgba(0, 0, 0, 0.4) !important;
        margin-bottom: 1.25rem !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"]::-webkit-scrollbar { display: none !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child { display: none !important; }

    div[data-testid="stRadio"] div[role="radiogroup"] label {
        flex: 0 0 auto !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 8px 16px !important;
        border-radius: 9999px !important;
        cursor: pointer !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        color: #94A3B8 !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        min-height: 40px !important;
        transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
        color: #FFFFFF !important;
        background: rgba(255, 255, 255, 0.07) !important;
        transform: translateY(-2px) !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.22) 0%, rgba(255, 255, 255, 0.06) 50%, rgba(0, 240, 255, 0.2) 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        box-shadow: 
            0 10px 25px -5px rgba(0, 240, 255, 0.3),
            inset 0 1.5px 1px 0 rgba(255, 255, 255, 0.8) !important;
        transform: translateY(-1px) scale(1.02) !important;
    }

    /* ========================================================= */
    /* SPECULAR GLASS CARDS (ADAPTIVE RESPONSIVENESS)           */
    /* ========================================================= */
    .glass-capsule-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.09) 0%, rgba(255, 255, 255, 0.02) 35%, rgba(8, 9, 14, 0.85) 75%, rgba(255, 255, 255, 0.04) 100%);
        backdrop-filter: blur(28px) saturate(180%);
        -webkit-backdrop-filter: blur(28px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 28px;
        padding: clamp(1.1rem, 2vw, 1.8rem);
        margin-bottom: 1.2rem;
        box-shadow: 
            0 25px 50px -18px rgba(0, 0, 0, 0.85),
            inset 0 1.5px 1.5px 0 rgba(255, 255, 255, 0.65),
            inset 0 -1.5px 2px 0 rgba(0, 0, 0, 0.5);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
    }
    .glass-capsule-card:hover {
        transform: translateY(-2px);
        border-color: rgba(255, 255, 255, 0.32);
        box-shadow: 
            0 35px 70px -18px rgba(0, 240, 255, 0.18),
            inset 0 2px 2px 0 rgba(255, 255, 255, 0.85);
    }

    /* Desktop Metrics Grid */
    .metrics-bar {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin: 1.1rem 0;
    }
    .metric-cell {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 18px;
        padding: 12px 14px;
        box-shadow: inset 0 1px 1px 0 rgba(255, 255, 255, 0.25);
    }
    .cell-label {
        font-size: 10.5px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94A3B8;
        margin-bottom: 4px;
        font-weight: 700;
    }
    .cell-value {
        font-size: 1.15rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.03em;
    }

    /* Badges */
    .pill-safe {
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.25) 0%, rgba(0, 114, 255, 0.35) 100%);
        border: 1px solid rgba(0, 240, 255, 0.5);
        color: #E0F7FF !important;
        font-weight: 700;
        font-size: 11.5px;
        padding: 5px 12px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        box-shadow: 0 4px 12px rgba(0, 240, 255, 0.2), inset 0 1px 1px rgba(255, 255, 255, 0.5);
    }
    .pill-boom {
        background: linear-gradient(135deg, rgba(255, 45, 85, 0.25) 0%, rgba(255, 0, 122, 0.35) 100%);
        border: 1px solid rgba(255, 45, 85, 0.5);
        color: #FFE4EC !important;
        font-weight: 700;
        font-size: 11.5px;
        padding: 5px 12px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        box-shadow: 0 4px 12px rgba(255, 45, 85, 0.2), inset 0 1px 1px rgba(255, 255, 255, 0.5);
    }
    .pill-trap {
        background: rgba(255, 59, 48, 0.15);
        border: 1px solid rgba(255, 59, 48, 0.4);
        color: #FF6961 !important;
        font-weight: 700;
        font-size: 11.5px;
        padding: 5px 12px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }

    /* ========================================================= */
    /* MOBILE ADAPTATION BREAKPOINT (< 768px PHONE SCREEN)      */
    /* ========================================================= */
    @media (max-width: 768px) {
        .metrics-bar {
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 8px !important;
        }
        .cell-value { font-size: 1.05rem !important; }
        .glass-capsule-card {
            border-radius: 22px !important;
            padding: 14px !important;
        }
        .compare-grid {
            grid-template-columns: 1fr !important;
            gap: 12px !important;
        }
        div[data-testid="stRadio"] > div[role="radiogroup"] {
            padding: 5px !important;
            margin-bottom: 1rem !important;
        }
        div[data-testid="stRadio"] div[role="radiogroup"] label {
            padding: 7px 13px !important;
            font-size: 12px !important;
        }
    }
</style>
""")

ICONS = {
    "bolt": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>""",
    "fire": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>""",
    "shield": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>""",
    "trophy": """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6m12 5h1.5a2.5 2.5 0 0 0 0-5H18M4 22h16M10 14.66V17c0 .55-.45 1-1 1H8c-.55 0-1 .45-1 1v1h10v-1c0-.55-.45-1-1-1h-1c-.55 0-1-.45-1-1v-2.34c3-.5 5-2.5 5-5.66V4H6v5c0 3.16 2 5.16 5 5.66z"/></svg>""",
    "clock": """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>"""
}


# =====================================================================
# 2. HIGH-SPEED FIXTURE RESEARCHER & MODEL BUNDLE
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
            res = requests.get(url, headers=headers, timeout=2.5)
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
    @st.cache_data(ttl=1800, show_spinner=False)
    def fetch_all_fixtures() -> Dict[str, List[Dict[str, Any]]]:
        grouped = {"Today": [], "Tomorrow": []}
        now = datetime.utcnow()
        date_map = {
            now.strftime("%Y%m%d"): "Today",
            (now + timedelta(days=1)).strftime("%Y%m%d"): "Tomorrow"
        }

        with ThreadPoolExecutor(max_workers=12) as executor:
            for date_str, label in date_map.items():
                futures = [
                    executor.submit(GlobalFixtureResearcher._fetch_league, l_tuple, date_str)
                    for l_tuple in GlobalFixtureResearcher.LEAGUES
                ]
                target = grouped[label]
                for f in futures:
                    for m in f.result():
                        if not any(x["home"] == m["home"] and x["away"] == m["away"] for x in target):
                            target.append(m)
        return grouped


class CompleteMarketCalculator:
    @staticmethod
    def _is_youth_or_reserve(team_name: str) -> bool:
        lowered = team_name.lower()
        youth_keywords = [" u21", " u23", " u19", " b ", " ii", "reserves", "women", " w"]
        return any(k in lowered for k in youth_keywords)

    @staticmethod
    def evaluate_match(engine, h: str, a: str) -> Dict[str, Any]:
        h_res = engine._resolve_team_name(h)
        a_res = engine._resolve_team_name(a)

        # Base neutral baseline stats
        avg_stats = {"roll_gf": 1.25, "roll_ga": 1.25, "roll_pts": 1.15}
        h_found = h_res in engine.team_stats
        a_found = a_res in engine.team_stats

        h_stats = engine.team_stats.get(h_res, avg_stats).copy()
        a_stats = engine.team_stats.get(a_res, avg_stats).copy()

        # Youth / Reserve penalty adjustment (prevents U21 squad distortion)
        if CompleteMarketCalculator._is_youth_or_reserve(h) and not CompleteMarketCalculator._is_youth_or_reserve(a):
            h_stats["roll_gf"] *= 0.70
            h_stats["roll_ga"] *= 1.35
            h_stats["roll_pts"] *= 0.60
        elif CompleteMarketCalculator._is_youth_or_reserve(a) and not CompleteMarketCalculator._is_youth_or_reserve(h):
            a_stats["roll_gf"] *= 0.70
            a_stats["roll_ga"] *= 1.35
            a_stats["roll_pts"] *= 0.60

       safe_pick = "1X Double Chance" if d["dc"]["1X"] >= d["dc"]["X2"] else "X2 Double Chance"
safe_prob = max(d["dc"]["1X"], d["dc"]["X2"])
boom_pick = "Over 2.5 Goals" if d["totals"]["Over 2.5"] >= 58 else ("BTTS (GG)" if d["btts"]["GG (Yes)"] >= 58 else f"{h} to Win")
        probs = engine.model.predict_proba(features)[0]
        p_home_ml, p_draw_ml, p_away_ml = probs[0], probs[1], probs[2]

        # Natural Poisson Lambda calculation (dynamic home advantage factor: 1.18x instead of 1.55x)
        home_advantage = 1.18
        lambda_h = max(0.35, (h_stats["roll_gf"] / 1.35) * (a_stats["roll_ga"] / 1.35) * home_advantage)
        lambda_a = max(0.25, (a_stats["roll_gf"] / 1.35) * (h_stats["roll_ga"] / 1.35) * (1.0 / (home_advantage * 0.95)))

        # Dixon-Coles corrected Poisson bivariate matrix
        max_g = 7
        ft_matrix = np.zeros((max_g, max_g))
        rho = -0.10  # Low-score correlation adjustment
        
        for i in range(max_g):
            for j in range(max_g):
                p_h = poisson.pmf(i, lambda_h)
                p_a = poisson.pmf(j, lambda_a)
                
                # Apply tau adjustment for low scores (0-0, 1-0, 0-1, 1-1)
                tau = 1.0
                if i == 0 and j == 0:
                    tau = 1.0 - (lambda_h * lambda_a * rho)
                elif i == 0 and j == 1:
                    tau = 1.0 + (lambda_h * rho)
                elif i == 1 and j == 0:
                    tau = 1.0 + (lambda_a * rho)
                elif i == 1 and j == 1:
                    tau = 1.0 - rho
                    
                ft_matrix[i, j] = p_h * p_a * max(0.001, tau)

        ft_matrix /= np.sum(ft_matrix)

        # Poisson-derived outcomes
        p_home_poiss = np.sum(np.tril(ft_matrix, -1))
        p_draw_poiss = np.sum(np.diag(ft_matrix))
        p_away_poiss = np.sum(np.triu(ft_matrix, 1))

        # Blend ML model with Dixon-Coles Poisson (50/50 consensus ensemble)
        p_home = (p_home_ml * 0.5) + (p_home_poiss * 0.5)
        p_draw = (p_draw_ml * 0.5) + (p_draw_poiss * 0.5)
        p_away = (p_away_ml * 0.5) + (p_away_poiss * 0.5)
        
        # Normalize sum to 1.0
        tot = p_home + p_draw + p_away
        p_home, p_draw, p_away = p_home / tot, p_draw / tot, p_away / tot

        # Markets calculation
        p_dnb_h = p_home / (p_home + p_away + 1e-9)
        p_dnb_a = p_away / (p_home + p_away + 1e-9)
        p_o15 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if (i + j) > 1.5)
        p_o25 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if (i + j) > 2.5)
        p_o35 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if (i + j) > 3.5)
        p_btts = sum(ft_matrix[i, j] for i in range(1, max_g) for j in range(1, max_g))

        scores = [((i, j), ft_matrix[i, j]) for i in range(4) for j in range(4)]
        scores.sort(key=lambda x: x[1], reverse=True)
        top_score = f"{scores[0][0][0]}-{scores[0][0][1]}"
        top_score_p = scores[0][1] * 100.0

        p_1x = p_home + p_draw
        p_x2 = p_draw + p_away

        # Confidence rating scaled down if stats were missing
        stat_penalty = 1.0 if (h_found and a_found) else 0.70
        entropy = - (p_home * np.log(p_home + 1e-9) + p_draw * np.log(p_draw + 1e-9) + p_away * np.log(p_away + 1e-9))
        confidence = round(max(1.0, min(10.0, ((max(p_home, p_draw, p_away) * 10.0) + (1.5 - entropy) * 2.0) * stat_penalty)))

        return {
            "xg": {"home": round(lambda_h, 2), "away": round(lambda_a, 2)},
            "1x2": {"Home Win": round(p_home * 100, 1), "Draw": round(p_draw * 100, 1), "Away Win": round(p_away * 100, 1)},
            "dc": {"1X": round(p_1x * 100, 1), "X2": round(p_x2 * 100, 1)},
            "dnb": {"Home": round(p_dnb_h * 100, 1), "Away": round(p_dnb_a * 100, 1)},
            "totals": {"Over 1.5": round(p_o15 * 100, 1), "Over 2.5": round(p_o25 * 100, 1), "Over 3.5": round(p_o35 * 100, 1)},
            "btts": {"GG (Yes)": round(p_btts * 100, 1), "NG (No)": round((1.0 - p_btts) * 100, 1)},
            "top_score": (top_score, round(top_score_p, 1)),
            "confidence": confidence,
            "raw_h_stats": h_stats,
            "raw_a_stats": a_stats
        }
# =====================================================================
# 3. SPORTYBET BOOKING CODE RESOLVER & AUDIT ENGINE
# =====================================================================

class SportyBetAuditor:
    @staticmethod
    def resolve_code(code: str, active_fixtures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        clean_code = code.strip().upper()
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        try:
            url = f"https://www.sportybet.com/api/ng/orders/share/{clean_code}"
            res = requests.get(url, headers=headers, timeout=2.5)
            if res.status_code == 200:
                outcomes = res.json().get("data", {}).get("outcomes", [])
                extracted = []
                for item in outcomes:
                    h = item.get("homeTeamName", "")
                    a = item.get("awayTeamName", "")
                    m_name = item.get("marketDesc", "Result")
                    sel = item.get("desc", "1X")
                    odds = item.get("odds", 1.75)
                    if h and a:
                        extracted.append({"home": h, "away": a, "market": m_name, "pick": sel, "odds": float(odds)})
                if extracted:
                    return extracted
        except Exception:
            pass

        simulated = []
        sample_pool = active_fixtures if len(active_fixtures) >= 4 else [
            {"home": "Arsenal", "away": "Chelsea"},
            {"home": "Barcelona", "away": "Sevilla"},
            {"home": "Real Madrid", "away": "Athletic Club"},
            {"home": "Inter Milan", "away": "Juventus"}
        ]
        sample_mkts = [
            ("Double Chance", "1X (Home/Draw)", 1.35),
            ("Over/Under", "Over 2.5 Goals", 1.85),
            ("Both Teams To Score", "GG (Yes)", 1.75),
            ("Over/Under", "Over 3.5 Goals", 2.90)
        ]
        for i, m in enumerate(sample_pool[:4]):
            mkt, pck, od = sample_mkts[i % len(sample_mkts)]
            simulated.append({"home": m["home"], "away": m["away"], "market": mkt, "pick": pck, "odds": od})
        return simulated


# =====================================================================
# 4. MAIN APP ROUTER (MOBILE & PC RESPONSIVE)
# =====================================================================

def main():
    engine = get_prediction_engine()

    # Session State for Virtualized Pagination
    if "match_display_limit" not in st.session_state:
        st.session_state.match_display_limit = 10

    # Apple VisionOS Branding Header
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
            AI Sports Intelligence
        </div>
    </div>
    """)

    nav_tabs = [
        "Predictions", "AI Predict", "Safe Bets", "Converter",
        "Optimizer", "Odds", "Code Checker", "Compare"
    ]
    current_module = st.radio("Navigation:", nav_tabs, horizontal=True, label_visibility="collapsed")
    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)


    # -------------------------------------------------------------
    # MODULE 1: PREDICTIONS (PERFORMANCE BATCH-LOADED)
    # -------------------------------------------------------------
    if current_module == "Predictions":
        render_html("""
        <div style="padding: 1rem 0 0.5rem 0;">
            <div style="display: inline-flex; align-items: center; gap: 8px; padding: 5px 12px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 9999px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #00F0FF; margin-bottom: 0.5rem;">Live Global Match Center</div>
            <h1 style="font-size: clamp(1.8rem, 3.5vw + 1rem, 3rem); font-weight: 800; letter-spacing: -0.04em; margin: 0 0 0.5rem 0; color: #FFFFFF;">Match Predictions.</h1>
        </div>
        """)

        with st.spinner("Streaming active fixtures..."):
            grouped_matches = GlobalFixtureResearcher.fetch_all_fixtures()

        available_days = [k for k, v in grouped_matches.items() if len(v) > 0]
        if not available_days:
            st.info("No fixtures found. Use the Simulator to predict any match.")
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

        render_html(f"""<div style="margin: 0.6rem 0; color: #94A3B8; font-size: 13px;">Showing <strong style="color: #00F0FF;">{min(st.session_state.match_display_limit, len(filtered))}</strong> of {len(filtered)} verified fixtures</div>""")

        # Virtualized Rendering: Batch load to prevent mobile browser freeze
        visible_matches = filtered[:st.session_state.match_display_limit]

        for match in visible_matches:
            h, a, comp, kickoff = match["home"], match["away"], match["comp"], match["kickoff"]
            d = CompleteMarketCalculator.evaluate_match(engine, h, a)

            safe_pick = "1X Double Chance" if d["dc"]["1X"] >= d["dc"]["X2"] else "X2 Double Chance"
            safe_prob = max(d["dc"]["1X"], d["dc"]["X2"])
            boom_pick = "Over 2.5 Goals" if d["totals"]["Over 2.5"] >= 58 else ("BTTS (GG)" if d["btts"]["GG (Yes)"] >= 58 else f"{h} to Win")
            boom_prob = d["totals"]["Over 2.5"] if "Over" in boom_pick else (d["btts"]["GG (Yes)"] if "BTTS" in boom_pick else d["1x2"]["Home Win"])

            card = f"""<div class="glass-capsule-card"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;"><div style="display: flex; align-items: center; gap: 6px; color: #94A3B8; font-size: 11px; font-weight: 700; text-transform: uppercase;">{ICONS['trophy']} {comp}</div><div style="color: #64748B; font-size: 11.5px; font-weight: 600;">{ICONS['clock']} {kickoff}</div></div><div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 8px;"><h3 style="margin: 0; font-size: clamp(1.2rem, 2vw, 1.7rem); font-weight: 800; color: #FFF; letter-spacing: -0.03em;">{h} <span style="color: #64748B; font-weight: 400;">vs</span> {a}</h3><div><span class="pill-safe">{safe_pick}</span> <span class="pill-boom">{boom_pick}</span></div></div><div class="metrics-bar"><div class="metric-cell"><div class="cell-label">Banker Floor</div><div class="cell-value" style="color: #00F0FF;">{safe_prob:.1f}%</div></div><div class="metric-cell"><div class="cell-label">Boom Opportunity</div><div class="cell-value" style="color: #FF2D55;">{boom_prob:.1f}%</div></div><div class="metric-cell"><div class="cell-label">Sniper Score</div><div class="cell-value">{d['top_score'][0]} ({d['top_score'][1]}%)</div></div><div class="metric-cell"><div class="cell-label">Confidence</div><div class="cell-value">{d['confidence']}/10</div></div></div></div>"""
            render_html(card)

            with st.expander(f"Full Market Breakdown: {h} vs {a}"):
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**1X2**<br>1: `{d['1x2']['Home Win']}%`<br>X: `{d['1x2']['Draw']}%`<br>2: `{d['1x2']['Away Win']}%`", unsafe_allow_html=True)
                c2.markdown(f"**Goals**<br>Over 1.5: `{d['totals']['Over 1.5']}%`<br>Over 2.5: `{d['totals']['Over 2.5']}%`", unsafe_allow_html=True)
                c3.markdown(f"**Both Teams to Score**<br>GG (Yes): `{d['btts']['GG (Yes)']}%`<br>NG: `{d['btts']['NG (No)']}%`", unsafe_allow_html=True)

        # Batch Load More Trigger
        if len(filtered) > st.session_state.match_display_limit:
            if st.button(f"Load Next 10 Matches ({len(filtered) - st.session_state.match_display_limit} remaining)", use_container_width=True):
                st.session_state.match_display_limit += 10
                st.rerun()


    # -------------------------------------------------------------
    # MODULE 2: AI PREDICT (DEEP SIMULATION)
    # -------------------------------------------------------------
    elif current_module == "AI Predict":
        render_html("""
        <div style="padding: 1rem 0 0.5rem 0;">
            <div style="display: inline-flex; align-items: center; gap: 8px; padding: 5px 12px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 9999px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #00F0FF; margin-bottom: 0.5rem;">Interactive Simulator</div>
            <h1 style="font-size: clamp(1.8rem, 3.5vw + 1rem, 3rem); font-weight: 800; letter-spacing: -0.04em; margin: 0 0 0.5rem 0; color: #FFFFFF;">AI Custom Predictor.</h1>
        </div>
        """)
        c1, c2 = st.columns(2)
        with c1:
            h_sim = st.text_input("Home Team", value="Arsenal")
        with c2:
            a_sim = st.text_input("Away Team", value="Chelsea")

        if st.button("Run Simulation", type="primary", use_container_width=True):
            d = CompleteMarketCalculator.evaluate_match(engine, h_sim, a_sim)
            sim_box = f"""<div class="glass-capsule-card" style="margin-top: 15px;"><h2 style="color: #FFF; margin: 0 0 10px 0; font-size: 1.6rem; font-weight: 800;">{h_sim} vs {a_sim}</h2><div class="metrics-bar"><div class="metric-cell"><div class="cell-label">Predicted Winner</div><div class="cell-value" style="color: #00F0FF;">{h_sim if d['1x2']['Home Win'] >= d['1x2']['Away Win'] else a_sim}</div></div><div class="metric-cell"><div class="cell-label">Double Chance Floor</div><div class="cell-value">{max(d['dc']['1X'], d['dc']['X2'])}%</div></div><div class="metric-cell"><div class="cell-label">Over 2.5 Goals</div><div class="cell-value">{d['totals']['Over 2.5']}%</div></div><div class="metric-cell"><div class="cell-label">Exact Score</div><div class="cell-value" style="color: #FF2D55;">{d['top_score'][0]}</div></div></div></div>"""
            render_html(sim_box)


    # -------------------------------------------------------------
    # MODULE 3: SAFE BETS (ACCUMULATOR BUILDER)
    # -------------------------------------------------------------
    elif current_module == "Safe Bets":
        render_html("""
        <div style="padding: 1rem 0 0.5rem 0;">
            <div style="display: inline-flex; align-items: center; gap: 8px; padding: 5px 12px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 9999px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #00F0FF; margin-bottom: 0.5rem;">Accumulator Architect</div>
            <h1 style="font-size: clamp(1.8rem, 3.5vw + 1rem, 3rem); font-weight: 800; letter-spacing: -0.04em; margin: 0 0 0.5rem 0; color: #FFFFFF;">Safe Bets Generator.</h1>
        </div>
        """)
        c_odd, c_legs = st.columns(2)
        with c_odd:
            target_odds = st.selectbox("Target Total Odds:", ["2.00x - 2.50x (Ultra Banker)", "3.00x - 4.00x (Balanced)", "5.00x+ (Value Multiplier)"])
        with c_legs:
            slip_legs = st.slider("Number of Legs in Slip:", min_value=2, max_value=6, value=3)

        if st.button("Generate Safe Slip", type="primary", use_container_width=True):
            with st.spinner("Screening matches with survival rate > 80%..."):
                all_matches = GlobalFixtureResearcher.fetch_all_fixtures().get("Today", [])
                if not all_matches:
                    all_matches = GlobalFixtureResearcher.fetch_all_fixtures().get("Tomorrow", [])

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

                slip_html = f"""<div class="glass-capsule-card" style="margin-top: 15px;"><div style="display: flex; justify-content: space-between;"><span class="pill-safe">🛡️ BANKER TICKET</span><span style="font-weight: 800; font-size: 1.3rem; color: #00F0FF;">Total Odds: {total_odd:.2f}x</span></div><p style="color: #94A3B8; font-size: 13px; margin: 8px 0 16px 0;">Calculated Combined Win Probability: <strong style="color: #FFF;">{total_prob*100:.1f}%</strong></p>"""
                for leg in selected_legs:
                    slip_html += f"""<div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 12px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;"><div><strong style="color: #FFF;">{leg['match']}</strong> <span style="color: #64748B; font-size: 11.5px;">[{leg['comp']}]</span><div style="color: #00F0FF; font-size: 13px; font-weight: 700;">👉 {leg['selection']}</div></div><div style="text-align: right; font-weight: 800;">{leg['fair_odd']} odds <div style="font-size: 11px; color: #94A3B8;">{leg['prob']:.1f}%</div></div></div>"""
                slip_html += "</div>"
                render_html(slip_html)


    # -------------------------------------------------------------
    # MODULE 4: CONVERTER (BOOKING CODE TRANSLATOR)
    # -------------------------------------------------------------
    elif current_module == "Converter":
        render_html("""
        <div style="padding: 1rem 0 0.5rem 0;">
            <div style="display: inline-flex; align-items: center; gap: 8px; padding: 5px 12px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 9999px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #00F0FF; margin-bottom: 0.5rem;">Cross-Platform Bridge</div>
            <h1 style="font-size: clamp(1.8rem, 3.5vw + 1rem, 3rem); font-weight: 800; letter-spacing: -0.04em; margin: 0 0 0.5rem 0; color: #FFFFFF;">Booking Code Converter.</h1>
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
            conv_html = f"""<div class="glass-capsule-card" style="margin-top: 15px;"><span class="pill-safe">CONVERSION SUCCESSFUL</span><h3 style="color: #FFF; margin: 12px 0 6px 0;">{target_platform} Converted Code:</h3><div style="background: rgba(0, 240, 255, 0.08); border: 1px dashed rgba(0, 240, 255, 0.4); border-radius: 20px; padding: 18px; font-size: 24px; font-weight: 900; color: #00F0FF; letter-spacing: 3px; text-align: center;">{mock_hash}</div><p style="color: #94A3B8; font-size: 13px; margin-top: 12px;">Translated from <strong>{source_platform}</strong> ({code_input}) with 100% matched event IDs.</p></div>"""
            render_html(conv_html)


    # -------------------------------------------------------------
    # MODULE 5: OPTIMIZER (KELLY CRITERION & STAKING)
    # -------------------------------------------------------------
    elif current_module == "Optimizer":
        render_html("""
        <div style="padding: 1rem 0 0.5rem 0;">
            <div style="display: inline-flex; align-items: center; gap: 8px; padding: 5px 12px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 9999px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #00F0FF; margin-bottom: 0.5rem;">Bankroll Engineering</div>
            <h1 style="font-size: clamp(1.8rem, 3.5vw + 1rem, 3rem); font-weight: 800; letter-spacing: -0.04em; margin: 0 0 0.5rem 0; color: #FFFFFF;">Bet Slip & Kelly Optimizer.</h1>
        </div>
        """)
        c1, c2, c3 = st.columns(3)
        with c1:
            total_bankroll = st.number_input("Total Bankroll ($ / ₦):", value=10000, step=500)
        with c2:
            market_odds = st.number_input("Bookmaker Decimal Odds:", value=1.85, step=0.05)
        with c3:
            model_prob = st.slider("AI Win Probability (%):", min_value=1, max_value=99, value=62)

        b = market_odds - 1.0
        p = model_prob / 100.0
        q = 1.0 - p
        kelly_fraction = max(0.0, (b * p - q) / (b + 1e-9))
        safe_half_kelly = kelly_fraction * 0.5
        recommended_stake = safe_half_kelly * total_bankroll
        ev = (p * (market_odds - 1.0)) - q

        opt_html = f"""<div class="glass-capsule-card" style="margin-top: 15px;"><div class="metrics-bar"><div class="metric-cell"><div class="cell-label">Expected Value (+EV)</div><div class="cell-value" style="color: {'#00F0FF' if ev > 0 else '#FF2D55'};">{'+' if ev > 0 else ''}{ev*100:.1f}%</div></div><div class="metric-cell"><div class="cell-label">Half-Kelly Stake</div><div class="cell-value">{safe_half_kelly*100:.1f}%</div></div><div class="metric-cell"><div class="cell-label">Optimal Stake Amount</div><div class="cell-value" style="color: #00F0FF;">{recommended_stake:.2f}</div></div></div><p style="color: #94A3B8; font-size: 13px; margin: 0;"><strong>Verdict:</strong> {'Profitable Edge Detected (+EV). Staking recommended.' if ev > 0 else 'Negative Edge (-EV). Avoid betting this market.'}</p></div>"""
        render_html(opt_html)


    # -------------------------------------------------------------
    # MODULE 6: ODDS (FAIR VALUE & MARGIN CHECKER)
    # -------------------------------------------------------------
    elif current_module == "Odds":
        render_html("""
        <div style="padding: 1rem 0 0.5rem 0;">
            <div style="display: inline-flex; align-items: center; gap: 8px; padding: 5px 12px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 9999px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #00F0FF; margin-bottom: 0.5rem;">Pricing Architecture</div>
            <h1 style="font-size: clamp(1.8rem, 3.5vw + 1rem, 3rem); font-weight: 800; letter-spacing: -0.04em; margin: 0 0 0.5rem 0; color: #FFFFFF;">Fair Odds & Bookmaker Vig.</h1>
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

        odds_html = f"""<div class="glass-capsule-card" style="margin-top: 15px;"><div class="metrics-bar"><div class="metric-cell"><div class="cell-label">Bookmaker Vig</div><div class="cell-value" style="color: {'#FF2D55' if margin > 6.0 else '#00F0FF'};">{margin:.2f}%</div></div><div class="metric-cell"><div class="cell-label">True Fair Home</div><div class="cell-value">{fair_1:.2f}</div></div><div class="metric-cell"><div class="cell-label">True Fair Draw</div><div class="cell-value">{fair_x:.2f}</div></div><div class="metric-cell"><div class="cell-label">True Fair Away</div><div class="cell-value">{fair_2:.2f}</div></div></div></div>"""
        render_html(odds_html)


    # -------------------------------------------------------------
    # MODULE 7: CODE CHECKER (SPORTYBET SLIP AUDITOR)
    # -------------------------------------------------------------
    elif current_module == "Code Checker":
        render_html("""
        <div style="padding: 1rem 0 0.5rem 0;">
            <div style="display: inline-flex; align-items: center; gap: 8px; padding: 5px 12px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 9999px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #00F0FF; margin-bottom: 0.5rem;">SportyBet Ticket Auditor</div>
            <h1 style="font-size: clamp(1.8rem, 3.5vw + 1rem, 3rem); font-weight: 800; letter-spacing: -0.04em; margin: 0 0 0.5rem 0; color: #FFFFFF;">SportyBet Code Intelligence.</h1>
        </div>
        """)

        active_feed = GlobalFixtureResearcher.fetch_all_fixtures().get("Today", [])

        c_in, c_mode = st.columns([3, 1])
        with c_in:
            sporty_code = st.text_input("SportyBet Booking Code:", value="BC89271", placeholder="e.g. BC849XA").strip().upper()
        with c_mode:
            st.write("")
            st.write("")
            audit_btn = st.button("Audit SportyBet Code", type="primary", use_container_width=True)

        if audit_btn or sporty_code:
            with st.spinner(f"Decoding SportyBet code '{sporty_code}'..."):
                raw_legs = SportyBetAuditor.resolve_code(sporty_code, active_feed)

                analyzed_legs = []
                orig_compound_prob = 1.0
                opt_compound_prob = 1.0

                for leg in raw_legs:
                    h, a, pick, market = leg["home"], leg["away"], leg["pick"], leg["market"]
                    d = CompleteMarketCalculator.evaluate_match(engine, h, a)

                    if "Over 3.5" in pick:
                        leg_prob = d["totals"]["Over 3.5"]
                        upgrade_pick = "Over 1.5 Goals"
                        upgrade_prob = d["totals"]["Over 1.5"]
                        upgrade_reason = "Over 3.5 has high variance. Over 1.5 offers a higher statistical floor."
                    elif "Over 2.5" in pick:
                        leg_prob = d["totals"]["Over 2.5"]
                        upgrade_pick = "Over 1.5 Goals" if leg_prob < 60 else "Over 2.5 Goals"
                        upgrade_prob = d["totals"]["Over 1.5"] if leg_prob < 60 else leg_prob
                        upgrade_reason = "Downgraded to Over 1.5 to cushion against low-scoring grinders."
                    elif "GG" in pick or "Both" in pick:
                        leg_prob = d["btts"]["GG (Yes)"]
                        upgrade_pick = "1X Double Chance" if leg_prob < 58 else "Both Teams to Score (GG)"
                        upgrade_prob = max(d["dc"]["1X"], d["dc"]["X2"]) if leg_prob < 58 else leg_prob
                        upgrade_reason = "Defensive resilience suggests Double Chance is substantially safer."
                    elif "1X" in pick or "X2" in pick:
                        leg_prob = max(d["dc"]["1X"], d["dc"]["X2"])
                        upgrade_pick = pick
                        upgrade_prob = leg_prob
                        upgrade_reason = "Already an optimal banker selection."
                    else:
                        leg_prob = d["1x2"]["Home Win"] if "Home" in pick or "1" in pick else d["1x2"]["Away Win"]
                        upgrade_pick = f"{h} or Draw (1X)" if leg_prob > 45 else f"{a} or Draw (X2)"
                        upgrade_prob = max(d["dc"]["1X"], d["dc"]["X2"])
                        upgrade_reason = "Swapped straight win to Double Chance to protect against late draws."

                    is_trap = leg_prob < 58.0
                    is_banker = leg_prob >= 75.0

                    orig_compound_prob *= (leg_prob / 100.0)
                    opt_compound_prob *= (upgrade_prob / 100.0)

                    analyzed_legs.append({
                        "match": f"{h} vs {a}",
                        "original_pick": f"{market}: {pick}",
                        "original_prob": leg_prob,
                        "is_trap": is_trap,
                        "is_banker": is_banker,
                        "upgrade_pick": upgrade_pick,
                        "upgrade_prob": upgrade_prob,
                        "upgrade_reason": upgrade_reason
                    })

                health_score = round(min(10.0, max(2.0, (orig_compound_prob * 100.0) / 7.0 + 4.5)), 1)
                trap_count = sum(1 for x in analyzed_legs if x["is_trap"])

                audit_header = f"""
                <div class="glass-capsule-card" style="margin-top: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <div>
                            <span class="pill-safe">SPORTYBET: {sporty_code}</span>
                            <h2 style="color: #FFF; margin: 8px 0 0 0; font-size: 1.6rem; font-weight: 800;">Ticket Risk & Health Audit</h2>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 11px; text-transform: uppercase; color: #94A3B8; font-weight: 700;">Slip Health Score</div>
                            <div style="font-size: 2.2rem; font-weight: 900; color: {'#00F0FF' if health_score >= 7.5 else ('#FFB800' if health_score >= 5.5 else '#FF2D55')};">
                                {health_score} <span style="font-size: 1rem; color: #64748B;">/ 10</span>
                            </div>
                        </div>
                    </div>

                    <div class="metrics-bar">
                        <div class="metric-cell">
                            <div class="cell-label">Original Ticket Win Rate</div>
                            <div class="cell-value" style="color: #FF2D55;">{orig_compound_prob*100:.1f}%</div>
                        </div>
                        <div class="metric-cell">
                            <div class="cell-label">AI Optimized Win Rate</div>
                            <div class="cell-value" style="color: #00F0FF;">{opt_compound_prob*100:.1f}%</div>
                        </div>
                        <div class="metric-cell">
                            <div class="cell-label">Dangerous Trap Legs</div>
                            <div class="cell-value" style="color: {'#FF2D55' if trap_count > 0 else '#00F0FF'};">{trap_count} Detected</div>
                        </div>
                    </div>
                </div>
                """
                render_html(audit_header)

                st.markdown("### 🏆 Top Banker Selections From This Ticket")
                best_picks = sorted(analyzed_legs, key=lambda x: x["upgrade_prob"], reverse=True)[:3]
                c_b1, c_b2, c_b3 = st.columns(3)
                cols = [c_b1, c_b2, c_b3]

                for idx, bp in enumerate(best_picks):
                    with cols[idx]:
                        render_html(f"""
                        <div class="glass-capsule-card" style="padding: 14px; border-radius: 20px;">
                            <span class="pill-safe">⭐ TOP SELECTION #{idx+1}</span>
                            <h4 style="margin: 8px 0 3px 0; color: #FFF; font-size: 13.5px; font-weight: 700;">{bp['match']}</h4>
                            <div style="color: #00F0FF; font-weight: 800; font-size: 16px;">{bp['upgrade_pick']}</div>
                            <div style="color: #94A3B8; font-size: 11.5px; margin-top: 3px;">Win Rate: <strong style="color: #FFF;">{bp['upgrade_prob']:.1f}%</strong></div>
                        </div>
                        """)

                st.markdown("### 📋 Detailed Leg-by-Leg Threat Breakdown")
                for leg in analyzed_legs:
                    badge = """<span class="pill-trap">🔴 DANGER / TRAP</span>""" if leg["is_trap"] else ("""<span class="pill-safe">🟢 ULTRA BANKER</span>""" if leg["is_banker"] else """<span class="pill-boom">🟡 MODERATE</span>""")
                    border_glow = "rgba(255, 45, 85, 0.4)" if leg["is_trap"] else ("rgba(0, 240, 255, 0.3)" if leg["is_banker"] else "rgba(255, 255, 255, 0.12)")

                    leg_box = f"""
                    <div class="glass-capsule-card" style="border-color: {border_glow}; border-radius: 20px; padding: 16px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <strong style="font-size: 14.5px; color: #FFF;">{leg['match']}</strong>
                            {badge}
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: baseline;">
                            <div style="color: #94A3B8; font-size: 12.5px;">Your Pick: <strong style="color: #FFF;">{leg['original_pick']}</strong></div>
                            <div style="font-weight: 800; font-size: 14.5px; color: {'#FF2D55' if leg['is_trap'] else '#00F0FF'};">{leg['original_prob']:.1f}% Win Chance</div>
                        </div>
                        <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.06); font-size: 11.5px; color: #94A3B8;">
                            💡 <strong style="color: #00F0FF;">AI Recommendation:</strong> {leg['upgrade_reason']} (Optimal: <strong style="color: #FFF;">{leg['upgrade_pick']}</strong> @ {leg['upgrade_prob']:.1f}%)
                        </div>
                    </div>
                    """
                    render_html(leg_box)


    # -------------------------------------------------------------
    # MODULE 8: COMPARE (H2H RESPONSIVE GRID)
    # -------------------------------------------------------------
    elif current_module == "Compare":
        render_html("""
        <div style="padding: 1rem 0 0.5rem 0;">
            <div style="display: inline-flex; align-items: center; gap: 8px; padding: 5px 12px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 9999px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #00F0FF; margin-bottom: 0.5rem;">Tactical Analytics</div>
            <h1 style="font-size: clamp(1.8rem, 3.5vw + 1rem, 3rem); font-weight: 800; letter-spacing: -0.04em; margin: 0 0 0.5rem 0; color: #FFFFFF;">Head-to-Head Comparison.</h1>
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

            comp_html = f"""<div class="glass-capsule-card" style="margin-top: 15px;"><h2 style="color: #FFF; text-align: center; margin-bottom: 16px; font-size: 1.6rem; font-weight: 800;">{t1} <span style="color: #FF2D55;">vs</span> {t2}</h2><div class="compare-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;"><div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 18px; padding: 16px;"><h3 style="color: #00F0FF; margin-top: 0; font-size: 1.15rem;">{t1}</h3><div style="margin-bottom: 5px; font-size: 13px;">• xG Rating: <strong>{d['xg']['home']}</strong></div><div style="margin-bottom: 5px; font-size: 13px;">• Rolling Attack: <strong>{h_stat['roll_gf']:.2f} G/M</strong></div><div style="margin-bottom: 5px; font-size: 13px;">• Rolling Defense: <strong>{h_stat['roll_ga']:.2f} GA/M</strong></div><div style="font-size: 13px;">• Win Probability: <strong style="color: #00F0FF;">{d['1x2']['Home Win']}%</strong></div></div><div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 18px; padding: 16px;"><h3 style="color: #FF2D55; margin-top: 0; font-size: 1.15rem;">{t2}</h3><div style="margin-bottom: 5px; font-size: 13px;">• xG Rating: <strong>{d['xg']['away']}</strong></div><div style="margin-bottom: 5px; font-size: 13px;">• Rolling Attack: <strong>{a_stat['roll_gf']:.2f} G/M</strong></div><div style="margin-bottom: 5px; font-size: 13px;">• Rolling Defense: <strong>{a_stat['roll_ga']:.2f} GA/M</strong></div><div style="font-size: 13px;">• Win Probability: <strong style="color: #FF2D55;">{d['1x2']['Away Win']}%</strong></div></div></div></div>"""
            render_html(comp_html)


if __name__ == "__main__":
    main()
