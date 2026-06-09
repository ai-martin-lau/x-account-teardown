---
name: x-account-teardown
description: 对任意 X(Twitter)账号做「数据级起号解剖」。输入一个 handle/链接,自动导出该账号全部推文(原创+回复+互动数据),还原它的起号全过程——休眠期、起号拐点、内容支柱、发布节奏、回复打法、爆款钩子公式、增长曲线,产出一份可直接交付/可抄作业的中文 Markdown 报告(含增长曲线图)。触发词:分析X账号、分析推特账号、起号分析、起号过程、研究大V、拆解这个账号、导出某人的推文、export tweets、X account analysis、twitter teardown、这个号怎么起来的、扒一下这个博主、复盘某账号、analyze @某人。也适用于只给一个 @handle 或 x.com 链接并说「研究/拆解/扒一下」。
---

# X 账号起号解剖器

把任意一个 X 账号变成一份「起号解剖报告」:**它怎么从 0 做起来的,内容/节奏/打法是什么,怎么抄。**

```
拿到 handle → 采集全量推文 → 解剖分析 → 生成报告(Markdown + 增长曲线图)
```

最终产物:一份 `REPORT.md`(GitHub 原生可读)+ `growth.svg` 增长曲线,放在用户指定的产出目录。

---

## 第 0 步:确认输入

从用户输入里提取 **handle**(去掉 @ 和 URL 前缀,`https://x.com/foo` → `foo`)。
若用户没说要分析谁,问一句「分析哪个账号?给我 @handle 或主页链接」即可,不要长篇确认。

可选追问(能推断就别问):是否需要包含回复(默认包含,回复是起号研究的关键信号)。

---

## 第 1 步:环境自检(只在首次/报错时做)

脚本目录:`scripts/`。需要 **Python 3.10+** 和 **twscrape**。

```bash
# 找一个 3.10+ 的 python(系统自带常是 3.9,不够)
which python3.11 python3.12 python3.13 2>/dev/null

# 在产出目录建独立 venv 并装依赖(只需一次)
<py3.10+> -m venv <产出目录>/.venv
<产出目录>/.venv/bin/pip install -q twscrape jieba
```

> jieba 可选,但强烈建议装——中文内容支柱提取靠它,不装会退化成 n-gram 噪音。

**登录态**:`acquire.py` 会自动从「带调试端口运行的 Chrome」抠 cookie(连 httpOnly 的 auth_token 都能拿,无需 API key、无需手动贴 token)。
前提:用户的 Chrome 是用 `--remote-debugging-port=9222` 启动且已登录 x.com(本机 web-access skill 的 CDP 模式即满足)。
如果没有,提示用户三选一(脚本报错信息里有):带调试端口启动 Chrome / 传 `--cookies` / 设 `X_COOKIES`。

**网络**:脚本自动复用系统 `HTTPS_PROXY` 或探测本地代理(7890 等)。x.com 直连不通的地区必须挂代理(国内常态)。

---

## 第 2 步:采集(acquire.py)

```bash
<venv>/bin/python scripts/acquire.py <handle> --out <产出目录>/<handle>_export
```

- 账号推文 **< 3000 条** → 走时间线接口(user_tweets + user_tweets_and_replies),一次拉全。
- 账号推文 **> 3000 条** → 自动切「**按月份搜索**」逐窗拼接,**绕过 X 的 3200 条时间线上限**(这是关键设计:时间线接口本身有 ~3200 上限,但 `from:handle since: until:` 搜索按月开窗就能无限回溯)。也可加 `--force-search` 手动强制。
- 产物:`<handle>_export/all_posts.json`(已做作者过滤,剔除「他回复过的大V原帖」污染)+ `profile.json`。

> 单账号会被 X 限流,大号采集可能要等几分钟(twscrape 会自动等待重试)。这是正常现象,耐心等它跑完,不要中断。
> 想加速可在 twscrape 里加多个账号 cookie。

---

## 第 3 步:分析(analyze.py)

```bash
<venv>/bin/python scripts/analyze.py <产出目录>/<handle>_export
```

产出 `analysis.json`,包含:
- **summary**:注册时间、起号拐点(自动检测)、休眠期月数、原创/回复/转推数
- **monthly**:逐月原创量/回复量/均赞/均浏览/均收藏/互动率
- **growth_trend**:对均赞做线性拟合,判断「强劲上升/稳步上升/平台期/下滑」
- **content_pillars**:高频主题词(jieba 分词)
- **format_mix**:图文/纯文字/长推/视频占比、平均字数、语言分布
- **cadence**:按星期/小时的发布节奏、最活跃时段
- **reply_strategy**:回复:原创比、自我续写(thread)vs 蹲守他人、重点蹲守对象 Top20
- **hooks**:Top60 高赞帖首行的钩子句式分布(数字/保姆级/白嫖/亲历/情绪/提问/趋势)
- **breakouts**:爆款 Top15(综合赞+收藏×3+转发×2 排序)

---

## 第 4 步:出报告(report.py)

```bash
<venv>/bin/python scripts/report.py <产出目录>/<handle>_export/analysis.json --out-dir <产出目录>/<handle>_report
```

产出 `REPORT.md` + `growth.svg`。报告结构:速览 → 起号时间线 → 增长曲线 → 内容支柱 → 格式打法 → 发布节奏 → 回复打法 → 爆款解剖 → 钩子公式 → **复刻清单(可抄作业)**。

---

## 第 5 步:解读(这是 skill 的灵魂)

脚本给的是「骨架数据」。读完 `analysis.json` 后,**你要在回复里加一段人话解读**,而不是只把报告丢给用户:
- 指出这个账号起号的**关键动作**(例:休眠 10 个月→某月突然单月 60 原创+400 回复,典型「攒够弹药再all-in」)。
- 找出**最反常识的一招**(例:回复量是原创 5 倍,靠蹲守头部账号评论区导流)。
- 给用户**一句可执行的建议**:如果他想复刻,第一步该做什么。

把 `REPORT.md` 的路径告诉用户,并附上你的解读。

---

## 参考资料(references/)

- `references/methodology.md` —— 起号分析框架、各指标怎么解读、3200 上限与 cookie 抠取的技术细节、已知坑。
读 methodology 再动手能避免重复踩坑。

## 注意
- 数据来自 X 公开接口,只反映**公开可见**的推文与互动数;粉丝增长曲线 X 不公开,本 skill 用「均赞/均浏览随时间变化」作为增长代理指标。
- 已删除的推文拿不到;被设为仅关注者可见的内容拿不到。
- 别对同一大号短时间反复全量采集,容易触发风控。
