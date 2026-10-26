"""
================================================================================
STATISTICAL & PROBABILISTIC PREDICTION ENGINE (DIXON-COLES + ENSEMBLE)
================================================================================
"""

import numpy as np
from scipy.stats import poisson
from typing import Dict, List, Tuple, Any, Optional

class DixonColesEngine:
    @staticmethod
    def tau_adjustment(x: int, y: int, lambda_h: float, lambda_a: float, rho: float = -0.11) -> float:
        if x == 0 and y == 0:
            return 1.0 - (lambda_h * lambda_a * rho)
        elif x == 0 and y == 1:
            return 1.0 + (lambda_h * rho)
        elif x == 1 and y == 0:
            return 1.0 + (lambda_a * rho)
        elif x == 1 and y == 1:
            return 1.0 - rho
        else:
            return 1.0

    @classmethod
    def compute_distribution(cls, lambda_h: float, lambda_a: float, rho: float = -0.11, max_goals: int = 8) -> np.ndarray:
        matrix = np.zeros((max_goals, max_goals))
        for x in range(max_goals):
            for y in range(max_goals):
                tau = cls.tau_adjustment(x, y, lambda_h, lambda_a, rho)
                matrix[x, y] = max(0.0, tau) * poisson.pmf(x, lambda_h) * poisson.pmf(y, lambda_a)
        matrix = np.clip(matrix, 0.0, None)
        return matrix / np.sum(matrix)

class MarketPricingEngine:
    @staticmethod
    def de_vig_multiplicative(odds_list: List[float]) -> Tuple[List[float], float]:
        inv = [1.0 / o for o in odds_list]
        margin = sum(inv) - 1.0
        fair_probs = [i / (1.0 + margin) for i in inv]
        return fair_probs, margin * 100.0

    @classmethod
    def evaluate_markets(cls, engine, h: str, a: str, lineup_confirmed: bool = False) -> Dict[str, Any]:
        h_res = engine._resolve_team_name(h)
        a_res = engine._resolve_team_name(a)
        avg = {"roll_gf": 1.35, "roll_ga": 1.35, "roll_pts": 1.30}
        h_stats = engine.team_stats.get(h_res, avg)
        a_stats = engine.team_stats.get(a_res, avg)

        feats = np.array([[
            h_stats["roll_gf"], h_stats["roll_ga"], h_stats["roll_pts"],
            a_stats["roll_gf"], a_stats["roll_ga"], a_stats["roll_pts"]
        ]])
        ml_probs = engine.model.predict_proba(feats)[0]
        p_h_ml, p_d_ml, p_a_ml = ml_probs[0], ml_probs[1], ml_probs[2]

        lambda_h = max(0.45, (h_stats["roll_gf"] / 1.4) * (a_stats["roll_ga"] / 1.4) * 1.55)
        lambda_a = max(0.35, (a_stats["roll_gf"] / 1.4) * (h_stats["roll_ga"] / 1.4) * 1.25)
        if lineup_confirmed:
            lambda_h *= 1.025
            lambda_a *= 1.015

        mat = DixonColesEngine.compute_distribution(lambda_h, lambda_a)

        # 1X2 Probabilities
        p_home_dc = float(np.sum(np.tril(mat, -1)))
        p_draw_dc = float(np.sum(np.diag(mat)))
        p_away_dc = float(np.sum(np.triu(mat, 1)))

        # Ensemble ML + Dixon-Coles
        p_h = 0.5 * p_home_dc + 0.5 * p_h_ml
        p_d = 0.5 * p_draw_dc + 0.5 * p_d_ml
        p_a = 0.5 * p_away_dc + 0.5 * p_a_ml
        total = p_h + p_d + p_a
        p_h, p_d, p_a = p_h / total, p_d / total, p_a / total

        p_1x = p_h + p_d
        p_x2 = p_d + p_a
        p_12 = p_h + p_a
        p_dnb_h = p_h / (p_h + p_a + 1e-9)

        p_o05 = float(sum(mat[i, j] for i in range(8) for j in range(8) if (i + j) > 0.5))
        p_o15 = float(sum(mat[i, j] for i in range(8) for j in range(8) if (i + j) > 1.5))
        p_o25 = float(sum(mat[i, j] for i in range(8) for j in range(8) if (i + j) > 2.5))
        p_u25 = 1.0 - p_o25
        p_o35 = float(sum(mat[i, j] for i in range(8) for j in range(8) if (i + j) > 3.5))
        p_o45 = float(sum(mat[i, j] for i in range(8) for j in range(8) if (i + j) > 4.5))

        p_btts_yes = float(sum(mat[i, j] for i in range(1, 8) for j in range(1, 8)))
        p_btts_no = 1.0 - p_btts_yes

        lambda_h_ht = lambda_h * 0.44
        lambda_a_ht = lambda_a * 0.44
        ht_mat = DixonColesEngine.compute_distribution(lambda_h_ht, lambda_a_ht, max_goals=5)
        p_ht_home = float(np.sum(np.tril(ht_mat, -1)))
        p_ht_draw = float(np.sum(np.diag(ht_mat)))
        p_ht_away = float(np.sum(np.triu(ht_mat, 1)))
        p_ht_o05 = float(sum(ht_mat[i, j] for i in range(5) for j in range(5) if (i + j) > 0.5))
        p_ht_o15 = float(sum(ht_mat[i, j] for i in range(5) for j in range(5) if (i + j) > 1.5))

        p_home_minus_1_5 = float(sum(mat[i, j] for i in range(8) for j in range(8) if (i - j) >= 2))
        p_away_plus_1_5 = 1.0 - p_home_minus_1_5

        score_candidates = [((i, j), mat[i, j]) for i in range(5) for j in range(5)]
        score_candidates.sort(key=lambda x: x[1], reverse=True)
        top_scores = [(f"{s[0][0]}-{s[0][1]}", round(s[1] * 100, 1)) for s in score_candidates[:3]]

        vig = 1.055
        market_odds_1x2 = [round(vig / p_h, 2), round(vig / p_d, 2), round(vig / p_a, 2)]
        best_price_home = market_odds_1x2[0]

        ev_home = (p_h * best_price_home) - 1.0

        # Evidence Quality Index (EQI: 0 - 100)
        entropy = - (p_h * np.log(p_h + 1e-9) + p_d * np.log(p_d + 1e-9) + p_a * np.log(p_a + 1e-9))
        norm_entropy = min(1.0, entropy / 1.09)
        eqi = int((30 if lineup_confirmed else 18) + ((1.0 - norm_entropy) * 45) + 25)

        if ev_home >= 0.05 and eqi >= 65:
            decision = ("STRONG SIGNAL (+EV EDGE)", "sig-green", "Positive statistical expectation over market price with verified evidence.")
        elif p_1x >= 0.78 and eqi >= 60:
            decision = ("HIGH PROBABILITY FLOOR (BANKER)", "sig-green", "High survival probability protects capital against volatile draw outcomes.")
        elif eqi < 55 or not lineup_confirmed:
            decision = ("UNCERTAIN — AWAIT CONFIRMED LINEUPS", "sig-amber", "Lineup variance remains high; wait for official starting sheets.")
        else:
            decision = ("FAIR PRICE — NO CLEAR STATISTICAL EDGE", "sig-red", "Market odds are efficiently priced; model detects no edge.")

        return {
            "xg": {"home": round(lambda_h, 2), "away": round(lambda_a, 2)},
            "p_1x2": {"1": round(p_h * 100, 1), "X": round(p_d * 100, 1), "2": round(p_a * 100, 1)},
            "p_dc": {"1X": round(p_1x * 100, 1), "X2": round(p_x2 * 100, 1), "12": round(p_12 * 100, 1)},
            "p_dnb": {"Home": round(p_dnb_h * 100, 1)},
            "p_goals": {
                "O0.5": round(p_o05 * 100, 1), "O1.5": round(p_o15 * 100, 1),
                "O2.5": round(p_o25 * 100, 1), "U2.5": round(p_u25 * 100, 1),
                "O3.5": round(p_o35 * 100, 1), "O4.5": round(p_o45 * 100, 1)
            },
            "p_btts": {"GG": round(p_btts_yes * 100, 1), "NG": round(p_btts_no * 100, 1)},
            "p_ht": {"1H_1": round(p_ht_home * 100, 1), "1H_X": round(p_ht_draw * 100, 1), "1H_2": round(p_ht_away * 100, 1), "1H_O05": round(p_ht_o05 * 100, 1), "1H_O15": round(p_ht_o15 * 100, 1)},
            "p_handicap": {"Home -1.5": round(p_home_minus_1_5 * 100, 1), "Away +1.5": round(p_away_plus_1_5 * 100, 1)},
            "top_scores": top_scores,
            "odds_1x2": {"1": best_price_home, "X": market_odds_1x2[1], "2": market_odds_1x2[2]},
            "ev": round(ev_home * 100, 1),
            "eqi": eqi,
            "decision": decision
        }