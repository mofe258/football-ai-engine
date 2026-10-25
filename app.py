"""
================================================================================
AI FOOTBALL BETTING ANALYTICS & MULTI-MARKET WEB DASHBOARD (STREAMLIT)
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

# Import model pipeline from football_engine
from football_engine import build_or_load_pipeline


# =====================================================================
# 1. UI CONFIGURATION & STYLING
# =====================================================================

st.set_page_config(
    page_title="AI Match & Multi-Market Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Sportsbook Dark-Theme CSS
st.markdown("""
<style>
    .main { background-color: #0b0e14; }
    .stApp { background-color: #0b0e14; color: #e6edf3; }
    .match-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)


# =====================================================================
# 2. CACHED ENGINE & PREDICTION LOGIC
# =====================================================================

@st.cache_resource(show_spinner="Initializing AI prediction models...")
def get_prediction_engine():
    """Loads and caches the trained ML pipeline bundle in RAM."""
    return build_or_load_pipeline(force_retrain=False)


@st.cache_data(ttl=1800, show_spinner=False)
def get_cached_prediction(h: str, a: str) -> Dict[str, Any]:
    """Caches predictions for 30 minutes so page clicks are instantaneous."""
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
    @st.cache_data(ttl=900, show_spinner="Fetching verified live schedules...")
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
                                    team_name = c.get("team", {}).get("displayName") or c.get("team", {}).get("name")
                                    if c.get("homeAway") == "home":
                                        h = team_name
                                    else:
                                        a = team_name

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


# =====================================================================
# 3. COMPLETE PROBABILISTIC MARKET ENGINE
# =====================================================================

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

        # DNB
        denom = p_home_ml + p_away_ml + 1e-9
        p_dnb_h = p_home_ml / denom
        p_dnb_a = p_away_ml / denom

        # Totals
        p_o15 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if (i + j) > 1.5)
        p_o25 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if (i + j) > 2.5)
        p_u35 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if (i + j) < 3.5)

        # BTTS
        p_btts = sum(ft_matrix[i, j] for i in range(1, max_g) for j in range(1, max_g))

        # Multi Goal
        p_mg_13 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if 1 <= (i + j) <= 3)
        p_mg_24 = sum(ft_matrix[i, j] for i in range(max_g) for j in range(max_g) if 2 <= (i + j) <= 4)

        # Top Correct Score
        score_candidates = [((i, j), ft_matrix[i, j]) for i in range(5) for j in range(5)]
        score_candidates.sort(key=lambda x: x[1], reverse=True)
        top_score = f"{score_candidates[0][0][0]}-{score_candidates[0][0][1]}"
        top_score_p = score_candidates[0][1] * 100.0

        # Half-Time Over 0.5
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
# 4. STREAMLIT USER INTERFACE
# =====================================================================

def main():
    # --- SIDEBAR CONTROLS ---
    st.sidebar.title("⚡ Control Center")
    app_mode = st.sidebar.radio("Navigation", ["📅 Scheduled Live Matches", "🔍 Custom Match Simulator"])
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🔄 Force Refresh Fixtures"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.info("💡 **Hot Reload Active:** Edit any python logic, save the file, and changes will instantly show here.")

    # --- MODE 1: SCHEDULED LIVE MATCHES ---
    if app_mode == "📅 Scheduled Live Matches":
        st.title("⚽ AI Football Multi-Market Analytics Dashboard")
        st.caption("Live prediction engine continuously synthesizing ML rolling form, Poisson matrices, and breaking team news.")

        grouped_matches = RealTimeFixtureResearcher.fetch_fixtures(days_ahead=2)
        total_games = sum(len(v) for v in grouped_matches.values())

        if total_games == 0:
            st.warning("No active matches found for Today or Tomorrow in top monitored leagues.")
            return

        available_tabs = [k for k, v in grouped_matches.items() if len(v) > 0]
        selected_tab = st.radio("Select Matchday:", available_tabs, horizontal=True)

        fixtures_to_show = grouped_matches[selected_tab]
        st.markdown(f"### 📋 Showing {len(fixtures_to_show)} Confirmed Fixtures for **{selected_tab}**")

        for idx, match in enumerate(fixtures_to_show):
            h, a, comp, kickoff = match["home"], match["away"], match["comp"], match["kickoff"]

            # Progress indicator per match
            with st.spinner(f"Analyzing {h} vs {a}..."):
                rep = get_cached_prediction(h, a)
                calc = CompleteMarketCalculator.calculate(rep["xg"]["home_xg"], rep["xg"]["away_xg"], rep["1x2"])

            # Card Container
            st.markdown(f"""
            <div class="match-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 13px; color: #8b949e; text-transform: uppercase;">🏆 {comp}</span>
                    <span style="font-size: 13px; color: #58a6ff;">⏰ Kickoff: {kickoff}</span>
                </div>
                <h2 style="margin: 8px 0; color: #ffffff;">{h} <span style="color: #ff4b2b;">vs</span> {a}</h2>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)
            
            # Safe Banker
            p_1x = rep["double_chance"]["1X (Home or Draw)"]
            p_x2 = rep["double_chance"]["X2 (Draw or Away)"]
            safe_name = "1X (Home/Draw)" if p_1x >= p_x2 else "X2 (Draw/Away)"
            safe_val = max(p_1x, p_x2)

            # Boom Pick
            boom_pick = "Over 2.5 Goals" if calc["totals"]["Over 2.5"] >= 58 else (
                "Both Teams To Score (GG)" if calc["btts"]["GG (Yes)"] >= 58 else f"{h} to Win"
            )
            boom_val = calc["totals"]["Over 2.5"] if "Over" in boom_pick else (
                calc["btts"]["GG (Yes)"] if "GG" in boom_pick else rep["1x2"]["Home Win"]
            )

            col1.metric("🛡️ SAFE BANKER", safe_name, f"{safe_val:.1f}%")
            col2.metric("💥 BOOM MARKET", boom_pick, f"{boom_val:.1f}%")
            col3.metric("🎯 EXACT SCORE", calc["top_score"][0], f"{calc['top_score'][1]}% prob")
            col4.metric("📊 AI CONFIDENCE", f"{rep['confidence']}/10", "Rating")

            # Detailed Expandable Tabs
            with st.expander(f"📊 View Full Market Catalog for {h} vs {a}"):
                m_tab1, m_tab2, m_tab3, m_tab4 = st.tabs([
                    "1X2 & DNB", "Goals & Scoring", "Half-Time Markets", "Multi-Goal & Combos"
                ])

                with m_tab1:
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**1X2 Match Result**<br>1: `{rep['1x2']['Home Win']}%`<br>X: `{rep['1x2']['Draw']}%`<br>2: `{rep['1x2']['Away Win']}%`", unsafe_allow_html=True)
                    c2.markdown(f"**Draw No Bet (DNB)**<br>{h}: `{calc['dnb']['Home']}%`<br>{a}: `{calc['dnb']['Away']}%`", unsafe_allow_html=True)
                    c3.markdown(f"**Double Chance**<br>1X: `{rep['double_chance']['1X (Home or Draw)']}%`<br>X2: `{rep['double_chance']['X2 (Draw or Away)']}%`", unsafe_allow_html=True)

                with m_tab2:
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Totals Over/Under**<br>Over 1.5: `{calc['totals']['Over 1.5']}%`<br>Over 2.5: `{calc['totals']['Over 2.5']}%`<br>Under 3.5: `{calc['totals']['Under 3.5']}%`", unsafe_allow_html=True)
                    c2.markdown(f"**Both Teams to Score**<br>GG (Yes): `{calc['btts']['GG (Yes)']}%`<br>NG (No): `{calc['btts']['NG (No)']}%`", unsafe_allow_html=True)
                    c3.markdown(f"**xG Projections**<br>{h}: `{rep['xg']['home_xg']}` xG<br>{a}: `{rep['xg']['away_xg']}` xG", unsafe_allow_html=True)

                with m_tab3:
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**1st Half Over 0.5 Goals**<br>Probability: `{calc['ht_o05']}%`", unsafe_allow_html=True)
                    c2.markdown(f"**Top Correct Scorelines**<br>#1: `{calc['top_score'][0]}` ({calc['top_score'][1]}%)", unsafe_allow_html=True)

                with m_tab4:
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**Multi-Goal Ranges**<br>1-3 Goals: `{calc['multigoal']['1-3 Goals']}%`<br>2-4 Goals: `{calc['multigoal']['2-4 Goals']}%`", unsafe_allow_html=True)
                    c2.markdown(f"**Value Combo (Acca Leg)**<br>1X & Over 1.5: `{round(safe_val * calc['totals']['Over 1.5'] / 100, 1)}%`", unsafe_allow_html=True)

            st.write("")

    # --- MODE 2: CUSTOM MATCH SIMULATOR ---
    elif app_mode == "🔍 Custom Match Simulator":
        st.title("🔍 Custom Fixture Simulator")
        st.caption("Input any two football clubs to run instant predictions across all markets.")

        col_h, col_a = st.columns(2)
        with col_h:
            home_custom = st.text_input("Enter Home Team:", value="Arsenal")
        with col_a:
            away_custom = st.text_input("Enter Away Team:", value="Chelsea")

        if st.button("🚀 Analyze Fixture", type="primary"):
            with st.spinner(f"Computing odds for {home_custom} vs {away_custom}..."):
                rep = get_cached_prediction(home_custom, away_custom)
                calc = CompleteMarketCalculator.calculate(rep["xg"]["home_xg"], rep["xg"]["away_xg"], rep["1x2"])

            st.success("Analysis Complete!")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Recommended Winner", rep["1x2"]["Selection"])
            c2.metric("Over 2.5 Goals", f"{calc['totals']['Over 2.5']}%")
            c3.metric("BTTS (GG)", f"{calc['btts']['GG (Yes)']}%")
            c4.metric("Exact Score", calc["top_score"][0])

            st.write("### 📋 Full Probability Matrix")
            df_prob = pd.DataFrame({
                "Market Selection": [
                    "Home Win", "Draw", "Away Win", "1X Double Chance",
                    "Over 1.5 Goals", "Over 2.5 Goals", "Under 3.5 Goals",
                    "BTTS: Yes (GG)", "Multi-Goal (1-3)", "1H Over 0.5"
                ],
                "Calculated Probability": [
                    f"{rep['1x2']['Home Win']}%", f"{rep['1x2']['Draw']}%", f"{rep['1x2']['Away Win']}%",
                    f"{rep['double_chance']['1X (Home or Draw)']}%", f"{calc['totals']['Over 1.5']}%",
                    f"{calc['totals']['Over 2.5']}%", f"{calc['totals']['Under 3.5']}%",
                    f"{calc['btts']['GG (Yes)']}%", f"{calc['multigoal']['1-3 Goals']}%",
                    f"{calc['ht_o05']}%"
                ]
            })
            st.dataframe(df_prob, use_container_width=True)


if __name__ == "__main__":
    main()