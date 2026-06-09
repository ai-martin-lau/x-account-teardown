#!/usr/bin/env python3
"""
report.py — 把 analysis.json 渲染成一份可直接交付的中文「起号解剖报告」。

产物:
  REPORT.md   —— GitHub 原生可读的 Markdown 报告(含数据表、爆款拆解、复刻清单)
  growth.svg  —— 纯 Python 生成的月度增长曲线(原创量 + 均赞双轴),嵌入报告

用法: python report.py <analysis.json|export_dir> [--out-dir DIR] [--title 标题]
"""
import argparse, json
from pathlib import Path


def fmt(n):
    n = n or 0
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1000:
        return f"{n/1000:.1f}K"
    return str(int(n))


def svg_growth(monthly, out_path):
    rows = [m for m in monthly if m["originals"] > 0 or m["replies"] > 0]
    if not rows:
        out_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
        return
    W, H, pad = 820, 320, 50
    n = len(rows)
    max_act = max(m["originals"] + m["replies"] for m in rows) or 1
    max_like = max(m["avg_likes"] for m in rows) or 1
    bw = (W - 2 * pad) / n
    def x(i): return pad + bw * (i + 0.5)
    def y_act(v): return H - pad - (H - 2 * pad) * v / max_act
    def y_like(v): return H - pad - (H - 2 * pad) * v / max_like
    bars, line_pts, labels = [], [], []
    for i, m in enumerate(rows):
        act = m["originals"] + m["replies"]
        bh = (H - 2 * pad) * act / max_act
        ox = pad + bw * i + bw * 0.15
        ow = bw * 0.7
        # 原创(深) + 回复(浅)堆叠
        oh = (H - 2 * pad) * m["originals"] / max_act
        rh = bh - oh
        bars.append(f"<rect x='{ox:.1f}' y='{H-pad-bh:.1f}' width='{ow:.1f}' height='{rh:.1f}' fill='#cfe3ff'/>")
        bars.append(f"<rect x='{ox:.1f}' y='{H-pad-oh:.1f}' width='{ow:.1f}' height='{oh:.1f}' fill='#1d6fe0'/>")
        line_pts.append(f"{x(i):.1f},{y_like(m['avg_likes']):.1f}")
        if n <= 14 or i % 2 == 0:
            labels.append(f"<text x='{x(i):.1f}' y='{H-pad+16:.1f}' font-size='10' text-anchor='middle' fill='#666'>{m['month'][2:]}</text>")
    dots = "".join(f"<circle cx='{p.split(',')[0]}' cy='{p.split(',')[1]}' r='3' fill='#e0561d'/>" for p in line_pts)
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' font-family='-apple-system,Helvetica,Arial,sans-serif'>
<rect width='{W}' height='{H}' fill='white'/>
<line x1='{pad}' y1='{H-pad}' x2='{W-pad}' y2='{H-pad}' stroke='#ddd'/>
{''.join(bars)}
<polyline points='{' '.join(line_pts)}' fill='none' stroke='#e0561d' stroke-width='2'/>
{dots}
{''.join(labels)}
<rect x='{pad}' y='14' width='11' height='11' fill='#1d6fe0'/><text x='{pad+16}' y='24' font-size='11' fill='#333'>原创/月</text>
<rect x='{pad+80}' y='14' width='11' height='11' fill='#cfe3ff'/><text x='{pad+96}' y='24' font-size='11' fill='#333'>回复/月</text>
<line x1='{pad+170}' y1='20' x2='{pad+190}' y2='20' stroke='#e0561d' stroke-width='2'/><text x='{pad+196}' y='24' font-size='11' fill='#333'>原创均赞(右轴)</text>
</svg>"""
    out_path.write_text(svg, encoding="utf-8")


def bar(v, vmax, width=20):
    f = int(round(width * v / vmax)) if vmax else 0
    return "█" * f + "·" * (width - f)


def build_md(a, title, has_svg):
    p = a["profile"]; s = a["summary"]; g = a["growth_trend"]
    fm = a["format_mix"]; rs = a["reply_strategy"]; cad = a["cadence"]
    name = p.get("displayname") or p.get("username") or title
    handle = p.get("username", "")
    L = []
    L.append(f"# 🔬 X 账号起号解剖 · {name} (@{handle})\n")

    # 一句话判词
    verdict = f"**注册后休眠 {s['dormancy_months']} 个月,{s['inflection_month']} 正式起号" if s.get("dormancy_months") else f"**{s['inflection_month']} 起号"
    verdict += f",随后均赞{g['trend']}(+{g['slope_per_month']}/月)。**"
    L.append(f"> {verdict}\n")
    L.append(f"> 数据范围 `{s['date_range'][0]} → {s['date_range'][1]}`,共抓取本人推文 **{s['total_posts_fetched']}** 条(原创 {s['originals']} / 回复 {s['replies']})。\n")

    # 速览卡片
    L.append("## 📊 速览\n")
    L.append("| 指标 | 数值 |")
    L.append("|---|---|")
    L.append(f"| 当前粉丝 | {fmt(p.get('followersCount'))} |")
    L.append(f"| 账号总推文 | {fmt(p.get('statusesCount'))} |")
    L.append(f"| 注册时间 | {s.get('registered','?')} |")
    L.append(f"| 起号拐点 | **{s.get('inflection_month','?')}** |")
    L.append(f"| 休眠期 | {s.get('dormancy_months','?')} 个月 |")
    L.append(f"| 原创 : 回复 | 1 : {rs['reply_to_original_ratio']} |")
    L.append(f"| 增长趋势 | {g['trend']}(均赞 +{g['slope_per_month']}/月) |")
    L.append(f"| 原创平均字数 | {fm['avg_len']} |\n")

    # 起号时间线叙事
    L.append("## ⏳ 起号时间线\n")
    if s.get("dormancy_months") and s["dormancy_months"] >= 2:
        L.append(f"1. **休眠期**:{s['registered']} 注册,但前 {s['dormancy_months']} 个月几乎零产出——账号是「先占位、后启动」。")
    L.append(f"2. **起号拐点**:**{s['inflection_month']}** 突然放量,当月活动量见下表,从此进入高频发布节奏。")
    L.append(f"3. **增长期**:原创均赞从起号初期稳步抬升,整体呈「{g['trend']}」。\n")

    # 增长曲线
    L.append("## 📈 增长曲线\n")
    if has_svg:
        L.append("![growth](growth.svg)\n")
    L.append("| 月份 | 原创 | 回复 | 原创均赞 | 原创均浏览 | 均收藏 | 互动率% |")
    L.append("|---|---|---|---|---|---|---|")
    for m in a["monthly"]:
        if m["total_activity"] == 0:
            continue
        mark = " 🚀" if m["month"] == s.get("inflection_month") else ""
        L.append(f"| {m['month']}{mark} | {m['originals']} | {m['replies']} | {fmt(m['avg_likes'])} | {fmt(m['avg_views'])} | {fmt(m['avg_bookmarks'])} | {m['engagement_rate']} |")
    L.append("")

    # 内容支柱
    L.append("## 🧱 内容支柱(高频主题)\n")
    pil = a["content_pillars"][:15]
    vmax = pil[0]["posts"] if pil else 1
    L.append("```")
    for it in pil:
        L.append(f"{it['term']:<10} {bar(it['posts'], vmax)} {it['posts']}")
    L.append("```\n")

    # 格式打法
    L.append("## 🎨 格式打法\n")
    L.append(f"- 原创共 **{fm['originals']}** 条:带图/视频 **{fm['with_media']}** · 纯文字 **{fm['pure_text']}** · 带链接 {fm['with_link']} · 含视频 {fm['with_video']}")
    L.append(f"- 平均字数 **{fm['avg_len']}**,其中超 280 字的长推 **{fm['long_posts_280plus']}** 条(长内容占比 {round(100*fm['long_posts_280plus']/max(fm['originals'],1))}%)")
    L.append(f"- 语言分布:{fm['lang_mix']}\n")

    # 发布节奏
    L.append("## ⏰ 发布节奏\n")
    wd = cad["by_weekday"]
    L.append("| " + " | ".join(wd.keys()) + " |")
    L.append("|" + "---|" * len(wd))
    L.append("| " + " | ".join(str(v) for v in wd.values()) + " |")
    L.append(f"\n最活跃时段(UTC):**{cad['peak_hour_utc']} 点**(北京时间约 {(cad['peak_hour_utc']+8)%24} 点)\n")

    # 回复打法
    L.append("## 💬 回复打法(评论区蹲守)\n")
    L.append(f"- 回复 / 原创 = **1 : {rs['reply_to_original_ratio']}** —— ")
    L.append("  " + ("**极度依赖回复涨粉**(典型「大V评论区蹲守」起号法)。" if rs['reply_to_original_ratio'] >= 2 else "回复与原创较均衡。"))
    L.append(f"- 其中续写自己(发 thread)**{rs['self_replies_threadbuilding']}** 次,蹲守他人 **{rs['external_replies']}** 次。")
    if rs["top_reply_targets"]:
        L.append(f"- **重点蹲守对象 Top 10**:")
        L.append("\n| 账号 | 回复次数 |\n|---|---|")
        for t in rs["top_reply_targets"][:10]:
            L.append(f"| @{t['account']} | {t['times']} |")
    L.append("")

    # 爆款解剖
    L.append("## 🔥 爆款解剖(Top 12)\n")
    L.append("| 日期 | ❤赞 | 👀浏览 | 🔖收藏 | 钩子(首行) |")
    L.append("|---|---|---|---|---|")
    for b in a["breakouts"][:12]:
        hook = b["hook"].replace("|", "/")
        L.append(f"| {b['date']} | {fmt(b['likes'])} | {fmt(b['views'])} | {fmt(b['bookmarks'])} | {hook} |")
    L.append("")

    # 钩子公式
    if a.get("hooks"):
        L.append("## 🪝 爆款钩子公式(Top60 高赞帖首行模式)\n")
        for h in a["hooks"]:
            L.append(f"- **{h['pattern']}** × {h['count']}")
        L.append("")

    # 复刻清单
    L.append("## ✅ 复刻清单(可抄作业)\n")
    top_pillars = "、".join(it["term"] for it in a["content_pillars"][:5])
    top_hook = a["hooks"][0]["pattern"] if a.get("hooks") else "亲历分享"
    L.append(f"1. **选题锁定**:主攻 `{top_pillars}` 这类高频主题,别发散。")
    L.append(f"2. **钩子模板**:首行优先用「{top_hook}」式开头,这是该账号爆款最密集的开法。")
    L.append(f"3. **节奏**:维持每月 ~{max(m['originals'] for m in a['monthly'])} 条原创的高频,起号期靠量铺开。")
    L.append(f"4. **回复打法**:原创每发 1 条,配 ~{int(rs['reply_to_original_ratio'])} 条回复,蹲守同赛道活跃账号的评论区导流。")
    L.append(f"5. **格式**:{round(100*fm['with_media']/max(fm['originals'],1))}% 的原创带图/视频,长图文(>280字)是收藏利器。")
    L.append("")
    L.append("---\n*由 [x-account-teardown](https://github.com/) 自动生成 · 数据来自 X 公开接口*")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="analysis.json 或导出目录")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--title", default="")
    args = ap.parse_args()
    src = Path(args.source)
    apath = src if src.is_file() else src / "analysis.json"
    a = json.loads(apath.read_text(encoding="utf-8"))
    out_dir = Path(args.out_dir) if args.out_dir else apath.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    svg_path = out_dir / "growth.svg"
    svg_growth(a["monthly"], svg_path)
    md = build_md(a, args.title, has_svg=True)
    md_path = out_dir / "REPORT.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"[report] -> {md_path}")
    print(f"[report] -> {svg_path}")


if __name__ == "__main__":
    main()
