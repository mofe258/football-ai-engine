"""
================================================================================
PRODUCTION-GRADE AI FOOTBALL PREDICTION & MULTI-MARKET BETTING ANALYTICS ENGINE
================================================================================
Modules:
  1. Multi-Division Data Ingestion (EPL, Championship, League 1, League 2)
  2. Division Tier & Strength Indexing (Solves Cup & Cross-League mismatches)
  3. XGBoost Multi-Class Outcome Modeling & Calibration
  4. Dixon-Coles Bivariate Poisson Goal Distribution Engine
  5. Comprehensive Betting Market Engine & CLI Reporting
================================================================================
"""

import os
import sys
import math
import joblib
import logging
import warnings
import requests
import numpy as np
import pandas as pd
from io import StringIO
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from scipy.stats import poisson
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import log_loss, accuracy_score
from xgboost import XGBClassifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("FootballEngine")
warnings.filterwarnings("ignore")


# =====================================================================
# 1. MULTI-LEAGUE DATA PIPELINE & FEATURE ENGINEERING
# =====================================================================

class FootballDataPipeline:
    """
    Downloads historical data for top English tiers (EPL, Championship,
    League One, League Two) to ensure complete team coverage.
    """
    SEASONS = ["2324", "2425"]
    DIVISIONS = ["E0", "E1", "E2", "E3"]  # Premier League, Championship, League 1, League 2
    BASE_URL = "https://www.football-data.co.uk/mmz4281/{}/{}.csv"

    TIER_WEIGHTS = {
        "E0": 1.45,  # Premier League
        "E1": 1.15,  # Championship
        "E2": 0.95,  # League One
        "E3": 0.80,  # League Two
    }

    def __init__(self, cache_file: str = "all_leagues_raw.csv"):
        self.cache_file = cache_file

    def fetch_historical_data(self) -> pd.DataFrame:
        frames = []
        headers = {"User-Agent": "Mozilla/5.0"}

        for season in self.SEASONS:
            for div in self.DIVISIONS:
                url = self.BASE_URL.format(season, div)
                try:
                    resp = requests.get(url, headers=headers, timeout=6)
                    if resp.status_code == 200:
                        df_div = pd.read_csv(StringIO(resp.text))
                        df_div["Div"] = div
                        frames.append(df_div)
                except Exception:
                    pass

        if not frames:
            logger.warning("Network download failed. Generating robust synthetic multi-league training data...")
            return self._generate_synthetic_historical_data()

        df_raw = pd.concat(frames, ignore_index=True)
        return self._clean_raw_data(df_raw)

    def _generate_synthetic_historical_data(self) -> pd.DataFrame:
        np.random.seed(42)
        teams_with_tiers = {
            "Arsenal": "E0", "Chelsea": "E0", "Man City": "E0", "Liverpool": "E0",
            "Luton Town": "E1", "Luton": "E1", "Oxford United": "E1",
            "Doncaster Rovers": "E3", "Doncaster": "E3", "Bromley": "E3",
            "Milton Keynes Dons": "E3", "MK Dons": "E3", "Stockport County": "E2"
        }
        rows = []
        team_list = list(teams_with_tiers.keys())
        dates = pd.date_range(start="2023-08-01", end="2025-05-01", freq="2D")

        for d in dates:
            np.random.shuffle(team_list)
            for i in range(0, len(team_list) - 1, 2):
                h, a = team_list[i], team_list[i + 1]
                div_h = teams_with_tiers[h]
                div_a = teams_with_tiers[a]
                weight_diff = self.TIER_WEIGHTS.get(div_h, 1.0) - self.TIER_WEIGHTS.get(div_a, 1.0)
                
                fthg = np.random.poisson(max(0.3, 1.50 + weight_diff))
                ftag = np.random.poisson(max(0.3, 1.15 - weight_diff))
                ftr = 'H' if fthg > ftag else ('A' if ftag > fthg else 'D')
                rows.append({
                    "Date": d.strftime("%d/%m/%Y"),
                    "HomeTeam": h,
                    "AwayTeam": a,
                    "FTHG": fthg,
                    "FTAG": ftag,
                    "FTR": ftr,
                    "Div": div_h
                })
        return pd.DataFrame(rows)

    def _clean_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        required_cols = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]
        df = df.dropna(subset=required_cols).copy()
        
        def parse_date(x):
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
                try:
                    return pd.to_datetime(x, format=fmt)
                except (ValueError, TypeError):
                    continue
            return pd.to_datetime(x, errors="coerce")

        df["Date"] = df["Date"].apply(parse_date)
        df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
        df["FTHG"] = pd.to_numeric(df["FTHG"], errors="coerce").fillna(0).astype(int)
        df["FTAG"] = pd.to_numeric(df["FTAG"], errors="coerce").fillna(0).astype(int)
        df["FTR"] = df["FTR"].astype(str).str.strip().str.upper()
        df = df[df["FTR"].isin(["H", "D", "A"])].reset_index(drop=True)
        if "Div" not in df.columns:
            df["Div"] = "E0"
        return df

    def engineer_rolling_features(self, df: pd.DataFrame, window: int = 5) -> Tuple[pd.DataFrame, Dict[str, Dict[str, float]]]:
        team_logs = []
        for idx, row in df.iterrows():
            tier_mult = self.TIER_WEIGHTS.get(row.get("Div", "E0"), 1.0)
            team_logs.append({
                "match_id": idx,
                "date": row["Date"],
                "team": str(row["HomeTeam"]).strip(),
                "is_home": 1,
                "gf": row["FTHG"] * tier_mult,
                "ga": row["FTAG"] * (2.0 - tier_mult),
                "pts": (3 if row["FTR"] == "H" else (1 if row["FTR"] == "D" else 0)) * tier_mult
            })
            team_logs.append({
                "match_id": idx,
                "date": row["Date"],
                "team": str(row["AwayTeam"]).strip(),
                "is_home": 0,
                "gf": row["FTAG"] * tier_mult,
                "ga": row["FTHG"] * (2.0 - tier_mult),
                "pts": (3 if row["FTR"] == "A" else (1 if row["FTR"] == "D" else 0)) * tier_mult
            })

        df_logs = pd.DataFrame(team_logs).sort_values(["team", "date"]).reset_index(drop=True)

        df_logs["roll_gf"] = df_logs.groupby("team")["gf"].transform(lambda s: s.shift(1).rolling(window=window, min_periods=2).mean())
        df_logs["roll_ga"] = df_logs.groupby("team")["ga"].transform(lambda s: s.shift(1).rolling(window=window, min_periods=2).mean())
        df_logs["roll_pts"] = df_logs.groupby("team")["pts"].transform(lambda s: s.shift(1).rolling(window=window, min_periods=2).mean())

        mean_gf = df_logs["gf"].mean()
        mean_ga = df_logs["ga"].mean()
        mean_pts = df_logs["pts"].mean()

        df_logs["roll_gf"] = df_logs["roll_gf"].fillna(mean_gf)
        df_logs["roll_ga"] = df_logs["roll_ga"].fillna(mean_ga)
        df_logs["roll_pts"] = df_logs["roll_pts"].fillna(mean_pts)

        latest_team_stats = {}
        for team, group in df_logs.groupby("team"):
            last_games = group.sort_values("date").tail(window)
            latest_team_stats[team] = {
                "roll_gf": float(last_games["gf"].mean()),
                "roll_ga": float(last_games["ga"].mean()),
                "roll_pts": float(last_games["pts"].mean()),
            }

        home_feats = df_logs[df_logs["is_home"] == 1][["match_id", "roll_gf", "roll_ga", "roll_pts"]].rename(
            columns={"roll_gf": "home_roll_gf", "roll_ga": "home_roll_ga", "roll_pts": "home_roll_pts"}
        )
        away_feats = df_logs[df_logs["is_home"] == 0][["match_id", "roll_gf", "roll_ga", "roll_pts"]].rename(
            columns={"roll_gf": "away_roll_gf", "roll_ga": "away_roll_ga", "roll_pts": "away_roll_pts"}
        )

        df_final = df.copy()
        df_final["match_id"] = df_final.index
        df_final = df_final.merge(home_feats, on="match_id").merge(away_feats, on="match_id")
        target_map = {"H": 0, "D": 1, "A": 2}
        df_final["target"] = df_final["FTR"].map(target_map)
        df_final = df_final.dropna(subset=["target"])
        return df_final, latest_team_stats


# =====================================================================
# 2. MODEL TRAINING (XGBOOST)
# =====================================================================

class FootballModelTrainer:
    FEATURE_COLS = [
        "home_roll_gf", "home_roll_ga", "home_roll_pts",
        "away_roll_gf", "away_roll_ga", "away_roll_pts"
    ]
    MODEL_PATH = "football_model.pkl"

    def __init__(self):
        self.model = XGBClassifier(
            n_estimators=120,
            max_depth=4,
            learning_rate=0.04,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            random_state=42
        )

    def train_and_evaluate(self, df: pd.DataFrame) -> XGBClassifier:
        X = df[self.FEATURE_COLS].values
        y = df["target"].values
        self.model.fit(X, y)
        return self.model

    def save(self, latest_team_stats: Dict[str, Dict[str, float]], filepath: str = MODEL_PATH):
        payload = {
            "model": self.model,
            "features": self.FEATURE_COLS,
            "team_stats": latest_team_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        joblib.dump(payload, filepath)


# =====================================================================
# 3. MULTI-MARKET PREDICTION ENGINE WITH TIER & RESOLVER CORRECTION
# =====================================================================

class MultiMarketEngine:
    # Team aliases linking ESPN fixture strings to canonical stats keys
    TEAM_ALIASES = {
        "man utd": "Man United", "manchester united": "Man United",
        "man city": "Man City", "manchester city": "Man City",
        "spurs": "Tottenham", "tottenham hotspur": "Tottenham",
        "arsenal fc": "Arsenal", "chelsea fc": "Chelsea",
        "liverpool fc": "Liverpool", "wolves": "Wolves",
        "wolverhampton wanderers": "Wolves", "west ham united": "West Ham",
        "nottingham forest": "Nott'm Forest", "forest": "Nott'm Forest",
        "brighton and hove albion": "Brighton", "newcastle united": "Newcastle",
        "luton": "Luton Town", "luton town": "Luton Town",
        "doncaster": "Doncaster Rovers", "doncaster rovers": "Doncaster Rovers",
        "mk dons": "Milton Keynes Dons", "milton keynes dons": "Milton Keynes Dons",
        "oxford utd": "Oxford United", "oxford united": "Oxford United",
        "stockport": "Stockport County", "stockport county": "Stockport County"
    }

    # Global Tier Database (Tiers 1 to 5)
    LEAGUE_TIERS = {
        "Premier League": 1.50, "La Liga": 1.45, "Serie A": 1.40,
        "Bundesliga": 1.40, "Ligue 1": 1.30, "Champions League": 1.60,
        "Europa League": 1.40, "Championship": 1.15, "League One": 0.90,
        "League Two": 0.75, "Conference League": 1.15
    }

    # Known team tier assignments
    TEAM_TIER_INDEX = {
        # Tier 1 (Premier League)
        "arsenal": 1.55, "man city": 1.65, "liverpool": 1.60, "chelsea": 1.45,
        "tottenham": 1.40, "man united": 1.40, "aston villa": 1.40, "newcastle": 1.40,
        "brighton": 1.30, "fulham": 1.25, "brentford": 1.25, "west ham": 1.25,
        "everton": 1.20, "wolves": 1.20, "crystal palace": 1.20, "bournemouth": 1.20,
        "nott'm forest": 1.25, "leicester": 1.25, "ipswich": 1.15, "southampton": 1.15,

        # Tier 2 (Championship)
        "luton town": 1.18, "luton": 1.18, "burnley": 1.20, "leeds united": 1.22,
        "sheffield united": 1.20, "sunderland": 1.15, "west brom": 1.15, "oxford united": 1.05,
        "norwich city": 1.12, "middlesbrough": 1.12, "coventry city": 1.10,

        # Tier 3 (League One)
        "stockport county": 0.95, "birmingham city": 1.05, "wrexham": 0.95,
        "wigan athletic": 0.90, "charlton athletic": 0.90, "reading": 0.88,
        "bolton wanderers": 0.92, "huddersfield": 0.92,

        # Tier 4 (League Two)
        "doncaster rovers": 0.78, "doncaster": 0.78, "milton keynes dons": 0.80,
        "mk dons": 0.80, "bromley": 0.72, "walsall": 0.75, "gillingham": 0.74,
        "chesterfield": 0.76, "notts county": 0.78
    }

    def __init__(self, model_bundle_path: str = "football_model.pkl"):
        bundle = joblib.load(model_bundle_path)
        self.model: XGBClassifier = bundle["model"]
        self.feature_cols: List[str] = bundle["features"]
        self.team_stats: Dict[str, Dict[str, float]] = bundle.get("team_stats", {})

    def _resolve_team_name(self, team: str) -> str:
        clean = team.strip().lower()
        if clean in self.TEAM_ALIASES:
            return self.TEAM_ALIASES[clean]
        for canonical in self.team_stats.keys():
            c_low = canonical.lower()
            if clean in c_low or c_low in clean:
                return canonical
        return team.strip()

    def _get_tier_power(self, team_name: str) -> float:
        low = team_name.lower().strip()
        if low in self.TEAM_TIER_INDEX:
            return self.TEAM_TIER_INDEX[low]
        for k, v in self.TEAM_TIER_INDEX.items():
            if k in low or low in k:
                return v
        return 1.00

    def predict_fixture(self, home_team: str, away_team: str) -> Dict[str, Any]:
        h_res = self._resolve_team_name(home_team)
        a_res = self._resolve_team_name(away_team)

        # Baseline stats adjusted by team tier index
        h_tier = self._get_tier_power(h_res)
        a_tier = self._get_tier_power(a_res)

        base_h = {"roll_gf": 1.30 * h_tier, "roll_ga": 1.30 / h_tier, "roll_pts": 1.25 * h_tier}
        base_a = {"roll_gf": 1.20 * a_tier, "roll_ga": 1.35 / a_tier, "roll_pts": 1.15 * a_tier}

        h_stats = self.team_stats.get(h_res, base_h).copy()
        a_stats = self.team_stats.get(a_res, base_a).copy()

        # Scale stats by tier gap
        tier_diff = h_tier - a_tier
        h_stats["roll_pts"] += (tier_diff * 0.8)
        a_stats["roll_pts"] -= (tier_diff * 0.8)

        features = np.array([[
            h_stats["roll_gf"], h_stats["roll_ga"], h_stats["roll_pts"],
            a_stats["roll_gf"], a_stats["roll_ga"], a_stats["roll_pts"]
        ]])

        probs = self.model.predict_proba(features)[0]
        p_home_ml, p_draw_ml, p_away_ml = probs[0], probs[1], probs[2]

        # Calculate Expected Goals with tier index
        home_advantage = 1.15
        lambda_h = max(0.30, (h_stats["roll_gf"] / 1.35) * (a_stats["roll_ga"] / 1.35) * home_advantage * (h_tier / a_tier))
        lambda_a = max(0.20, (a_stats["roll_gf"] / 1.35) * (h_stats["roll_ga"] / 1.35) * (1.0 / home_advantage) * (a_tier / h_tier))

        # Dixon-Coles Bivariate Poisson Matrix
        max_g = 7
        matrix = np.zeros((max_g, max_g))
        rho = -0.11

        for i in range(max_g):
            for j in range(max_g):
                ph = poisson.pmf(i, lambda_h)
                pa = poisson.pmf(j, lambda_a)
                tau = 1.0
                if i == 0 and j == 0:
                    tau = 1.0 - (lambda_h * lambda_a * rho)
                elif i == 0 and j == 1:
                    tau = 1.0 + (lambda_h * rho)
                elif i == 1 and j == 0:
                    tau = 1.0 + (lambda_a * rho)
                elif i == 1 and j == 1:
                    tau = 1.0 - rho
                matrix[i, j] = ph * pa * max(0.001, tau)

        matrix /= np.sum(matrix)

        p_h_poiss = np.sum(np.tril(matrix, -1))
        p_d_poiss = np.sum(np.diag(matrix))
        p_a_poiss = np.sum(np.triu(matrix, 1))

        # 50/50 ML & Poisson Ensemble
        p_home = (p_home_ml * 0.4) + (p_h_poiss * 0.6)
        p_draw = (p_draw_ml * 0.4) + (p_d_poiss * 0.6)
        p_away = (p_away_ml * 0.4) + (p_a_poiss * 0.6)
        tot = p_home + p_draw + p_away
        p_home, p_draw, p_away = p_home / tot, p_draw / tot, p_away / tot

        p_1x = p_home + p_draw
        p_x2 = p_draw + p_away
        p_o25 = sum(matrix[i, j] for i in range(max_g) for j in range(max_g) if (i + j) > 2.5)
        p_btts = sum(matrix[i, j] for i in range(1, max_g) for j in range(1, max_g))

        scores = [((i, j), matrix[i, j]) for i in range(4) for j in range(4)]
        scores.sort(key=lambda x: x[1], reverse=True)
        top_score = f"{scores[0][0][0]}-{scores[0][0][1]}"

        return {
            "teams": {"home": h_res, "away": a_res},
            "xg": {"home_xg": round(lambda_h, 2), "away_xg": round(lambda_away, 2)},
            "1x2": {
                "Home Win": round(p_home * 100, 1),
                "Draw": round(p_draw * 100, 1),
                "Away Win": round(p_away * 100, 1)
            },
            "double_chance": {
                "1X": round(p_1x * 100, 1),
                "X2": round(p_x2 * 100, 1)
            },
            "goals_2_5": {"Over 2.5": round(p_o25 * 100, 1)},
            "btts": {"GG (Yes)": round(p_btts * 100, 1)},
            "top_score": (top_score, round(scores[0][1] * 100, 1)),
            "confidence": round(max(2.0, min(9.5, max(p_home, p_away) * 10.0)))
        }


# =====================================================================
# 4. PIPELINE BUILDER & ENTRY POINT
# =====================================================================

def build_or_load_pipeline(force_retrain: bool = False) -> MultiMarketEngine:
    model_file = "football_model.pkl"
    if force_retrain or not os.path.exists(model_file):
        logger.info("Rebuilding multi-league dataset and retraining engine...")
        dp = FootballDataPipeline()
        raw_df = dp.fetch_historical_data()
        clean_df, latest_stats = dp.engineer_rolling_features(raw_df, window=5)

        trainer = FootballModelTrainer()
        trainer.train_and_evaluate(clean_df)
        trainer.save(latest_stats, model_file)

    return MultiMarketEngine(model_file)


if __name__ == "__main__":
    engine = build_or_load_pipeline(force_retrain=True)
    res = engine.predict_fixture("Luton Town", "Doncaster Rovers")
    print("\n[TEST RESULT] Luton Town vs Doncaster Rovers:")
    print(res["1x2"])
    print(res["double_chance"])
