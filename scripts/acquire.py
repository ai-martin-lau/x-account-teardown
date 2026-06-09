#!/usr/bin/env python3
"""
acquire.py — 把任意 X(Twitter)账号的全部推文拉成结构化 JSON。

亮点:
- 登录态零配置:自动从你「正在跑调试端口的 Chrome」里抠 auth_token/ct0,无需 API key、无需贴 token。
- 代理自适应:自动复用系统 HTTPS_PROXY,或探测本地 ClashX/Mihomo(7890)。
- 突破 3200 上限:账号推文 < 3000 走时间线接口;> 3000 自动切「按月份搜索」逐窗拼接,理论无上限。
- 作者过滤:剔除「他回复过的大V原帖」等对话上下文污染,只留目标本人的推。

用法:
    python acquire.py <handle> [--out DIR] [--proxy URL] [--cookies STR|PATH]
                       [--no-replies] [--cdp-port 9222]

依赖:twscrape (pip)、node(仅当需要自动抠 cookie 时);Python 3.10+。
"""
import argparse, asyncio, json, os, subprocess, sys, datetime as dt
from pathlib import Path

try:
    from twscrape import API, gather
except ImportError:
    sys.exit("缺少 twscrape:请先 `pip install twscrape`(需 Python 3.10+)")

HERE = Path(__file__).resolve().parent


# ---------- 登录态:从运行中的 Chrome 抠 cookie ----------
def resolve_cookies(arg_cookies: str | None, cdp_port: int) -> str:
    # 1) 显式传入(字符串或文件路径)
    if arg_cookies:
        p = Path(arg_cookies)
        if p.exists():
            txt = p.read_text(encoding="utf-8").strip()
            try:
                return json.loads(txt).get("cookieHeader", txt)
            except Exception:
                return txt
        return arg_cookies
    # 2) 环境变量
    if os.environ.get("X_COOKIES"):
        return os.environ["X_COOKIES"]
    # 3) 缓存文件
    cache = Path("/tmp/xcookies.json")
    if cache.exists():
        try:
            d = json.loads(cache.read_text())
            if d.get("auth_token") and d.get("ct0"):
                return d["cookieHeader"]
        except Exception:
            pass
    # 4) 现场从 Chrome 调试端口抠
    node = _which("node")
    script = HERE / "get_cookies.mjs"
    if node and script.exists():
        print(f"[cookies] 从 Chrome 调试端口 :{cdp_port} 抠取登录态…")
        env = {**os.environ, "CDP_PORT": str(cdp_port)}
        r = subprocess.run([node, str(script)], capture_output=True, text=True, env=env)
        if r.returncode == 0 and r.stdout.strip():
            d = json.loads(r.stdout)
            if d.get("auth_token") and d.get("ct0"):
                cache.write_text(r.stdout)
                return d["cookieHeader"]
        print("[cookies] 自动抠取失败:", (r.stderr or "").strip()[:200])
    sys.exit(
        "拿不到登录态。三选一:\n"
        "  a) 用带调试端口的 Chrome 登录 x.com:\n"
        "     /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222\n"
        "  b) 传 --cookies 'auth_token=...; ct0=...'\n"
        "  c) 设环境变量 X_COOKIES"
    )


def _which(cmd: str):
    r = subprocess.run(["which", cmd], capture_output=True, text=True)
    return r.stdout.strip() or None


# ---------- 代理自适应 ----------
def resolve_proxy(arg_proxy: str | None) -> str | None:
    if arg_proxy:
        return None if arg_proxy.lower() in ("none", "off", "") else arg_proxy
    for k in ("HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
        if os.environ.get(k):
            return os.environ[k]
    # 探测常见本地代理
    import socket
    for port in (7890, 7891, 1087, 1080, 8889):
        s = socket.socket()
        s.settimeout(0.3)
        try:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return f"http://127.0.0.1:{port}"
        finally:
            s.close()
    return None


# ---------- 归一化一行 ----------
def tw_row(t):
    return {
        "id": str(t.id),
        "author": t.user.username if t.user else None,
        "author_id": str(t.user.id) if t.user else None,
        "date": t.date.isoformat() if t.date else None,
        "url": t.url,
        "text": t.rawContent,
        "replyCount": t.replyCount,
        "retweetCount": t.retweetCount,
        "likeCount": t.likeCount,
        "quoteCount": t.quoteCount,
        "bookmarkedCount": getattr(t, "bookmarkedCount", None),
        "viewCount": t.viewCount,
        "lang": t.lang,
        "isReply": t.inReplyToTweetId is not None,
        "inReplyToUser": (t.inReplyToUser.username if t.inReplyToUser else None),
        "isRetweet": t.retweetedTweet is not None,
        "isQuote": t.quotedTweet is not None,
        "hashtags": t.hashtags,
        "mentions": [u.username for u in (t.mentionedUsers or [])],
        "media_photos": [p.url for p in (t.media.photos if t.media else [])],
        "media_videos": len(t.media.videos) if t.media else 0,
        "links": [l.url for l in (t.links or [])],
    }


def month_windows(start: dt.date, end: dt.date):
    cur = dt.date(start.year, start.month, 1)
    while cur <= end:
        nxt = dt.date(cur.year + (cur.month == 12), (cur.month % 12) + 1, 1)
        yield cur, nxt
        cur = nxt


async def fetch_by_timeline(api, uid, with_replies):
    print("[fetch] 策略=时间线接口(账号 <3000 条)")
    rows = await gather(api.user_tweets(uid, limit=10000))
    print(f"  user_tweets: {len(rows)}")
    if with_replies:
        rr = await gather(api.user_tweets_and_replies(uid, limit=10000))
        print(f"  user_tweets_and_replies: {len(rr)}")
        rows += rr
    return rows


async def fetch_by_search(api, handle, created, with_replies):
    print("[fetch] 策略=按月搜索拼接(账号 >3000 条,绕过 3200 上限)")
    start = created.date()
    end = dt.date.today()
    rows = []
    base = f"from:{handle}" + ("" if with_replies else " -filter:replies")
    for a, b in month_windows(start, end):
        q = f"{base} since:{a.isoformat()} until:{b.isoformat()}"
        chunk = await gather(api.search(q, limit=5000))
        if chunk:
            print(f"  {a.isoformat()}: +{len(chunk)}")
        rows += chunk
    return rows


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("handle")
    ap.add_argument("--out", default=None)
    ap.add_argument("--proxy", default=None)
    ap.add_argument("--cookies", default=None)
    ap.add_argument("--no-replies", action="store_true")
    ap.add_argument("--cdp-port", type=int, default=9222)
    ap.add_argument("--force-search", action="store_true", help="强制走按月搜索策略")
    args = ap.parse_args()

    handle = args.handle.lstrip("@")
    out_dir = Path(args.out) if args.out else Path.cwd() / f"{handle}_export"
    out_dir.mkdir(parents=True, exist_ok=True)

    cookies = resolve_cookies(args.cookies, args.cdp_port)
    proxy = resolve_proxy(args.proxy)
    print(f"[proxy] {proxy or '直连'}")

    db = str(out_dir / "accounts.db")
    api = API(db, proxy=proxy)
    await api.pool.add_account("teardown_sess", "x", "x@example.com", "x",
                               cookies=cookies, proxy=proxy)
    await api.pool.set_active("teardown_sess", True)

    user = await api.user_by_login(handle)
    if not user:
        sys.exit(f"找不到账号 @{handle}")
    uid = user.id
    profile = {
        "username": user.username, "id": str(uid), "displayname": user.displayname,
        "rawDescription": user.rawDescription, "followersCount": user.followersCount,
        "friendsCount": user.friendsCount, "statusesCount": user.statusesCount,
        "favouritesCount": user.favouritesCount, "mediaCount": user.mediaCount,
        "created": user.created.isoformat() if user.created else None,
        "location": user.location, "verified": user.verified, "blue": getattr(user, "blue", None),
        "profileImageUrl": user.profileImageUrl,
    }
    print(f"[user] @{user.username} | 粉丝 {user.followersCount} | 推文 {user.statusesCount} "
          f"| 注册 {profile['created'][:10] if profile['created'] else '?'}")

    with_replies = not args.no_replies
    if args.force_search or user.statusesCount > 3000:
        raw = await fetch_by_search(api, handle, user.created, with_replies)
    else:
        raw = await fetch_by_timeline(api, uid, with_replies)

    # 去重 + 作者过滤
    merged = {}
    for t in raw:
        merged[str(t.id)] = t
    rows = [tw_row(t) for t in merged.values()]
    rows = [r for r in rows if r["author_id"] == str(uid)]
    rows.sort(key=lambda r: r["date"] or "")

    (out_dir / "profile.json").write_text(json.dumps(profile, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "all_posts.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    n_orig = len([r for r in rows if not r["isReply"] and not r["isRetweet"]])
    print(f"[done] 本人推文 {len(rows)} 条(原创 {n_orig} / 回复 {len(rows)-n_orig}）")
    if rows:
        print(f"       时间跨度 {rows[0]['date'][:10]} → {rows[-1]['date'][:10]}")
    print(f"       -> {out_dir/'all_posts.json'}")
    print(f"       -> {out_dir/'profile.json'}")


if __name__ == "__main__":
    asyncio.run(main())
