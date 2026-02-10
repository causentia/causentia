"""
CAUSENTIA Backend API v1.0
Sovereign Crisis Early Warning System — Real Data Engine

Data Sources (All Open & Free):
1. World Bank API — GDP growth, inflation, debt/GDP, reserves
2. IMF WEO — Forecasts, fiscal indicators
3. FRED (Federal Reserve) — Exchange rates, spreads, US Treasury yields
4. GDELT — News sentiment & event monitoring
5. UN COMTRADE — Trade fragmentation (via proxy)
6. ACLED — Conflict events data

Author: Mohamed Ibrahim
License: MIT
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import asyncio
import json
import math
import time
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from pathlib import Path

# AI API Keys
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

app = FastAPI(
    title="CAUSENTIA API",
    description="Sovereign Crisis Early Warning System — Real Data Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════

CACHE_DIR = Path("/tmp/causentia_cache")
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL = 3600 * 6  # 6 hours

# Country mappings: ISO2 -> ISO3 (World Bank uses ISO3)
COUNTRIES = {
    "VE": {"iso3": "VEN", "name": "Venezuela", "flag": "🇻🇪", "region": "LAC"},
    "LB": {"iso3": "LBN", "name": "Lebanon", "flag": "🇱🇧", "region": "MENA"},
    "AR": {"iso3": "ARG", "name": "Argentina", "flag": "🇦🇷", "region": "LAC"},
    "ZW": {"iso3": "ZWE", "name": "Zimbabwe", "flag": "🇿🇼", "region": "SSA"},
    "TR": {"iso3": "TUR", "name": "Turkey", "flag": "🇹🇷", "region": "MENA"},
    "SD": {"iso3": "SDN", "name": "Sudan", "flag": "🇸🇩", "region": "SSA"},
    "SY": {"iso3": "SYR", "name": "Syria", "flag": "🇸🇾", "region": "MENA"},
    "PK": {"iso3": "PAK", "name": "Pakistan", "flag": "🇵🇰", "region": "SA"},
    "ET": {"iso3": "ETH", "name": "Ethiopia", "flag": "🇪🇹", "region": "SSA"},
    "NG": {"iso3": "NGA", "name": "Nigeria", "flag": "🇳🇬", "region": "SSA"},
    "IR": {"iso3": "IRN", "name": "Iran", "flag": "🇮🇷", "region": "MENA"},
    "EG": {"iso3": "EGY", "name": "Egypt", "flag": "🇪🇬", "region": "MENA"},
    "GH": {"iso3": "GHA", "name": "Ghana", "flag": "🇬🇭", "region": "SSA"},
    "KE": {"iso3": "KEN", "name": "Kenya", "flag": "🇰🇪", "region": "SSA"},
    "RU": {"iso3": "RUS", "name": "Russia", "flag": "🇷🇺", "region": "ECA"},
    "BD": {"iso3": "BGD", "name": "Bangladesh", "flag": "🇧🇩", "region": "SA"},
    "TN": {"iso3": "TUN", "name": "Tunisia", "flag": "🇹🇳", "region": "MENA"},
    "ZA": {"iso3": "ZAF", "name": "South Africa", "flag": "🇿🇦", "region": "SSA"},
    "CO": {"iso3": "COL", "name": "Colombia", "flag": "🇨🇴", "region": "LAC"},
    "BR": {"iso3": "BRA", "name": "Brazil", "flag": "🇧🇷", "region": "LAC"},
    "PH": {"iso3": "PHL", "name": "Philippines", "flag": "🇵🇭", "region": "EAP"},
    "MX": {"iso3": "MEX", "name": "Mexico", "flag": "🇲🇽", "region": "LAC"},
    "CN": {"iso3": "CHN", "name": "China", "flag": "🇨🇳", "region": "EAP"},
    "IN": {"iso3": "IND", "name": "India", "flag": "🇮🇳", "region": "SA"},
    "ID": {"iso3": "IDN", "name": "Indonesia", "flag": "🇮🇩", "region": "EAP"},
    "CL": {"iso3": "CHL", "name": "Chile", "flag": "🇨🇱", "region": "LAC"},
    "JP": {"iso3": "JPN", "name": "Japan", "flag": "🇯🇵", "region": "EAP"},
    "FR": {"iso3": "FRA", "name": "France", "flag": "🇫🇷", "region": "ECA"},
    "TH": {"iso3": "THA", "name": "Thailand", "flag": "🇹🇭", "region": "EAP"},
    "GB": {"iso3": "GBR", "name": "UK", "flag": "🇬🇧", "region": "ECA"},
    "US": {"iso3": "USA", "name": "United States", "flag": "🇺🇸", "region": "NAM"},
    "DE": {"iso3": "DEU", "name": "Germany", "flag": "🇩🇪", "region": "ECA"},
    "MY": {"iso3": "MYS", "name": "Malaysia", "flag": "🇲🇾", "region": "EAP"},
    "VN": {"iso3": "VNM", "name": "Vietnam", "flag": "🇻🇳", "region": "EAP"},
    "CA": {"iso3": "CAN", "name": "Canada", "flag": "🇨🇦", "region": "NAM"},
    "PL": {"iso3": "POL", "name": "Poland", "flag": "🇵🇱", "region": "ECA"},
    "SA": {"iso3": "SAU", "name": "Saudi Arabia", "flag": "🇸🇦", "region": "MENA"},
    "AU": {"iso3": "AUS", "name": "Australia", "flag": "🇦🇺", "region": "EAP"},
    "KR": {"iso3": "KOR", "name": "South Korea", "flag": "🇰🇷", "region": "EAP"},
    "AE": {"iso3": "ARE", "name": "UAE", "flag": "🇦🇪", "region": "MENA"},
    "UA": {"iso3": "UKR", "name": "Ukraine", "flag": "🇺🇦", "region": "ECA"},
    "IQ": {"iso3": "IRQ", "name": "Iraq", "flag": "🇮🇶", "region": "MENA"},
    "YE": {"iso3": "YEM", "name": "Yemen", "flag": "🇾🇪", "region": "MENA"},
    "AF": {"iso3": "AFG", "name": "Afghanistan", "flag": "🇦🇫", "region": "SA"},
    "MM": {"iso3": "MMR", "name": "Myanmar", "flag": "🇲🇲", "region": "EAP"},
    "LK": {"iso3": "LKA", "name": "Sri Lanka", "flag": "🇱🇰", "region": "SA"},
    "HT": {"iso3": "HTI", "name": "Haiti", "flag": "🇭🇹", "region": "LAC"},
    "CD": {"iso3": "COD", "name": "DR Congo", "flag": "🇨🇩", "region": "SSA"},
    "SO": {"iso3": "SOM", "name": "Somalia", "flag": "🇸🇴", "region": "SSA"},
    "LY": {"iso3": "LBY", "name": "Libya", "flag": "🇱🇾", "region": "MENA"},
    "MZ": {"iso3": "MOZ", "name": "Mozambique", "flag": "🇲🇿", "region": "SSA"},
    "CM": {"iso3": "CMR", "name": "Cameroon", "flag": "🇨🇲", "region": "SSA"},
    "PE": {"iso3": "PER", "name": "Peru", "flag": "🇵🇪", "region": "LAC"},
    "EC": {"iso3": "ECU", "name": "Ecuador", "flag": "🇪🇨", "region": "LAC"},
    "BO": {"iso3": "BOL", "name": "Bolivia", "flag": "🇧🇴", "region": "LAC"},
    "JO": {"iso3": "JOR", "name": "Jordan", "flag": "🇯🇴", "region": "MENA"},
    "MA": {"iso3": "MAR", "name": "Morocco", "flag": "🇲🇦", "region": "MENA"},
    "DZ": {"iso3": "DZA", "name": "Algeria", "flag": "🇩🇿", "region": "MENA"},
    "NP": {"iso3": "NPL", "name": "Nepal", "flag": "🇳🇵", "region": "SA"},
    "KH": {"iso3": "KHM", "name": "Cambodia", "flag": "🇰🇭", "region": "EAP"},
    "TZ": {"iso3": "TZA", "name": "Tanzania", "flag": "🇹🇿", "region": "SSA"},
    "UG": {"iso3": "UGA", "name": "Uganda", "flag": "🇺🇬", "region": "SSA"},
    "AO": {"iso3": "AGO", "name": "Angola", "flag": "🇦🇴", "region": "SSA"},
    "ZM": {"iso3": "ZMB", "name": "Zambia", "flag": "🇿🇲", "region": "SSA"},
    "SN": {"iso3": "SEN", "name": "Senegal", "flag": "🇸🇳", "region": "SSA"},
    "CI": {"iso3": "CIV", "name": "Ivory Coast", "flag": "🇨🇮", "region": "SSA"},
    "HN": {"iso3": "HND", "name": "Honduras", "flag": "🇭🇳", "region": "LAC"},
    "GT": {"iso3": "GTM", "name": "Guatemala", "flag": "🇬🇹", "region": "LAC"},
    "CU": {"iso3": "CUB", "name": "Cuba", "flag": "🇨🇺", "region": "LAC"},
    "KP": {"iso3": "PRK", "name": "North Korea", "flag": "🇰🇵", "region": "EAP"},
    "QA": {"iso3": "QAT", "name": "Qatar", "flag": "🇶🇦", "region": "MENA"},
    "HU": {"iso3": "HUN", "name": "Hungary", "flag": "🇭🇺", "region": "ECA"},
    "RO": {"iso3": "ROU", "name": "Romania", "flag": "🇷🇴", "region": "ECA"},
    "CZ": {"iso3": "CZE", "name": "Czechia", "flag": "🇨🇿", "region": "ECA"},
    "GR": {"iso3": "GRC", "name": "Greece", "flag": "🇬🇷", "region": "ECA"},
    "PT": {"iso3": "PRT", "name": "Portugal", "flag": "🇵🇹", "region": "ECA"},
    "IT": {"iso3": "ITA", "name": "Italy", "flag": "🇮🇹", "region": "ECA"},
    "ES": {"iso3": "ESP", "name": "Spain", "flag": "🇪🇸", "region": "ECA"},
    "SE": {"iso3": "SWE", "name": "Sweden", "flag": "🇸🇪", "region": "ECA"},
    "NO": {"iso3": "NOR", "name": "Norway", "flag": "🇳🇴", "region": "ECA"},
}

# World Bank API returns country.id as ISO2 in some responses; normalize to ISO3 for lookup
ISO2_TO_ISO3 = {iso2: meta["iso3"] for iso2, meta in COUNTRIES.items()}

# World Bank indicator codes
WB_INDICATORS = {
    "inflation": "FP.CPI.TOTL.ZG",          # CPI inflation annual %
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",       # GDP growth annual %
    "debt_gdp": "GC.DOD.TOTL.GD.ZS",         # Central govt debt % GDP
    "reserves_months": "FI.RES.TOTL.MO",      # Total reserves in months of imports
    "current_account": "BN.CAB.XOKA.GD.ZS",   # Current account balance % GDP
    "unemployment": "SL.UEM.TOTL.ZS",          # Unemployment total %
    "gov_expenditure": "GC.XPN.TOTL.GD.ZS",   # Government expenditure % GDP
    "trade_openness": "NE.TRD.GNFS.ZS",       # Trade % GDP
    "fdi_inflow": "BX.KLT.DINV.WD.GD.ZS",    # FDI net inflows % GDP
    "external_debt": "DT.DOD.DECT.GN.ZS",     # External debt stocks % GNI
    "broad_money": "FM.LBL.BMNY.GD.ZS",       # Broad money % GDP
    "domestic_credit": "FS.AST.PRVT.GD.ZS",   # Domestic credit to private sector % GDP
    "political_stability": "PV.EST",            # Political stability estimate (WGI)
    "gov_effectiveness": "GE.EST",              # Government effectiveness (WGI)
    "rule_of_law": "RL.EST",                    # Rule of law estimate (WGI)
    "control_corruption": "CC.EST",             # Control of corruption (WGI)
    "regulatory_quality": "RQ.EST",             # Regulatory quality (WGI)
    "population_growth": "SP.POP.GROW",         # Population growth annual %
    "gni_per_capita": "NY.GNP.PCAP.CD",        # GNI per capita (Atlas method)
    "undernourishment": "SN.ITK.DEFC.ZS",
    "poverty": "SI.POV.DDAY",
    "life_expectancy": "SP.DYN.LE00.IN",
    "literacy_rate": "SE.ADT.LITR.ZS",
    "maternal_mortality": "SH.STA.MMRT",
    "co2_emissions": "EN.ATM.CO2E.PC",
}

# FRED series IDs
FRED_SERIES = {
    "us_10y": "DGS10",                    # US 10-Year Treasury yield
    "vix": "VIXCLS",                       # CBOE VIX
    "dxy": "DTWEXBGS",                     # Trade weighted USD index
    "oil_wti": "DCOILWTICO",              # WTI crude oil price
    "gold": "GOLDAMGBD228NLBM",           # Gold price London fixing
    "ted_spread": "TEDRATE",               # TED Spread (risk indicator)
    "us_cpi": "CPIAUCSL",                 # US CPI
    "fed_funds": "FEDFUNDS",              # Federal Funds Rate
    "sp500": "SP500",                      # S&P 500
    "embi": "BAMLEMCBPIOAS",              # Emerging Markets Bond Index spread
}


# ═══════════════════════════════════════════════
# CACHE UTILITIES
# ═══════════════════════════════════════════════

def cache_get(key: str) -> Optional[dict]:
    """Get cached data if fresh."""
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        data = json.loads(path.read_text())
        if time.time() - data.get("_ts", 0) < CACHE_TTL:
            return data.get("payload")
    return None

def cache_set(key: str, payload):
    """Cache data with timestamp."""
    path = CACHE_DIR / f"{key}.json"
    path.write_text(json.dumps({"_ts": time.time(), "payload": payload}))


# ═══════════════════════════════════════════════
# DATA FETCHERS
# ═══════════════════════════════════════════════

async def fetch_world_bank(indicator: str, iso3_list: str, years: int = 5) -> dict:
    """Fetch indicator from World Bank API v2 — batched by 10 countries. Uses sync httpx (async client has DNS/timeout issues)."""
    cache_key = f"wb_{indicator}_{years}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    all_countries = iso3_list.split(";")
    batches = [all_countries[i:i+10] for i in range(0, len(all_countries), 10)]

    result = {}
    for batch in batches:
        batch_str = ";".join(batch)
        url = f"https://api.worldbank.org/v2/country/{batch_str}/indicator/{indicator}"
        params = {
            "format": "json",
            "per_page": 1000,
            "date": f"{datetime.now().year - years}:{datetime.now().year}",
        }
        try:
            resp = httpx.get(url, params=params, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) > 1 and data[1]:
                    for entry in data[1]:
                        raw_id = entry.get("country", {}).get("id", "")
                        iso3 = ISO2_TO_ISO3.get(raw_id, raw_id)
                        if not iso3:
                            continue
                        year = entry.get("date", "")
                        value = entry.get("value")
                        if iso3 not in result:
                            result[iso3] = {}
                        result[iso3][year] = value
        except Exception as e:
            print(f"[WB ERROR] {indicator} batch {batch_str[:20]}: {e}")
            continue

    cache_set(cache_key, result)
    return result


async def fetch_fred(series_id: str, obs_count: int = 30) -> dict:
    """Fetch data from FRED API (no key needed for basic access). Uses sync httpx."""
    cache_key = f"fred_{series_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    params = {"cosd": (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")}

    result = {"series": series_id, "data": []}
    try:
        resp = httpx.get(url, params=params, timeout=20)
        if resp.status_code == 200:
            lines = resp.text.strip().split("\n")
            for line in lines[1:]:  # skip header
                parts = line.split(",")
                if len(parts) == 2 and parts[1] != ".":
                    try:
                        result["data"].append({
                            "date": parts[0],
                            "value": float(parts[1])
                        })
                    except ValueError:
                        continue
            if result["data"]:
                result["latest"] = result["data"][-1]["value"]
    except Exception as e:
        print(f"[FRED ERROR] {series_id}: {e}")

    cache_set(cache_key, result)
    return result


async def fetch_gdelt_gkg(country_code: str) -> dict:
    """Fetch GDELT Global Knowledge Graph data for sentiment analysis. Uses sync httpx."""
    cache_key = f"gdelt_{country_code}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    country_name = COUNTRIES.get(country_code, {}).get("name", "")
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": f'"{country_name}" (economy OR crisis OR debt OR inflation OR default)',
        "mode": "timelinevol",
        "timespan": "30d",
        "format": "json",
    }

    result = {"country": country_code, "sentiment": 0, "volume": 0, "articles": []}
    try:
        resp = httpx.get(url, params=params, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            if "timeline" in data and data["timeline"]:
                timeline = data["timeline"][0].get("data", [])
                if timeline:
                    volumes = [p.get("value", 0) for p in timeline]
                    result["volume"] = sum(volumes)
                    result["avg_volume"] = sum(volumes) / len(volumes) if volumes else 0
                    if len(volumes) >= 7:
                        recent = sum(volumes[-7:]) / 7
                        older = sum(volumes[:7]) / 7
                        result["trend"] = (recent - older) / max(older, 1) * 100
    except Exception as e:
        print(f"[GDELT ERROR] {country_code}: {e}")

    cache_set(cache_key, result)
    return result


async def fetch_gdelt_tone(country_code: str) -> dict:
    """Fetch GDELT tone/sentiment for a country. Uses sync httpx."""
    cache_key = f"gdelt_tone_{country_code}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    country_name = COUNTRIES.get(country_code, {}).get("name", "")
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": f'"{country_name}" economy',
        "mode": "tonechart",
        "timespan": "14d",
        "format": "json",
    }

    result = {"country": country_code, "tone": 0}
    try:
        resp = httpx.get(url, params=params, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            if "tonechart" in data and data["tonechart"]:
                tones = [a.get("tone", 0) for a in data["tonechart"][:50]]
                result["tone"] = sum(tones) / len(tones) if tones else 0
    except Exception as e:
        print(f"[GDELT TONE ERROR] {country_code}: {e}")

    cache_set(cache_key, result)
    return result


# ═══════════════════════════════════════════════
# COLLAPSE INDEX CALCULATOR
# ═══════════════════════════════════════════════

def get_latest_value(wb_data: dict, iso3: str) -> Optional[float]:
    """Get most recent non-null value from World Bank data."""
    country_data = wb_data.get(iso3, {})
    for year in sorted(country_data.keys(), reverse=True):
        val = country_data.get(year)
        if val is not None:
            return float(val)
    return None


def compute_stress(indicators: dict) -> float:
    """
    Compute stress score (0-100).
    S = Σ(Si × Wi)

    Components:
    S1: Expectation Gap (inflation severity) — weight 0.25
    S2: Velocity of Change (GDP decline rate) — weight 0.20
    S3: Internal Contradiction (debt vs growth) — weight 0.20
    S4: External Shocks (current account + FDI) — weight 0.20
    S5: Market Pressure (GDELT sentiment) — weight 0.15
    """
    # S1: Inflation severity (0-100)
    inf = indicators.get("inflation", 5)
    if inf is None:
        inf = 5
    s1 = min(100, max(0, (abs(inf) / 50) * 100)) if inf > 10 else min(100, max(0, (abs(inf) / 20) * 100 * 0.5))
    if inf > 100:
        s1 = min(100, 70 + (inf - 100) / 500 * 30)

    # S2: GDP decline severity (0-100)
    gdp = indicators.get("gdp_growth", 2)
    if gdp is None:
        gdp = 2
    s2 = min(100, max(0, (-gdp + 3) * 15)) if gdp < 3 else 0

    # S3: Debt-to-GDP severity (0-100)
    debt = indicators.get("debt_gdp", 50)
    if debt is None:
        debt = 50
    s3 = min(100, max(0, (debt - 40) / 200 * 100))

    # S4: External vulnerability (0-100)
    ca = indicators.get("current_account", 0)
    if ca is None:
        ca = 0
    ext_debt = indicators.get("external_debt", 50)
    if ext_debt is None:
        ext_debt = 50
    s4_ca = min(50, max(0, (-ca) * 5)) if ca < 0 else 0
    s4_ext = min(50, max(0, (ext_debt - 50) / 300 * 50))
    s4 = s4_ca + s4_ext

    # S5: News sentiment pressure (0-100)
    tone = indicators.get("gdelt_tone", 0)
    news_trend = indicators.get("gdelt_trend", 0)
    s5 = min(100, max(0, (-tone * 10) + (news_trend * 0.5)))

    stress = (s1 * 0.25) + (s2 * 0.20) + (s3 * 0.20) + (s4 * 0.20) + (s5 * 0.15)
    return min(100, max(0, stress))


def compute_absorption(indicators: dict) -> float:
    """
    Compute absorption capacity (0.1-2.0).
    A = mean(reserves_score, fiscal_score, institutional_score)
    Higher = more absorption capacity = lower CI
    """
    # Reserves adequacy
    reserves = indicators.get("reserves_months", 3)
    if reserves is None:
        reserves = 3
    res_score = min(2, max(0.1, reserves / 6))

    # Fiscal space (inverse of debt burden)
    debt = indicators.get("debt_gdp", 60)
    if debt is None:
        debt = 60
    fiscal_score = min(2, max(0.1, (200 - debt) / 100))

    # Institutional credibility (WGI governance average)
    gov_eff = indicators.get("gov_effectiveness", 0)
    rule_law = indicators.get("rule_of_law", 0)
    corruption = indicators.get("control_corruption", 0)
    reg_quality = indicators.get("regulatory_quality", 0)
    if gov_eff is None: gov_eff = 0
    if rule_law is None: rule_law = 0
    if corruption is None: corruption = 0
    if reg_quality is None: reg_quality = 0

    # WGI ranges from -2.5 to 2.5, normalize to 0.1-2.0
    wgi_avg = (gov_eff + rule_law + corruption + reg_quality) / 4
    inst_score = min(2, max(0.1, (wgi_avg + 2.5) / 5 * 2))

    return (res_score + fiscal_score + inst_score) / 3


def compute_resilience(indicators: dict) -> float:
    """
    Compute resilience (0.1-2.0).
    R = geometric_mean(recovery_capacity, policy_flexibility)
    """
    # Recovery capacity (based on GDP growth trend)
    gdp = indicators.get("gdp_growth", 2)
    if gdp is None:
        gdp = 2
    recovery = min(2, max(0.1, (gdp + 5) / 10 * 2))

    # Policy flexibility (reserves + low debt + governance)
    reserves = indicators.get("reserves_months", 3)
    debt = indicators.get("debt_gdp", 60)
    pol_stab = indicators.get("political_stability", 0)
    if reserves is None: reserves = 3
    if debt is None: debt = 60
    if pol_stab is None: pol_stab = 0

    flex_score = min(2, max(0.1,
        (reserves / 12 * 0.4) +
        ((200 - debt) / 200 * 0.3) +
        ((pol_stab + 2.5) / 5 * 0.3) * 2
    ))

    # Geometric mean
    return max(0.1, math.sqrt(recovery * flex_score))


def compute_collapse_index(indicators: dict) -> dict:
    """
    CI = [Stress / (Absorption + Resilience)] × 100
    Clamped to 0-100
    """
    stress = compute_stress(indicators)
    absorption = compute_absorption(indicators)
    resilience = compute_resilience(indicators)

    raw_ci = (stress / (absorption + resilience)) * 1.5
    ci = min(100, max(0, raw_ci))

    # Risk classification
    if ci >= 70:
        level, window = "CRITICAL", "0-6 mo"
    elif ci >= 50:
        level, window = "DANGER", "6-12 mo"
    elif ci >= 25:
        level, window = "CAUTION", "12-24 mo"
    else:
        level, window = "SAFE", "24-36 mo"

    return {
        "ci": round(ci, 1),
        "stress": round(stress, 2),
        "absorption": round(absorption, 3),
        "resilience": round(resilience, 3),
        "level": level,
        "window": window,
    }


def compute_ci(indicators: dict) -> tuple:
    """
    Standalone CI calculator. Returns (ci, level, stress, absorption, resilience).
    Uses the same logic as compute_collapse_index.
    """
    d = compute_collapse_index(indicators)
    return (d["ci"], d["level"], d["stress"], d["absorption"], d["resilience"])


# ═══════════════════════════════════════════════
# FRACTURE INDEX CALCULATOR
# ═══════════════════════════════════════════════

async def compute_fracture_index(global_data: dict) -> dict:
    """
    FI = [α×TF + β×AC + γ×IS + δ×RS + ε×NP] × DM × (1 + EV)
    Uses FRED global indicators as proxies.
    """
    # Get global market indicators
    vix_data = await fetch_fred("VIXCLS")
    oil_data = await fetch_fred("DCOILWTICO")
    dxy_data = await fetch_fred("DTWEXBGS")
    embi_data = await fetch_fred("BAMLEMCBPIOAS")
    gold_data = await fetch_fred("GOLDAMGBD228NLBM")

    vix = vix_data.get("latest", 20)
    oil = oil_data.get("latest", 70)
    dxy = dxy_data.get("latest", 105)
    embi = embi_data.get("latest", 350)
    gold = gold_data.get("latest", 2000)

    # Trade Fragmentation proxy (normalized 0-1)
    # Higher DXY + higher EMBI = more fragmentation
    tf = min(1, max(0, ((dxy - 90) / 30 * 0.5) + ((embi - 200) / 600 * 0.5)))

    # Alliance Cohesion Decay proxy
    # Higher VIX = more uncertainty
    ac = min(1, max(0, (vix - 12) / 40))

    # Institutional Stress proxy
    # Combined VIX + EMBI signals
    is_score = min(1, max(0, ((vix - 15) / 35 * 0.5) + ((embi - 250) / 500 * 0.5)))

    # Resource Scarcity Pressure proxy
    # Oil volatility + Gold as safe haven indicator
    rs = min(1, max(0, ((oil - 50) / 80 * 0.4) + ((gold - 1500) / 1500 * 0.6)))

    # Strategic Proliferation Stress (fixed estimate — needs SIPRI data)
    np_score = 0.44

    # Domestic Multiplier (average of critical countries / total)
    critical_count = sum(1 for c in global_data.values() if c.get("ci", 0) >= 70)
    dm = 1.0 + (critical_count / len(global_data) * 0.5) if global_data else 1.0

    # Escalation Velocity (VIX rate of change as proxy)
    vix_hist = vix_data.get("data", [])
    ev = 0
    if len(vix_hist) >= 14:
        recent_vix = sum(d["value"] for d in vix_hist[-7:]) / 7
        older_vix = sum(d["value"] for d in vix_hist[-14:-7]) / 7
        ev = max(0, min(0.5, (recent_vix - older_vix) / older_vix)) if older_vix > 0 else 0

    # Composite FI
    raw_fi = (tf * 0.25 + ac * 0.20 + is_score * 0.20 + rs * 0.20 + np_score * 0.15) * dm * (1 + ev)
    fi_score = min(100, max(0, raw_fi * 100))

    return {
        "score": round(fi_score, 1),
        "components": {
            "trade_fragmentation": {"value": round(tf, 3), "weight": 0.25},
            "alliance_cohesion": {"value": round(ac, 3), "weight": 0.20},
            "institutional_stress": {"value": round(is_score, 3), "weight": 0.20},
            "resource_scarcity": {"value": round(rs, 3), "weight": 0.20},
            "strategic_proliferation": {"value": round(np_score, 3), "weight": 0.15},
            "domestic_multiplier": {"value": round(dm, 3), "type": "multiplier"},
            "escalation_velocity": {"value": round(ev, 3), "type": "multiplier"},
        },
        "market_data": {
            "vix": vix,
            "oil_wti": oil,
            "dxy": dxy,
            "embi_spread": embi,
            "gold": gold,
        },
        "status": "STRESSED" if fi_score >= 55 else "ELEVATED" if fi_score >= 40 else "NORMAL",
        "updated": datetime.utcnow().isoformat() + "Z",
    }


# ═══════════════════════════════════════════════
# CAUSAL ENTROPY INDEX
# ═══════════════════════════════════════════════

def compute_causal_entropy(global_data: dict, fi_data: dict) -> dict:
    """
    CEI = [α·IC + β·RL + γ·IN] / (1 + δ·RR)
    Interconnection Complexity, Response Latency, Information Noise, Redundancy/Reserves
    """
    if not global_data:
        return {"score": 50, "status": "FLUX"}

    ci_values = [c.get("ci", 50) for c in global_data.values()]
    avg_ci = sum(ci_values) / len(ci_values)
    std_ci = (sum((x - avg_ci) ** 2 for x in ci_values) / len(ci_values)) ** 0.5

    # Interconnection Complexity (how correlated are countries)
    ic = min(1, std_ci / 30)

    # Response Latency proxy (average governance quality)
    gov_scores = [c.get("indicators", {}).get("gov_effectiveness", 0) or 0 for c in global_data.values()]
    avg_gov = sum(gov_scores) / len(gov_scores) if gov_scores else 0
    rl = min(1, max(0, (1 - (avg_gov + 2.5) / 5)))

    # Information Noise (from Fracture Index VIX component)
    vix = fi_data.get("market_data", {}).get("vix", 20)
    info_noise = min(1, max(0, (vix - 12) / 35))

    # Redundancy/Reserves
    reserves = [c.get("indicators", {}).get("reserves_months", 3) or 3 for c in global_data.values()]
    avg_reserves = sum(reserves) / len(reserves)
    rr = min(1, max(0, avg_reserves / 12))

    raw_cei = (0.30 * ic + 0.25 * rl + 0.25 * info_noise) / (1 + 0.20 * rr)
    cei_score = min(100, max(0, raw_cei * 130))

    if cei_score >= 75:
        status = "ENTROPY"
    elif cei_score >= 50:
        status = "CHAOS"
    elif cei_score >= 25:
        status = "FLUX"
    else:
        status = "ORDER"

    return {
        "score": round(cei_score, 1),
        "components": {
            "interconnection_complexity": round(ic, 3),
            "response_latency": round(rl, 3),
            "information_noise": round(info_noise, 3),
            "redundancy_reserves": round(rr, 3),
        },
        "status": status,
        "updated": datetime.utcnow().isoformat() + "Z",
    }


# ═══════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════

@app.get("/")
async def root():
    return {"service": "CAUSENTIA API", "version": "1.0.0", "status": "operational"}


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "cache_dir": str(CACHE_DIR),
        "countries": len(COUNTRIES),
    }


@app.get("/api/data")
async def get_full_data():
    """
    Main endpoint — returns complete dashboard data.
    Fetches from all sources, computes all indices.
    """
    cache_key = "full_dashboard"
    cached = cache_get(cache_key)
    if cached:
        return JSONResponse(content=cached)

    # Build ISO3 list for World Bank batch request
    iso3_list = ";".join(c["iso3"] for c in COUNTRIES.values())

    # Fetch all World Bank indicators in parallel
    wb_tasks = {
        name: fetch_world_bank(code, iso3_list, 5)
        for name, code in WB_INDICATORS.items()
    }

    # Fetch GDELT for top-risk countries (limit API calls)
    top_countries = list(COUNTRIES.keys())[:20]
    gdelt_tasks = {
        code: fetch_gdelt_tone(code)
        for code in top_countries
    }

    # Execute all in parallel
    wb_keys = list(wb_tasks.keys())
    wb_results_list = await asyncio.gather(*wb_tasks.values(), return_exceptions=True)
    wb_results = {}
    for i, key in enumerate(wb_keys):
        if not isinstance(wb_results_list[i], Exception):
            wb_results[key] = wb_results_list[i]
        else:
            wb_results[key] = {}
            print(f"[FETCH ERROR] {key}: {wb_results_list[i]}")

    gdelt_keys = list(gdelt_tasks.keys())
    gdelt_results_list = await asyncio.gather(*gdelt_tasks.values(), return_exceptions=True)
    gdelt_results = {}
    for i, key in enumerate(gdelt_keys):
        if not isinstance(gdelt_results_list[i], Exception):
            gdelt_results[key] = gdelt_results_list[i]

    # Compute CI for each country
    countries_data = {}
    for iso2, meta in COUNTRIES.items():
        iso3 = meta["iso3"]

        indicators = {}
        for ind_name, wb_data in wb_results.items():
            indicators[ind_name] = get_latest_value(wb_data, iso3)

        # Add GDELT data
        gdelt = gdelt_results.get(iso2, {})
        indicators["gdelt_tone"] = gdelt.get("tone", 0)
        indicators["gdelt_trend"] = gdelt.get("trend", 0)

        ci_result = compute_collapse_index(indicators)

        # Human Development Score (0-100, higher = better)
        life_exp = indicators.get("life_expectancy") or 0
        literacy = indicators.get("literacy_rate") or 0
        poverty = indicators.get("poverty") or 0
        hunger = indicators.get("undernourishment") or 0
        hdi_life = min(100, (life_exp / 85) * 100) if life_exp else 50
        hdi_lit = literacy if literacy else 50
        hdi_pov = max(0, 100 - poverty * 2) if poverty else 50
        hdi_hunger = max(0, 100 - hunger * 3) if hunger else 50
        hdi = round((hdi_life * 0.3 + hdi_lit * 0.3 + hdi_pov * 0.2 + hdi_hunger * 0.2), 1)

        ind = {
            "inflation": round(indicators.get("inflation", 0) or 0, 1),
            "gdp_growth": round(indicators.get("gdp_growth", 0) or 0, 1),
            "debt_gdp": round(indicators.get("debt_gdp", 0) or 0, 1),
            "reserves_months": round(indicators.get("reserves_months", 0) or 0, 1),
            "current_account": round(indicators.get("current_account", 0) or 0, 1),
            "unemployment": round(indicators.get("unemployment", 0) or 0, 1),
            "external_debt": round(indicators.get("external_debt", 0) or 0, 1),
            "gov_effectiveness": round(indicators.get("gov_effectiveness", 0) or 0, 3),
            "rule_of_law": round(indicators.get("rule_of_law", 0) or 0, 3),
            "political_stability": round(indicators.get("political_stability", 0) or 0, 3),
            "gdelt_tone": round(indicators.get("gdelt_tone", 0) or 0, 2),
            "undernourishment": round(hunger, 1) if hunger else None,
            "poverty": round(poverty, 1) if poverty else None,
            "life_expectancy": round(life_exp, 1) if life_exp else None,
            "literacy_rate": round(literacy, 1) if literacy else None,
            "maternal_mortality": round(indicators.get("maternal_mortality") or 0, 1) if indicators.get("maternal_mortality") is not None else None,
            "co2_emissions": round(indicators.get("co2_emissions") or 0, 2) if indicators.get("co2_emissions") is not None else None,
        }
        countries_data[iso2] = {
            "code": iso2,
            "iso3": iso3,
            "name": meta["name"],
            "flag": meta["flag"],
            "region": meta["region"],
            **ci_result,
            "hdi": hdi,
            "indicators": ind,
        }

    # Compute Fracture Index
    fi_data = await compute_fracture_index(countries_data)

    # Compute CausalEntropy Index
    cei_data = compute_causal_entropy(countries_data, fi_data)

    # Summary counts
    counts = {"critical": 0, "danger": 0, "caution": 0, "safe": 0}
    for c in countries_data.values():
        if c["ci"] >= 70: counts["critical"] += 1
        elif c["ci"] >= 50: counts["danger"] += 1
        elif c["ci"] >= 25: counts["caution"] += 1
        else: counts["safe"] += 1

    result = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "counts": counts,
        "countries": countries_data,
        "fracture_index": fi_data,
        "causal_entropy": cei_data,
        "data_sources": {
            "world_bank": {"status": "connected", "indicators": len(wb_results)},
            "fred": {"status": "connected"},
            "gdelt": {"status": "connected", "countries_monitored": len(gdelt_results)},
        },
    }

    # Cache for 6 hours
    cache_set(cache_key, result)
    return JSONResponse(content=result)


@app.get("/api/country/{code}")
async def get_country(code: str):
    """Return detailed data for a single country from cached dashboard data."""
    code = code.upper()

    # Try to get from full dashboard cache first
    cached = cache_get("full_dashboard")
    if cached and code in cached.get("countries", {}):
        country = cached["countries"][code]
        # Add history data if available
        iso3 = COUNTRIES.get(code, {}).get("iso3", code)
        history = {}
        hist_indicators = {
            "FP.CPI.TOTL.ZG": "inflation",
            "NY.GDP.MKTP.KD.ZG": "gdp_growth",
            "GC.DOD.TOTL.GD.ZS": "debt_gdp",
            "FI.RES.TOTL.MO": "reserves_months",
            "BN.CAB.XOKA.GD.ZS": "current_account",
        }
        for wb_code, name in hist_indicators.items():
            cache_key = f"wb_{wb_code}_5"
            wb_cached = cache_get(cache_key)
            if wb_cached:
                iso3_key = None
                if iso3 in wb_cached:
                    iso3_key = iso3
                elif code in wb_cached:
                    iso3_key = code
                if iso3_key:
                    series = wb_cached[iso3_key]
                    history[name] = {y: v for y, v in series.items() if v is not None}

        country["history"] = history
        country["updated"] = cached.get("timestamp", datetime.now(timezone.utc).isoformat() + "Z")
        return country

    # Fallback: return basic data if no cache
    if code not in COUNTRIES:
        return {"error": f"Country {code} not found"}

    meta = COUNTRIES[code]
    return {
        "code": code,
        "iso3": meta["iso3"],
        "name": meta["name"],
        "flag": meta["flag"],
        "region": meta["region"],
        "ci": 0,
        "level": "UNKNOWN",
        "stress": 0,
        "absorption": 0,
        "resilience": 0,
        "indicators": {},
        "history": {},
        "hdi": 0,
        "updated": datetime.now(timezone.utc).isoformat() + "Z",
        "note": "Data loading, please refresh in 30 seconds",
    }


@app.get("/api/market")
async def get_market_data():
    """Get global market indicators from FRED."""
    tasks = {name: fetch_fred(series_id) for name, series_id in FRED_SERIES.items()}
    keys = list(tasks.keys())
    results_list = await asyncio.gather(*tasks.values(), return_exceptions=True)

    market = {}
    for i, key in enumerate(keys):
        if not isinstance(results_list[i], Exception):
            data = results_list[i]
            market[key] = {
                "latest": data.get("latest"),
                "series": key,
                "data_points": len(data.get("data", [])),
            }

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "market": market,
    }


@app.get("/api/gdelt/{iso2}")
async def get_gdelt(iso2: str):
    """Get GDELT news sentiment for a country."""
    iso2 = iso2.upper()
    if iso2 not in COUNTRIES:
        raise HTTPException(status_code=404, detail=f"Country {iso2} not found")

    tone = await fetch_gdelt_tone(iso2)
    vol = await fetch_gdelt_gkg(iso2)

    return {
        "country": iso2,
        "name": COUNTRIES[iso2]["name"],
        "tone": tone,
        "volume": vol,
        "updated": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/api/montecarlo/{iso2}")
async def run_montecarlo(iso2: str, scenarios: int = 10000):
    """Run Monte Carlo simulation for a country."""
    iso2 = iso2.upper()
    if iso2 not in COUNTRIES:
        raise HTTPException(status_code=404, detail=f"Country {iso2} not found")

    scenarios = min(scenarios, 50000)

    # Get current CI
    full_data = await get_full_data()
    body = full_data.body
    data = json.loads(body.decode() if isinstance(body, bytes) else body)

    country = data.get("countries", {}).get(iso2, {})
    ci = country.get("ci", 50)
    stress = country.get("stress", 30)

    import random
    results = []
    bins = [0] * 50

    for _ in range(scenarios):
        # Add randomness based on stress level
        shock = (random.gauss(0, 1) * (stress / 100) * 20)
        trend_bias = (random.random() - 0.45) * 5
        v = max(0, min(100, ci + shock + trend_bias))
        results.append(v)
        bin_idx = min(49, int(v / 2))
        bins[bin_idx] += 1

    results.sort()
    mean_ci = sum(results) / len(results)
    p5 = results[int(len(results) * 0.05)]
    p95 = results[int(len(results) * 0.95)]
    p_crisis = sum(1 for v in results if v >= 70) / len(results) * 100

    return {
        "country": iso2,
        "name": COUNTRIES[iso2]["name"],
        "scenarios": scenarios,
        "current_ci": ci,
        "results": {
            "mean": round(mean_ci, 1),
            "p5_best": round(p5, 1),
            "p95_worst": round(p95, 1),
            "p_crisis": round(p_crisis, 1),
        },
        "distribution": bins,
        "updated": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/api/scenario")
async def run_scenario(request: Request):
    """Apply economic shocks and recalculate CI using the same formula as the main dashboard."""
    body = await request.json()
    shocks = body.get("shocks", {})
    country_overrides = body.get("country_overrides", {})

    cached = cache_get("full_dashboard")
    if not cached:
        return {"error": "No cached data. Please load dashboard first."}

    countries_data = cached.get("countries", {})
    results = []

    for code, cdata in countries_data.items():
        indicators = dict(cdata.get("indicators", {}))

        for key, delta in shocks.items():
            if key in indicators and indicators[key] is not None:
                indicators[key] = indicators[key] + delta
            elif delta != 0:
                indicators[key] = delta

        if code in country_overrides:
            for key, delta in country_overrides[code].items():
                if key in indicators and indicators[key] is not None:
                    indicators[key] = indicators[key] + delta
                elif delta != 0:
                    indicators[key] = delta

        new_ci, new_level, new_stress, new_absorption, new_resilience = compute_ci(indicators)

        original_ci = cdata.get("ci", 0)
        delta_ci = round(new_ci - original_ci, 1)

        results.append({
            "code": code,
            "name": cdata.get("name", ""),
            "flag": cdata.get("flag", ""),
            "region": cdata.get("region", ""),
            "originalCI": original_ci,
            "newCI": new_ci,
            "delta": delta_ci,
            "originalLevel": cdata.get("level", ""),
            "newLevel": new_level,
            "stress": new_stress,
            "absorption": new_absorption,
            "resilience": new_resilience,
            "indicators": indicators,
        })

    results.sort(key=lambda x: x["delta"], reverse=True)

    return {
        "scenario": shocks,
        "country_overrides": country_overrides,
        "results": results,
        "summary": {
            "avg_delta": round(sum(r["delta"] for r in results) / max(1, len(results)), 1),
            "critical": len([r for r in results if r["newCI"] >= 70]),
            "danger": len([r for r in results if 50 <= r["newCI"] < 70]),
            "caution": len([r for r in results if 25 <= r["newCI"] < 50]),
            "safe": len([r for r in results if r["newCI"] < 25]),
            "old_critical": len([r for r in results if r["originalCI"] >= 70]),
            "old_danger": len([r for r in results if 50 <= r["originalCI"] < 70]),
            "downgrades": len([r for r in results if r["delta"] > 5]),
            "beneficiaries": len([r for r in results if r["delta"] < -2]),
            "total": len(results),
        }
    }


@app.post("/api/chat")
async def ai_chat(request: Request):
    """AI Analyst Chat - uses Claude for deep analysis, GPT for quick summaries."""
    body = await request.json()
    question = body.get("question", "")
    country_code = body.get("country", None)
    mode = body.get("mode", "auto")  # auto, claude, gpt

    if not question:
        return {"error": "No question provided"}

    # Build context from live data
    cached = cache_get("full_dashboard")
    if not cached:
        return {"error": "Dashboard data not loaded yet. Please refresh the main page first."}

    countries_data = cached.get("countries", {})

    # Build data context
    context_parts = []

    # Global summary
    counts = cached.get("counts", {})
    fi = cached.get("fracture_index", {})
    cei = cached.get("causal_entropy", {})
    context_parts.append(f"CAUSENTIA Global Status: {counts.get('critical',0)} Critical, {counts.get('danger',0)} Danger, {counts.get('caution',0)} Caution, {counts.get('safe',0)} Safe out of {len(countries_data)} countries.")
    context_parts.append(f"Fracture Index: {fi.get('score',0)} ({fi.get('level','N/A')}), CausalEntropy Index: {cei.get('score',0)} ({cei.get('level','N/A')})")

    # Top 10 highest risk
    sorted_countries = sorted(countries_data.values(), key=lambda x: x.get('ci', 0), reverse=True)
    top10 = sorted_countries[:10]
    context_parts.append("Top 10 Highest Risk: " + ", ".join([f"{c['name']} CI:{c['ci']} ({c.get('level','')})" for c in top10]))

    # If specific country requested, add detailed data
    if country_code and country_code.upper() in countries_data:
        c = countries_data[country_code.upper()]
        ind = c.get("indicators", {})
        context_parts.append(f"\nDetailed data for {c['name']} ({c['code']}):")
        context_parts.append(f"  Collapse Index: {c['ci']} - Level: {c.get('level','')} - Risk Window: {c.get('risk_window','')}")
        context_parts.append(f"  Stress: {c.get('stress',0)}, Absorption: {c.get('absorption',0)}, Resilience: {c.get('resilience',0)}")
        context_parts.append(f"  HDI: {c.get('hdi',0)}")
        context_parts.append(f"  Economic: Inflation={ind.get('inflation','N/A')}%, GDP Growth={ind.get('gdp_growth','N/A')}%, Debt/GDP={ind.get('debt_gdp','N/A')}%, Reserves={ind.get('reserves_months','N/A')} months")
        context_parts.append(f"  External: Current Account={ind.get('current_account','N/A')}% GDP, External Debt={ind.get('external_debt','N/A')}% GNI, FDI={ind.get('fdi_inflow','N/A')}% GDP")
        context_parts.append(f"  Governance: Political Stability={ind.get('political_stability','N/A')}, Gov Effectiveness={ind.get('gov_effectiveness','N/A')}, Rule of Law={ind.get('rule_of_law','N/A')}, Corruption Control={ind.get('control_corruption','N/A')}")
        context_parts.append(f"  Human Dev: Life Expectancy={ind.get('life_expectancy','N/A')} yrs, Literacy={ind.get('literacy_rate','N/A')}%, Poverty={ind.get('poverty','N/A')}%, Undernourishment={ind.get('undernourishment','N/A')}%, Maternal Mortality={ind.get('maternal_mortality','N/A')}/100k")
        context_parts.append(f"  News: GDELT Tone={ind.get('gdelt_tone','N/A')}, Trend={ind.get('gdelt_trend','N/A')}%")

    data_context = "\n".join(context_parts)

    system_prompt = f"""You are CAUSENTIA AI Analyst — an expert sovereign risk intelligence system. You analyze countries using the Collapse Index (CI) methodology:
- CI 0-25: SAFE (24-36 month window)
- CI 25-50: CAUTION (12-24 month window)
- CI 50-70: DANGER (6-12 month window)
- CI 70-85: CRITICAL (0-6 month window)
- CI 85-100: COLLAPSE (imminent)

CI = [Σ(Sᵢ × Wᵢ)] / (A + R) × 100 where S=Stress, A=Absorption, R=Resilience.

You have access to LIVE data from World Bank (25 indicators), FRED (market data), and GDELT (news sentiment) for {len(countries_data)} countries.

CURRENT LIVE DATA:
{data_context}

Rules:
- Never mention that you are Claude, GPT, or any specific AI model. You are CAUSENTIA AI Analyst.
- Sign off responses as "— CAUSENTIA AI" only when appropriate for formal analysis.
- Always cite specific numbers from the data
- Be direct and analytical, like a Bloomberg terminal analyst
- Use bullet points for clarity
- If comparing countries, use tables
- Flag any concerning trends or threshold crossings
- Respond in the same language as the question
- Keep responses focused and actionable
- When discussing risks, quantify them with CI scores and indicators"""

    # Decide which AI to use
    use_claude = True
    if mode == "gpt":
        use_claude = False
    elif mode == "auto":
        # Use Claude for deep analysis, GPT for quick questions
        deep_keywords = ["why", "analyze", "explain", "compare", "predict", "scenario", "لماذا", "حلل", "اشرح", "قارن"]
        use_claude = any(kw in question.lower() for kw in deep_keywords)

    try:
        if use_claude:
            # Use Claude for deep analysis
            resp = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": CLAUDE_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 2000,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": question}],
                },
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                answer = data["content"][0]["text"]
                return {"answer": answer, "model": "Claude Sonnet", "provider": "anthropic"}
            else:
                # Fallback to GPT
                use_claude = False

        if not use_claude:
            # Use GPT
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question},
                    ],
                    "max_tokens": 2000,
                },
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json()
                answer = data["choices"][0]["message"]["content"]
                return {"answer": answer, "model": "GPT-4o Mini", "provider": "openai"}
            else:
                return {"error": f"AI API error: {resp.status_code} - {resp.text[:200]}"}

    except Exception as e:
        return {"error": f"AI request failed: {str(e)}"}


@app.post("/api/subscribe")
async def subscribe(request: Request):
    """Store alert subscription."""
    body = await request.json()
    email = body.get("email", "")
    if not email or "@" not in email:
        return {"error": "Invalid email"}

    subs_file = "/tmp/causentia_subscribers.json"
    try:
        with open(subs_file, "r") as f:
            subs = json.load(f)
    except Exception:
        subs = []

    subs.append({
        "email": email,
        "countries": body.get("countries", "all"),
        "triggers": body.get("triggers", {}),
        "frequency": body.get("frequency", "realtime"),
        "subscribed_at": datetime.now(timezone.utc).isoformat(),
    })

    with open(subs_file, "w") as f:
        json.dump(subs, f)

    return {"status": "subscribed", "email": email}


@app.post("/api/cache/clear")
async def clear_cache():
    """Clear all cached data."""
    import shutil
    shutil.rmtree(CACHE_DIR, ignore_errors=True)
    CACHE_DIR.mkdir(exist_ok=True)
    return {"status": "cache cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003)
