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
from concurrent.futures import ThreadPoolExecutor

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
    @staticmethod
    def compute_fingerprint(home: str, away: str, market: str, selection: str) -> str:
        raw = f"{home.lower().strip()}_{away.lower().strip()}_{market.lower().strip()}_{selection.lower().strip()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @classmethod
    def parse_raw_message(cls, text: str, source_id: str) -> Optional[Dict[str, Any]]:
        cleaned = re.sub(r"[<>{}\\\\]", "", text).strip()
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
        ("uefa.europa", "Europa League"), ("uefa.europa.conf", "Conference League"),
        ("eng.2", "Championship"), ("eng.3", "League One"), ("eng.4", "League Two"),
        ("esp.2", "La Liga 2"), ("ita.2", "Serie B"), ("ger.2", "2. Bundesliga"),
        ("fra.2", "Ligue 2"), ("por.1", "Primeira Liga"), ("ned.1", "Eredivisie"),
        ("tur.1", "Süper Lig"), ("sco.1", "Scottish Premiership"), ("sau.1", "Saudi Pro League"),
        ("usa.1", "MLS"), ("bra.1", "Brasileirão"), ("arg.1", "Argentine Primera")
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
    def _fetch_single_league(cls, league_tuple: Tuple[str, str]) -> List[Dict[str, Any]]:
        code, name = league_tuple
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
        headers = {"User-Agent": "Mozilla/5.0"}
        found = []
        try:
            res = requests.get(url, headers=headers, timeout=3.0)
            if res.status_code == 200:
                for ev in res.json().get("events", []):
                    status_state = ev.get("status", {}).get("type", {}).get("state", "")
                    if status_state in ["pre", "in"]:
                        comps = ev.get("competitions", [{}])[0]
                        competitors = comps.get("competitors", [])
                        venue_name = comps.get("venue", {}).get("fullName", "Official Stadium")
                        h, a = None, None
                        for c in competitors:
                            tname = cls.normalize_team(c.get("team", {}).get("displayName") or c.get("team", {}).get("name") or "")
                            if c.get("homeAway") == "home":
                                h = tname
                            else:
                                a = tname
                        raw_date = ev.get("date", "")
                        kickoff = raw_date
                        match_date_str = ""
                        try:
                            dt = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M%z")
                            kickoff = dt.strftime("%A, %b %d @ %H:%M UTC")
                            match_date_str = dt.strftime("%Y-%m-%d")
                        except Exception:
                            pass
                        if h and a:
                            found.append({
                                "canonical_id": hashlib.md5(f"{h}_{a}_{raw_date}".encode()).hexdigest()[:12],
                                "home": h,
                                "away": a,
                                "comp": name,
                                "kickoff": kickoff,
                                "match_date": match_date_str,
                                "status": "Live" if status_state == "in" else "Scheduled",
                                "lineup_status": "Confirmed Starting XI" if status_state == "in" else "Projected Lineup",
                                "venue": venue_name,
                                "last_refresh": datetime.utcnow().strftime("%H:%M:%S UTC")
                            })
        except Exception:
            pass
        return found

    @classmethod
    def get_canonical_schedule(cls) -> Dict[str, List[Dict[str, Any]]]:
        grouped = {"Today": [], "Tomorrow": [], "Upcoming": []}
        now = datetime.utcnow()
        today_str = now.strftime("%Y-%m-%d")
        tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(cls._fetch_single_league, l_tuple)
                for l_tuple in cls.LEAGUE_REGISTRY
            ]
            all_real_matches = []
            for f in futures:
                for m in f.result():
                    if not any(x["canonical_id"] == m["canonical_id"] for x in all_real_matches):
                        all_real_matches.append(m)

        for m in all_real_matches:
            m_date = m.get("match_date", "")
            if m_date == today_str:
                grouped["Today"].append(m)
            elif m_date == tomorrow_str:
                grouped["Tomorrow"].append(m)
            else:
                grouped["Upcoming"].append(m)

        return grouped
