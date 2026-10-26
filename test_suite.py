import unittest
import numpy as np
from core.database import init_db, get_connection
from core.adapters import TelegramTipsterAdapter
from core.prediction import DixonColesEngine, MarketPricingEngine
from core.backtesting import BacktestService

class TestPersonalBetEngine(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_dixon_coles_normalization(self):
        mat = DixonColesEngine.compute_distribution(1.70, 1.10)
        total_p = np.sum(mat)
        self.assertAlmostEqual(total_p, 1.0, places=5, msg="Dixon-Coles matrix must sum to 1.0")

    def test_de_vig_multiplicative(self):
        odds = [2.00, 3.40, 3.60]
        fair_probs, vig = MarketPricingEngine.de_vig_multiplicative(odds)
        self.assertAlmostEqual(sum(fair_probs), 1.0, places=5)
        self.assertGreater(vig, 0.0, "Vig must be positive")

    def test_expected_value_calculation(self):
        p_model = 0.60
        odds = 1.90
        ev = (p_model * odds) - 1.0
        self.assertAlmostEqual(ev, 0.14, places=2)

    def test_telegram_tip_fingerprint_dedup(self):
        fp1 = TelegramTipsterAdapter.compute_fingerprint("Arsenal", "Chelsea", "1X2", "Home Win")
        fp2 = TelegramTipsterAdapter.compute_fingerprint("  arsenal", "CHELSEA  ", "1x2", "home win")
        self.assertEqual(fp1, fp2, "Fingerprints must match after normalization")

    def test_backtest_metrics_integrity(self):
        metrics = BacktestService.compute_empirical_metrics()
        self.assertLess(metrics["overall_brier_score"], 0.25, "Brier score must outperform random baseline (0.25)")
        self.assertGreater(metrics["beat_clv_percentage"], 50.0, "CLV beat rate must exceed 50%")

if __name__ == '__main__':
    unittest.main()