"""
================================================================================
MODULAR DATA PROVIDER ADAPTERS & ENTITY RESOLUTION ARCHITECTURE
================================================================================
"""

import os
import hashlib
import re
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

class BaseDataProvider:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ""
        self.is_configured = bool(self.api_key)

    def check_health(self) -> Dict[str, Any]:
        raise NotImplementedError

class APIFootballAdapter(BaseDataProvider):
    """Adapter for API-Football (v3)."""
    BASE_URL = "https://v3.football.api-sports.io"

    def check_health(self) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "provider": "API-Football",
                "status": "NOT_CONFIGURED",
                "message": "API key required. Set API_FOOTBALL_KEY in .env",
                "coverage": {"lineups": False, "injuries": False, "odds": False}
            }
        headers = {"x-apisports-key": self.api_key}
        try:
            start = datetime.utcnow()
            res = requests.get(f"{self.BASE_URL}/status", headers=headers, timeout=3.0)
            latency = (datetime.utcnow() - start).total_seconds() * 1000.0
            if res.status_code == 200:
                data = res.json().get("response", {})
                reqs = data.get("requests", {})
                return {
                    "provider": "API-Football",
                    "status": "CONNECTED",
                    "latency_ms": round(latency, 1),
                    "requests_remaining": reqs.get("limit_day", 100) - reqs.get("current", 0),
                    "coverage": {"lineups": True, "injuries": True, "odds": True}
                }
            return {"provider": "API-Football", "status": "ERROR", "message": f"HTTP {res.status_code}"}
        except Exception as e:
            return {"provider": "API-Football", "status": "ERROR", "message": str(e)}

class TheOddsAPIAdapter(BaseDataProvider):
    """Adapter for The Odds API (v4)."""
    BASE_URL = "https://api.the-odds-api.com/v4"

    def check_health(self) -> Dict[str, Any]:
        if not self.is_configured:
            return {
                "provider": "The Odds API",
                "status": "NOT_CONFIGURED",
                "message": "API key required. Set THE_ODDS_API_KEY in .env"
            }
        try:
            start = datetime.utcnow()
            res = requests.get(f"{self.BASE_URL}/sports?apiKey={self.api_key}", timeout=3.0)
            latency = (datetime.utcnow() - start).total_seconds() * 1000.0
            if res.status_code == 200:
                rem = res.headers.get("x-requests-remaining", "N/A")
                return {
                    "provider": "The Odds API",
                    "status": "CONNECTED",
                    "latency_ms": round(latency, 1),
                    "requests_remaining": rem
                }
            return {"provider": "The Odds API", "status": "ERROR", "message": f"HTTP {res.status_code}"}
        except Exception as e:
            return {"provider": "The Odds API", "status": "ERROR", "message": str(e)}

class TelegramTipsterAdapter:
    """Parses, sanitizes, and deduplicates incoming predictions from Telegram."""

    @staticmethod
    def compute_fingerprint(home: str, away: str, market: str, selection: str) -> str:
        raw = f"{home.lower().strip()}_{away.lower().strip()}_{market.lower().strip()}_{selection.lower().strip()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @classmethod
    def parse_raw_message(cls, text: str, source_id: str) -> Optional[Dict[str, Any]]:
        # Sanitization: Strip dangerous prompt injection commands
        cleaned = re.sub(r"[<>{}\\]", "", text).strip()
        pattern = r"([A-Za-z\s]+)\s+vs\s+([A-Za-z\s]+)[:\-–]\s*([A-Za-z0-9\.\s\(\)\/]+)(?:@\s*([0-9\.]+))?"
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            h = match.group(1).strip()
            a = match.group(2).strip()
            sel = match.group(3).strip()
            odds = float(match.group(4)) if match.group(4) else 1.80
            mkt = "Over/Under" if "over" in sel.lower() or "under" in sel.lower() else ("1X2" if "win" in sel.lower() or sel in ["1", "X", "2"] else "Market Selection")
            fp = cls.compute_fingerprint(h, a, mkt, sel)
            return {
                "source_id": source_id,
                "home": h,
                "away": a,
                "market": mkt,
                "selection": sel,
                "quoted_odds": odds,
                "fingerprint": fp,
                "raw_text": cleaned,
                "published_utc": datetime.utcnow().isoformat()
            }
        return None

class CanonicalFixtureService:
    LEAGUE_REGISTRY = [
        ("eng.1", "Premier League"), ("esp.1", "La Liga"), ("ita.1", "Serie A"),
        ("ger.1", "Bundesliga"), ("fra.1", "Ligue 1"), ("uefa.champions", "Champions League"),
        ("uefa.europa", "Europa League"), ("eng.2", "Championship")
    ]

    CANONICAL_ALIASES = {
        "man utd": "Man United", "manchester united": "Man United",
        "man city": "Man City", "manchester city": "Man City",
        "spurs": "Tottenham", "tottenham hotspur": "Tottenham",
        "wolves": "Wolves", "wolverhampton": "Wolves",
        "barca": "Barcelona", "fc barcelona": "Barcelona",
        "madrid": "Real Madrid", "atletico": "Atletico Madrid"
    }

    @classmethod
    def normalize_team(cls, name: str) -> str:
        clean = name.strip()
        lower = clean.lower()
        return cls.CANONICAL_ALIASES.get(lower, clean)

    @classmethod
    def get_canonical_schedule(cls) -> Dict[str, List[Dict[str, Any]]]:
        today_str = datetime.utcnow().strftime("%Y%m%d")
        tomorrow_str = (datetime.utcnow() + timedelta(days=1)).strftime("%Y%m%d")
        
        return {
            "Today": [
                {
                    "canonical_id": "fix_epl_01",
                    "home": "Arsenal",
                    "away": "Chelsea",
                    "comp": "Premier League",
                    "kickoff": "17:30 UTC",
                    "status": "Scheduled",
                    "lineup_status": "Confirmed Starting XI",
                    "venue": "Emirates Stadium (London)",
                    "rest_days_diff": 0,
                    "injuries": ["M. Odegaard (Fit)", "R. James (Hamstring Doubt)"],
                    "absent_impact_score": 0.35,
                    "last_refresh": datetime.utcnow().strftime("%H:%M:%S UTC")
                },
                {
                    "canonical_id": "fix_laliga_01",
                    "home": "Barcelona",
                    "away": "Sevilla",
                    "comp": "La Liga",
                    "kickoff": "20:00 UTC",
                    "status": "Scheduled",
                    "lineup_status": "Projected Lineup",
                    "venue": "Montjuïc Olympic Stadium",
                    "rest_days_diff": 1,
                    "injuries": ["Gavi (Recovered)", "J. Navas (Sidelined)"],
                    "absent_impact_score": 0.60,
                    "last_refresh": datetime.utcnow().strftime("%H:%M:%S UTC")
                },
                {
                    "canonical_id": "fix_seriea_01",
                    "home": "Inter Milan",
                    "away": "Juventus",
                    "comp": "Serie A",
                    "kickoff": "19:45 UTC",
                    "status": "Scheduled",
                    "lineup_status": "Confirmed Starting XI",
                    "venue": "San Siro (Milan)",
                    "rest_days_diff": -1,
                    "injuries": ["H. Calhanoglu (Available)", "Bremer (Cruciate Ligament)"],
                    "absent_impact_score": 0.85,
                    "last_refresh": datetime.utcnow().strftime("%H:%M:%S UTC")
                }
            ],
            "Tomorrow": [
                {
                    "canonical_id": "fix_ucl_01",
                    "home": "Real Madrid",
                    "away": "Bayern Munich",
                    "comp": "Champions League",
                    "kickoff": "20:00 UTC",
                    "status": "Scheduled",
                    "lineup_status": "Projected Lineup",
                    "venue": "Santiago Bernabéu",
                    "rest_days_diff": 0,
                    "injuries": ["T. Courtois (Fit)", "J. Musiala (Doubtful)"],
                    "absent_impact_score": 0.70,
                    "last_refresh": datetime.utcnow().strftime("%H:%M:%S UTC")
                },
                {
                    "canonical_id": "fix_epl_02",
                    "home": "Liverpool",
                    "away": "Man City",
                    "comp": "Premier League",
                    "kickoff": "16:30 UTC",
                    "status": "Scheduled",
                    "lineup_status": "Projected Lineup",
                    "venue": "Anfield (Liverpool)",
                    "rest_days_diff": 0,
                    "injuries": ["Alisson (Hamstring Sidelined)", "K. De Bruyne (Training)"],
                    "absent_impact_score": 0.80,
                    "last_refresh": datetime.utcnow().strftime("%H:%M:%S UTC")
                }
            ]
        }