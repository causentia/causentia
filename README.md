<div align="center">

# CAUSENTIA

### Sovereign Crisis Early Warning System

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18584024.svg)](https://doi.org/10.5281/zenodo.18584024)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Live](https://img.shields.io/badge/Live-causentia.org-00CC6A)](https://causentia.org)
[![Countries](https://img.shields.io/badge/Countries-80-blue)]()
[![Indicators](https://img.shields.io/badge/Indicators-25+-orange)]()

**Real-time sovereign risk intelligence for 80 countries using 25+ indicators.**
**Open-source. Transparent. Free.**

[Live Dashboard](https://causentia.org) | [API Docs](https://causentia.org/#api) | [Research Papers](https://doi.org/10.5281/zenodo.18584024)

</div>

---

## What is CAUSENTIA?

CAUSENTIA monitors **80 countries** in real-time using data from the **World Bank**, **FRED**, and **GDELT** to compute the **Collapse Index (CI)** — a composite sovereign risk score (0-100) that predicts economic crises with **87% accuracy** and **10.1 months average lead time**.
```
CI = [Stress x Weight] / (Absorption + Resilience) x 100
```

| CI Range | Level | Risk Window |
|----------|-------|-------------|
| 0-25 | SAFE | 24-36 months |
| 25-50 | CAUTION | 12-24 months |
| 50-70 | DANGER | 6-12 months |
| 70-85 | CRITICAL | 0-6 months |
| 85-100 | COLLAPSE | Imminent |

---

## Live Global Assessment (Feb 2026)

| Country | CI | Status | Key Risk |
|---------|-----|--------|----------|
| Sudan | 77.9 | CRITICAL | Hyperinflation 138.8% |
| Haiti | 41.4 | CAUTION | GDP collapse |
| Lebanon | 38.5 | CAUTION | Debt default |
| Argentina | 31.0 | CAUTION | 219.9% inflation |
| Turkey | 18.2 | SAFE | Structural buffers |

**Fracture Index:** 29.6 (NORMAL) | **CausalEntropy:** 36.1 (FLUX)

---

## Quick Start
```bash
git clone https://github.com/causentia/causentia.git
cd causentia/backend
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/health | System health check |
| GET | /api/data | Full dashboard (80 countries) |
| GET | /api/country/{code} | Single country analysis |
| GET | /api/montecarlo/{code} | 10,000-scenario simulation |
| POST | /api/scenario | Custom scenarios |
| POST | /api/chat | AI-powered analysis |

---

## 12 Platform Innovations

1. **Country Deep Dive** - 25+ indicators per country
2. **Regional Heatmap** - CI/HDI toggle
3. **Scenario Builder** - 6 preset shocks
4. **HDI Integration** - Life expectancy, literacy, poverty
5. **Country Comparison** - Side-by-side analysis
6. **AI Analyst Chat** - Claude + GPT, EN/AR
7. **Custom Scenarios** - 8 interactive sliders
8. **PDF Reports** - Professional A4 reports
9. **Early Warning** - 4-tier alerts + trajectory
10. **API Documentation** - Interactive docs
11. **Contagion Network** - 85+ trade links
12. **Alert System** - Email + webhooks

---

## Backtesting Performance

Validated against 15 sovereign crises (2010-2025):

| Metric | CAUSENTIA | KLR | IMF |
|--------|-----------|-----|-----|
| Precision | 85% | 68% | 74% |
| Recall | 87% | 72% | 79% |
| F1-Score | 86% | 70% | 76% |
| Lead Time | 10.1 mo | 8.3 mo | 12.4 mo |

---

## Citation
```bibtex
@software{ibrahim2026causentia,
  author = {Mohamed Ibrahim},
  title = {CAUSENTIA: Sovereign Crisis Early Warning System},
  year = {2026},
  doi = {10.5281/zenodo.18584024},
  url = {https://causentia.org}
}
```

## Research Papers

| # | Title |
|---|-------|
| 1 | CAUSENTIA Technical Report v2.2 |
| 2 | The Collapse Index: A Triadic Framework |
| 3 | CausalEntropy and Fracture Index |
| 4 | Contagion Network Analysis |
| 5 | Software and Dataset Documentation |

All papers: [doi.org/10.5281/zenodo.18584024](https://doi.org/10.5281/zenodo.18584024)

---

## License

MIT License - see [LICENSE](LICENSE)

## Author

**Mohamed Ibrahim** - Independent Researcher, Istanbul, Turkey
- Email: mohamed@mohamed.online
- Web: [causentia.org](https://causentia.org)
- DOI: [10.5281/zenodo.18584024](https://doi.org/10.5281/zenodo.18584024)
