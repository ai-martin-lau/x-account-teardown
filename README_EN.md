<div align="center">

<a href="README.md">简体中文</a> · <a href="README_EN.md">English</a> · <a href="README_JA.md">日本語</a> · <a href="README_KO.md">한국어</a> · <a href="README_ES.md">Español</a>

# 🔬 x-account-teardown

**A data-level "growth autopsy" for any X (Twitter) account**

Give it a `@handle` → export every tweet → reconstruct exactly how the account grew from zero

</div>

---

Not just another tweet scraper. It answers a far more valuable question:

> **How did this big account actually grow from zero? What were its content, cadence, and tactics — and how do I copy them?**

It lays out an account's entire tweet history along the timeline and reverse-engineers its growth arc: **dormancy → inflection point → content pillars → posting cadence → reply strategy → viral-hook formulas → growth curve**, then ships a ready-to-deliver, copy-the-homework report.

## 📈 Sample (a real AI-niche creator who hit 20K followers in 14 months)

See the full sample report at [`assets/sample/REPORT.md`](assets/sample/REPORT.md). At a glance: dormant through 2025, then a sudden launch in 2026-01 (62 originals + 420 replies in a single month), with average likes climbing steadily afterward.

The report shows you:
- **Growth timeline** — dormant for 10 months after sign-up, then went all-in
- **Content pillars** — `video / Claude / Codex / tools / models / learning` — a pure AI-tooling lane
- **Reply strategy** — 5× more replies than originals, cold-started by camping in top accounts' reply sections (with a Top-20 list of targets)
- **Viral-hook formulas** — among the top-60 posts, "first-person/firsthand" ×31, "step-by-step tutorial" and "free/freebie" hooks dominate
- **Copy-this checklist** — 5 directly actionable takeaways

## ✨ Why it's different

| | Typical scraper | x-account-teardown |
|---|---|---|
| Auth | You hand-copy a token from DevTools | **Auto-pulls cookies from your logged-in Chrome** (httpOnly included, zero config) |
| 3200 cap | Hits the wall, misses early tweets | **Date-windowed search bypasses the cap**, back to tweet #1 |
| Output | A pile of JSON | **Growth-autopsy report + growth-curve chart + copy-this checklist** |
| Insight | None | Auto-detects the inflection point, growth slope, hook formulas, reply targets |

## 🚀 Usage

This is a [Claude Code](https://claude.com/claude-code) Skill. Just tell Claude:

```
Analyze how @naval grew its account
```

Claude runs the whole acquire → analyze → report pipeline and gives you a plain-language read.

### Run it manually

```bash
# 1. Install (Python 3.10+)
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 2. Launch Chrome with a debug port, logged in to x.com (for auto cookie pull)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# 3. Pipeline
.venv/bin/python scripts/acquire.py naval --out out/naval_export
.venv/bin/python scripts/analyze.py out/naval_export
.venv/bin/python scripts/report.py out/naval_export/analysis.json --out-dir out/naval_report
```

No debug-port Chrome? Use `--cookies 'auth_token=...; ct0=...'` or set the `X_COOKIES` env var.

## 🧩 How it works

```
acquire.py   twscrape + auto cookie pull + proxy autodetect + 3200 bypass + author filter
   ↓ all_posts.json / profile.json
analyze.py   inflection detection / monthly growth / content pillars (jieba) / cadence / reply strategy / hooks / breakouts
   ↓ analysis.json
report.py    Markdown autopsy report + pure-Python growth-curve SVG
   ↓ REPORT.md / growth.svg
```

See [`references/methodology.md`](references/methodology.md) for the growth-analysis framework and technical details.

## ⚠️ Notes

- Data comes from X's public endpoints — public tweets and engagement only. Follower curves aren't public; this tool uses avg-likes/views over time as a growth proxy.
- Deleted / followers-only tweets are not retrievable.
- A proxy may be required to reach x.com in some regions (the script reuses your system proxy / probes local 7890).
- **⚠️ Use a dedicated burner account, not your main one**: the tool acts with the identity of whatever account is logged into your Chrome, so any anti-abuse risk lands on that account. Only high-frequency mass scraping is risky; pulling a few thousand tweets occasionally is fine.
- For research only. Don't repeatedly mass-scrape the same account.

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ai-martin-lau/x-account-teardown&type=Date)](https://star-history.com/#ai-martin-lau/x-account-teardown&Date)

## 📄 License

MIT
