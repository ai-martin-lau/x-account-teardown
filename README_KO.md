<div align="center">

<a href="README.md">简体中文</a> · <a href="README_EN.md">English</a> · <a href="README_JA.md">日本語</a> · <a href="README_KO.md">한국어</a> · <a href="README_ES.md">Español</a>

# 🔬 x-account-teardown

**임의의 X(트위터) 계정을 "데이터 수준에서 해부"하기**

`@handle` 입력 → 모든 트윗 내보내기 → 그 계정이 0에서 어떻게 성장했는지 재구성

</div>

---

또 하나의 트윗 스크레이퍼가 아닙니다. 훨씬 더 값진 질문에 답합니다.

> **이 대형 계정은 도대체 0에서 어떻게 성장했는가? 콘텐츠·발행 빈도·전술은 무엇이며, 어떻게 따라 할 수 있는가?**

계정의 모든 트윗을 시간순으로 펼쳐 성장 궤적을 역설계합니다. **휴면기 → 성장 변곡점 → 콘텐츠 기둥 → 발행 리듬 → 답글 전략 → 바이럴 후크 공식 → 성장 곡선**. 마지막에는 바로 가져다 쓸 수 있는 "베껴 쓰기용" 리포트를 출력합니다.

## 📈 샘플(14개월 만에 팔로워 2만 명을 달성한 실제 AI 분야 크리에이터)

전체 샘플 리포트는 [`assets/sample/REPORT.md`](assets/sample/REPORT.md) 참조. 한눈에 보기: 2025년 내내 휴면, 2026년 1월에 갑자기 시작(한 달에 오리지널 62 + 답글 420), 이후 평균 좋아요가 꾸준히 상승.

리포트에서 볼 수 있는 것:
- **성장 타임라인** — 가입 후 10개월 휴면하다가 한 번에 올인
- **콘텐츠 기둥** — `영상 / Claude / Codex / 도구 / 모델 / 학습` 으로 순수 AI 도구 노선
- **답글 전략** — 오리지널의 5배에 달하는 답글. 상위 계정의 답글난에 상주하며 콜드 스타트(상주 대상 Top20 포함)
- **바이럴 후크 공식** — 좋아요 상위 60개 중 "1인칭·직접 경험" ×31, "친절한 단계별 튜토리얼"·"무료·공짜" 후크가 최다
- **베껴 쓰기 체크리스트** — 바로 실행 가능한 5가지

## ✨ 무엇이 다른가

| | 일반 스크레이퍼 | x-account-teardown |
|---|---|---|
| 인증 | DevTools에서 토큰을 직접 복사 | **로그인된 Chrome에서 쿠키 자동 추출**(httpOnly 포함, 설정 불필요) |
| 3200개 한도 | 벽에 막혀 초기 트윗을 못 가져옴 | **월 단위 검색으로 한도 우회**, 첫 트윗까지 거슬러 올라감 |
| 출력 | JSON 더미 | **해부 리포트 + 성장 곡선 그래프 + 베껴 쓰기 체크리스트** |
| 인사이트 | 없음 | 성장 변곡점·성장 기울기·후크 공식·답글 대상을 자동 검출 |

## 🚀 사용법

이것은 [Claude Code](https://claude.com/claude-code) 스킬입니다. Claude에게 이렇게 말하면 됩니다:

```
@naval 이 계정이 어떻게 성장했는지 분석해줘
```

Claude가 "수집 → 분석 → 리포트" 전 과정을 자동 실행하고 쉬운 말로 해설합니다.

### 수동 실행

```bash
# 1. 설치(Python 3.10+)
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 2. 디버그 포트로 Chrome 실행, x.com 로그인 상태 유지(쿠키 자동 추출용)
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# 3. 파이프라인
.venv/bin/python scripts/acquire.py naval --out out/naval_export
.venv/bin/python scripts/analyze.py out/naval_export
.venv/bin/python scripts/report.py out/naval_export/analysis.json --out-dir out/naval_report
```

디버그 포트가 켜진 Chrome이 없으면 `--cookies 'auth_token=...; ct0=...'` 또는 환경 변수 `X_COOKIES` 사용.

## 🧩 동작 원리

```
acquire.py   twscrape + 쿠키 자동 추출 + 프록시 자동 감지 + 3200 우회 + 작성자 필터
   ↓ all_posts.json / profile.json
analyze.py   변곡점 검출 / 월별 성장 / 콘텐츠 기둥(jieba) / 리듬 / 답글 전략 / 후크 / 바이럴
   ↓ analysis.json
report.py    Markdown 해부 리포트 + 순수 Python 성장 곡선 SVG
   ↓ REPORT.md / growth.svg
```

성장 분석 프레임워크와 기술 세부 사항은 [`references/methodology.md`](references/methodology.md) 참조.

## ⚠️ 참고

- 데이터는 X의 공개 엔드포인트에서 가져오며 공개 트윗과 인게이지먼트만 반영합니다. 팔로워 곡선은 비공개이므로 시간에 따른 평균 좋아요/조회수를 성장 대리 지표로 사용합니다.
- 삭제된 / 팔로워 전용 트윗은 가져올 수 없습니다.
- 일부 지역에서는 x.com 접속에 프록시가 필요합니다(스크립트가 시스템 프록시 재사용 / 로컬 7890 탐색).
- **⚠️ 메인이 아닌 전용 부계정을 사용하세요**: 이 도구는 Chrome에 로그인된 계정의 신원으로 동작하므로, 어뷰즈 대응 리스크는 그 계정에 걸립니다. 위험한 것은 고빈도 대량 수집뿐이며, 가끔 수천 건을 가져오는 정도는 대체로 괜찮습니다.
- 연구 목적으로만 사용하세요. 동일 계정에 대한 고빈도·반복 대량 수집은 피하세요.

## ⭐ 스타 히스토리

[![Star History Chart](https://api.star-history.com/svg?repos=ai-martin-lau/x-account-teardown&type=Date)](https://star-history.com/#ai-martin-lau/x-account-teardown&Date)

## 📄 라이선스

MIT
