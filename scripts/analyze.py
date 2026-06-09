#!/usr/bin/env python3
"""
analyze.py — 把 acquire.py 产出的 all_posts.json 解剖成结构化洞察 analysis.json。

不止统计,而是还原「起号过程」:
  休眠期 → 起号拐点 → 内容支柱 → 发布节奏 → 回复打法 → 爆款解剖 → 增长曲线。

只用标准库;若安装了 jieba 会用它做更好的中文分词(可选)。

用法: python analyze.py <export_dir> [--out analysis.json]
"""
import argparse, json, re, math
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path

try:
    import jieba  # 可选
    _HAS_JIEBA = True
except Exception:
    _HAS_JIEBA = False

STOP = set("的 了 是 我 你 他 她 它 在 也 和 就 都 而 及 与 这 那 有 个 们 把 被 让 给 到 啊 吧 呢 吗 呀 哦 嗯 一个 一下 这个 那个 什么 怎么 可以 自己 不是 没有 就是 还是 这样 因为 所以 但是 如果 已经 一直 真的 现在 知道 觉得 我们 你们 他们 很多 所有 直接 然后 时候 一些 一样 不会 不能 还有 这些 那些 出来 起来 这种 非常 比较 而且 或者 不要 需要 可能 应该 通过 进行 这里 那里 大家 东西 一点 其实 一定 看到 想要 里面 之前 今天 最后 使用 问题 内容 朋友 一次 一篇 一条 一天 这次 多人 the a an to of and or is are be in on at it for you i we my your this that with как".split())
EN_STOP = set("the a an and or to of in on at is are be it for you i we my your this that with as by from will can how what why not but if so just my our get got use using one all out about more your you're it's i'm".split())


_DEFAULTS = {"links": [], "mentions": [], "media_photos": [], "media_videos": 0,
             "hashtags": [], "text": "", "lang": None, "likeCount": 0, "viewCount": 0,
             "bookmarkedCount": 0, "retweetCount": 0, "replyCount": 0, "quoteCount": 0,
             "isReply": False, "isRetweet": False, "isQuote": False, "inReplyToUser": None}


def load(d: Path):
    posts = json.loads((d / "all_posts.json").read_text(encoding="utf-8"))
    for p in posts:  # 兼容旧版导出:补齐缺失字段
        for k, v in _DEFAULTS.items():
            p.setdefault(k, v)
    profile = {}
    if (d / "profile.json").exists():
        profile = json.loads((d / "profile.json").read_text(encoding="utf-8"))
    return posts, profile


def n(x):
    return x or 0


def is_original(p):
    return not p["isReply"] and not p["isRetweet"]


def parse_dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def tokenize(text):
    text = re.sub(r"https?://\S+", " ", text or "")
    text = re.sub(r"[@#]\w+", " ", text)
    toks = []
    # 英文词
    for w in re.findall(r"[A-Za-z][A-Za-z0-9\-\.]{2,}", text):
        wl = w.lower()
        if wl not in EN_STOP and len(wl) >= 3:
            toks.append(wl)
    # 中文
    zh = "".join(re.findall(r"[一-鿿]+", text))
    if _HAS_JIEBA:
        for w in jieba.cut(zh):
            if len(w) >= 2 and w not in STOP:
                toks.append(w)
    else:
        # 退化:2-gram + 3-gram
        for seg in re.findall(r"[一-鿿]{2,}", text):
            for k in (2, 3):
                for i in range(len(seg) - k + 1):
                    g = seg[i:i + k]
                    if g not in STOP:
                        toks.append(g)
    return toks


def monthly(posts):
    m = defaultdict(lambda: {"orig": 0, "reply": 0, "rt": 0, "likes": 0, "views": 0,
                             "bm": 0, "rts": 0, "replies_recv": 0})
    for p in posts:
        key = p["date"][:7]
        if p["isRetweet"]:
            m[key]["rt"] += 1
            continue
        if p["isReply"]:
            m[key]["reply"] += 1
        else:
            m[key]["orig"] += 1
            m[key]["likes"] += n(p["likeCount"])
            m[key]["views"] += n(p["viewCount"])
            m[key]["bm"] += n(p["bookmarkedCount"])
            m[key]["rts"] += n(p["retweetCount"])
            m[key]["replies_recv"] += n(p["replyCount"])
    out = []
    for k in sorted(m):
        d = m[k]
        o = max(d["orig"], 1)
        out.append({
            "month": k, "originals": d["orig"], "replies": d["reply"], "retweets": d["rt"],
            "total_activity": d["orig"] + d["reply"] + d["rt"],
            "avg_likes": round(d["likes"] / o, 1), "avg_views": round(d["views"] / o, 1),
            "avg_bookmarks": round(d["bm"] / o, 1), "avg_retweets": round(d["rts"] / o, 1),
            "sum_likes": d["likes"], "sum_views": d["views"],
            "engagement_rate": round(d["likes"] / d["views"] * 100, 2) if d["views"] else 0,
            "bookmark_rate": round(d["bm"] / d["views"] * 100, 2) if d["views"] else 0,
        })
    return out


def detect_inflection(monthly_rows):
    """找起号拐点:第一次「月活动量」站上全程中位数*1.5,且后续持续高位的那个月。"""
    if not monthly_rows:
        return None
    acts = [r["total_activity"] for r in monthly_rows]
    peak = max(acts) if acts else 0
    thresh = max(peak * 0.2, 15)  # 活动量达到峰值20%或至少15条,视为「认真发」
    for i, r in enumerate(monthly_rows):
        if r["total_activity"] >= thresh:
            # 确认后面不是昙花一现
            tail = monthly_rows[i:i + 3]
            if sum(x["total_activity"] for x in tail) / len(tail) >= thresh * 0.6:
                return r["month"]
    return monthly_rows[0]["month"]


def content_pillars(originals, topn=18):
    c = Counter()
    for p in originals:
        for t in set(tokenize(p["text"])):  # set:一条内多次不重复计
            c[t] += 1
    return [{"term": t, "posts": cnt} for t, cnt in c.most_common(topn)]


def format_mix(posts):
    orig = [p for p in posts if is_original(p)]
    has_media = lambda p: p["media_photos"] or p["media_videos"]
    has_link = lambda p: p["links"]
    lens = [len(p["text"] or "") for p in orig]
    # 自答 thread 检测:连续 self-reply
    thread_starters = sum(1 for p in orig if "🧵" in (p["text"] or "") or re.search(r"(1/|^\d+\.)", (p["text"] or "")[:6]))
    return {
        "originals": len(orig),
        "with_media": sum(1 for p in orig if has_media(p)),
        "with_link": sum(1 for p in orig if has_link(p)),
        "with_video": sum(1 for p in orig if p["media_videos"]),
        "pure_text": sum(1 for p in orig if not has_media(p) and not has_link(p)),
        "avg_len": round(sum(lens) / len(lens), 1) if lens else 0,
        "long_posts_280plus": sum(1 for L in lens if L > 280),
        "thread_like": thread_starters,
        "lang_mix": dict(Counter(p["lang"] for p in orig).most_common(5)),
    }


def cadence(posts):
    wd = Counter()
    hr = Counter()
    for p in posts:
        d = parse_dt(p["date"])
        if d:
            wd[d.weekday()] += 1  # 0=Mon (UTC)
            hr[d.hour] += 1
    days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return {
        "by_weekday": {days[k]: wd.get(k, 0) for k in range(7)},
        "by_hour_utc": {str(h): hr.get(h, 0) for h in range(24)},
        "peak_hour_utc": max(hr, key=hr.get) if hr else None,
    }


def reply_strategy(posts, self_handle):
    replies = [p for p in posts if p["isReply"]]
    self_replies = [p for p in replies if p["inReplyToUser"] == self_handle]   # 续写自己=发 thread
    ext = [p for p in replies if p["inReplyToUser"] and p["inReplyToUser"] != self_handle]
    targets = Counter(p["inReplyToUser"] for p in ext)
    return {
        "total_replies": len(replies),
        "self_replies_threadbuilding": len(self_replies),
        "external_replies": len(ext),
        "top_reply_targets": [{"account": a, "times": c} for a, c in targets.most_common(20)],
        "reply_to_original_ratio": round(len(replies) / max(len([p for p in posts if is_original(p)]), 1), 2),
    }


def breakouts(originals, topn=15):
    def score(p):
        return n(p["likeCount"]) + n(p["bookmarkedCount"]) * 3 + n(p["retweetCount"]) * 2
    top = sorted(originals, key=score, reverse=True)[:topn]
    rows = []
    for p in top:
        txt = (p["text"] or "").strip()
        has_media = bool(p["media_photos"] or p["media_videos"])
        clean = re.sub(r"https?://t\.co/\S+", "", txt).strip()
        first = clean.split("\n")[0].strip() if clean else ""
        if not first:
            first = "[图文/视频]" if has_media else "[长文/链接]"
        rows.append({
            "date": p["date"][:10], "likes": n(p["likeCount"]), "views": n(p["viewCount"]),
            "bookmarks": n(p["bookmarkedCount"]), "retweets": n(p["retweetCount"]),
            "url": p["url"], "hook": first[:60], "text": clean[:280], "has_media": has_media,
        })
    return rows


def hooks(originals):
    """爆款首行模式:统计高赞帖第一句的开头句式。"""
    top = sorted(originals, key=lambda p: n(p["likeCount"]), reverse=True)[:60]
    patterns = Counter()
    for p in top:
        first = (p["text"] or "").strip().split("\n")[0]
        if not first:
            continue
        if re.search(r"\d", first[:8]): patterns["数字开头(榜单/步骤/金额)"] += 1
        if any(w in first for w in ["保姆级", "全流程", "教程", "手把手", "教你"]): patterns["保姆级/教程承诺"] += 1
        if any(w in first for w in ["免费", "白嫖", "0成本", "赠金", "薅"]): patterns["免费/白嫖钩子"] += 1
        if any(w in first for w in ["我", "自己", "刚", "今天", "分享"]): patterns["第一人称/亲历"] += 1
        if any(w in first for w in ["竟然", "太", "震惊", "夸张", "牛", "炸", "强"]): patterns["情绪放大"] += 1
        if "?" in first or "？" in first or any(w in first for w in ["有谁", "还有人", "为什么"]): patterns["提问/挑衅"] += 1
        if any(w in first for w in ["预测", "趋势", "未来", "时代", "判断"]): patterns["趋势/观点"] += 1
    return [{"pattern": k, "count": v} for k, v in patterns.most_common()]


def growth_trend(monthly_rows):
    """对均赞做简单线性拟合,判断增长斜率。"""
    pts = [(i, r["avg_likes"]) for i, r in enumerate(monthly_rows) if r["originals"] >= 3]
    if len(pts) < 3:
        return {"slope_per_month": 0, "trend": "数据不足"}
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
    denom = sum((x - mx) ** 2 for x in xs) or 1
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom
    trend = "强劲上升" if slope > 15 else "稳步上升" if slope > 3 else "平台期" if slope > -3 else "下滑"
    return {"slope_per_month": round(slope, 1), "trend": trend}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export_dir")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    d = Path(args.export_dir)
    posts, profile = load(d)
    originals = [p for p in posts if is_original(p)]

    mrows = monthly(posts)
    inflect = detect_inflection(mrows)
    first_active = mrows[0]["month"] if mrows else None
    created = (profile.get("created") or "")[:7]
    # 休眠期:注册到起号拐点
    dormancy = None
    if created and inflect:
        try:
            c = datetime.strptime(created, "%Y-%m"); f = datetime.strptime(inflect, "%Y-%m")
            dormancy = (f.year - c.year) * 12 + (f.month - c.month)
        except Exception:
            pass

    analysis = {
        "profile": profile,
        "summary": {
            "total_posts_fetched": len(posts),
            "originals": len(originals),
            "replies": len([p for p in posts if p["isReply"]]),
            "retweets": len([p for p in posts if p["isRetweet"]]),
            "date_range": [posts[0]["date"][:10], posts[-1]["date"][:10]] if posts else None,
            "registered": created,
            "inflection_month": inflect,
            "dormancy_months": dormancy,
            "first_activity_month": first_active,
        },
        "monthly": mrows,
        "growth_trend": growth_trend(mrows),
        "format_mix": format_mix(posts),
        "content_pillars": content_pillars(originals),
        "cadence": cadence(posts),
        "reply_strategy": reply_strategy(posts, profile.get("username")),
        "hooks": hooks(originals),
        "breakouts": breakouts(originals),
    }
    out = Path(args.out) if args.out else d / "analysis.json"
    out.write_text(json.dumps(analysis, ensure_ascii=False, indent=1), encoding="utf-8")
    s = analysis["summary"]
    print(f"[analyze] 原创 {s['originals']} / 回复 {s['replies']} | 注册 {s['registered']} "
          f"| 起号拐点 {s['inflection_month']} | 休眠 {s['dormancy_months']} 个月")
    print(f"          增长趋势:{analysis['growth_trend']['trend']} "
          f"(均赞 +{analysis['growth_trend']['slope_per_month']}/月)")
    print(f"          -> {out}")


if __name__ == "__main__":
    main()
