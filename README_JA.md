<p align="center">
  <a href="README.md">English</a> · <a href="README_ZH.md">简体中文</a> · <a href="README_JA.md">日本語</a> · <a href="README_KO.md">한국어</a> · <a href="README_ES.md">Español</a>
</p>

<div align="center">

# 🔬 x-account-teardown

**任意の X(Twitter)アカウントを「データレベルで解剖」する**

`@handle` を入力 → 全ツイートを取得 → そのアカウントがゼロからどう伸びたかを再構築

</div>

---

ただのツイート取得ツールではありません。もっと価値のある問いに答えます。

> **この有名アカウントは、ゼロからどうやって伸びたのか？コンテンツ・投稿頻度・戦術は何か。どうすれば真似できるのか。**

アカウントの全ツイートを時系列に並べ、その成長の軌跡を逆算します。**休眠期 → 立ち上がりの転換点 → コンテンツの柱 → 投稿リズム → リプライ戦術 → バズるフックの型 → 成長曲線**。最終的に、そのまま使える「お手本」レポートを出力します。

## 📈 サンプル(14か月で2万フォロワーに達した、実在のAI系クリエイター)

サンプルレポート全文は [`assets/sample/REPORT.md`](assets/sample/REPORT.md) を参照。ひと目で分かること：2025年はほぼ休眠、2026年1月に突然始動(単月で オリジナル62 + リプライ420)、以降は平均いいね数が着実に上昇。

レポートで分かること：
- **成長タイムライン** — 登録後10か月休眠してから一気に本格始動
- **コンテンツの柱** — `動画 / Claude / Codex / ツール / モデル / 学習` という純粋なAIツール路線
- **リプライ戦術** — オリジナルの5倍のリプライ。上位アカウントのリプ欄に張り付いてコールドスタート(蹲守対象 Top20 付き)
- **バズるフックの型** — 高評価上位60件のうち「一人称・実体験」×31、「手取り足取りのチュートリアル」「無料・タダ取り」フックが最多
- **真似するチェックリスト** — そのまま実行できる5項目

## ✨ 何が違うのか

| | 普通のスクレイパー | x-account-teardown |
|---|---|---|
| 認証 | DevToolsからトークンを手作業でコピー | **ログイン中のChromeからCookieを自動取得**(httpOnlyも含む、設定不要) |
| 3200件の上限 | 壁にぶつかり初期ツイートが取れない | **月単位の検索で上限を回避**し、最初の1件まで遡る |
| 出力 | JSONの山 | **解剖レポート + 成長曲線グラフ + 真似用チェックリスト** |
| 洞察 | なし | 立ち上がりの転換点・成長の傾き・フックの型・リプライ先を自動検出 |

## 🚀 使い方

これは [Claude Code](https://claude.com/claude-code) のスキルです。Claudeにこう伝えるだけ：

```
@naval がどうやってアカウントを伸ばしたか分析して
```

Claudeが「取得 → 分析 → レポート」を自動で実行し、平易な言葉で解説します。

### 手動で実行する

```bash
# 1. インストール(Python 3.10+)
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 2. デバッグポート付きでChromeを起動し、x.com にログインしておく(Cookie自動取得用)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# 3. パイプライン
.venv/bin/python scripts/acquire.py naval --out out/naval_export
.venv/bin/python scripts/analyze.py out/naval_export
.venv/bin/python scripts/report.py out/naval_export/analysis.json --out-dir out/naval_report
```

デバッグポート付きのChromeがない場合は `--cookies 'auth_token=...; ct0=...'` または環境変数 `X_COOKIES` を使用。

## 🧩 仕組み

```
acquire.py   twscrape + Cookie自動取得 + プロキシ自動判定 + 3200回避 + 著者フィルタ
   ↓ all_posts.json / profile.json
analyze.py   転換点検出 / 月次成長 / コンテンツの柱(jieba) / リズム / リプライ戦術 / フック / バズ
   ↓ analysis.json
report.py    Markdown解剖レポート + 純Python製の成長曲線SVG
   ↓ REPORT.md / growth.svg
```

成長分析のフレームワークと技術的な詳細は [`references/methodology.md`](references/methodology.md) を参照。

## ⚠️ 注意

- データはXの公開エンドポイント由来で、公開ツイートとエンゲージメントのみを反映します。フォロワー曲線は非公開のため、本ツールは時系列の平均いいね/表示数を成長の代理指標として使います。
- 削除済み / フォロワー限定のツイートは取得できません。
- 地域によっては x.com への接続にプロキシが必要です(スクリプトがシステムプロキシを再利用 / ローカルの7890を探索)。
- **⚠️ メインではなく専用のサブ垢を使うこと**：本ツールはChromeにログイン中のアカウントの身元で動作するため、対策上のリスクはそのアカウントにかかります。危険なのは高頻度の大量取得だけで、たまに数千件取る程度なら基本的に問題ありません。
- 研究目的のみ。同一アカウントへの高頻度・反復的な大量取得は避けてください。

## ⭐ スター推移

[![Star History Chart](https://api.star-history.com/svg?repos=ai-martin-lau/x-account-teardown&type=Date)](https://star-history.com/#ai-martin-lau/x-account-teardown&Date)

## 📄 ライセンス

MIT
