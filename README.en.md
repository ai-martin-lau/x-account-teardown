<div align="center">

# 🔬 x-account-teardown

**A data-level "growth autopsy" for any X (Twitter) account**

Give it a `@handle` → export every tweet → reconstruct exactly how the account grew from zero

[简体中文](README.md) · English

</div>

---

Not just another tweet scraper. It answers a far more valuable question:

> **How did this big account actually grow from zero? What were its content, cadence, and tactics — and how do I copy them?**

It lays out an account's entire tweet history along the timeline and reverse-engineers its growth arc: **dormancy → inflection point → content pillars → posting cadence → reply strategy → viral-hook formulas → growth curve**, then ships a ready-to-deliver, copy-the-homework report.

See the sample report at [`assets/sample-gengdaJ/REPORT.md`](assets/sample-gengdaJ/REPORT.md) — Yichen (@gengdaJ), a law student who hit 20K followers in 14 months. The teardown reveals: 10 months dormant before going all-in, an all-AI-tooling content focus, **5× more replies than originals** (cold-started by camping in big accounts' reply sections), and the hook formulas behind the top posts.

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
Analyze how @gengdaJ grew its account
```

Claude runs the whole acquire → analyze → report pipeline and gives you a plain-language read.

### Run it manually

```bash
# 1. Install (Python 3.10+)
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 2. Launch Chrome with a debug port, logged in to x.com (for auto cookie pull)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# 3. Pipeline
.venv/bin/python scripts/acquire.py gengdaJ --out out/gengdaJ_export
.venv/bin/python scripts/analyze.py out/gengdaJ_export
.venv/bin/python scripts/report.py out/gengdaJ_export/analysis.json --out-dir out/gengdaJ_report
```

No debug-port Chrome? Use `--cookies 'auth_token=...; ct0=...'` or set the `X_COOKIES` env var.

## 🧩 How it works

```
acquire.py   twscrape + auto cookie pull + proxy autodetect + 3200 bypass + author filter
analyze.py   inflection detection / monthly growth / content pillars / cadence / reply strategy / hooks / breakouts
report.py    Markdown autopsy report + pure-Python growth-curve SVG
```

See [`references/methodology.md`](references/methodology.md) for the growth-analysis framework and technical details.

## ⚠️ Notes

- Data comes from X's public endpoints — public tweets and engagement only. Follower curves aren't public; this tool uses avg-likes/views over time as a growth proxy.
- Deleted / followers-only tweets are not retrievable.
- A proxy may be required to reach x.com in some regions (the script reuses your system proxy / probes local 7890).
- **⚠️ Use a dedicated burner account, not your main one**: the tool acts with the identity of whatever account is logged into your Chrome, so any anti-abuse risk lands on that account. Only high-frequency mass scraping is risky; pulling a few thousand tweets occasionally is fine.
- For research only. Don't repeatedly mass-scrape the same account.

## 📄 License

MIT
