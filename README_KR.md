# ⚡ MCP Vault (`mcpv`)

> **The Ultimate Performance Booster for AI Agents**  
> _"시스템 렉은 99% 줄이고, 로딩은 없애고, 토큰 비용은 1/10로."_

<div align="center">

![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-F7CA3F.svg?style=flat-square&logo=python&logoColor=black)
![Platform](https://img.shields.io/badge/OS-Windows-0078D6.svg?style=flat-square&logo=windows&logoColor=white)
![Status](https://img.shields.io/badge/Status-Accelerated-brightgreen.svg?style=flat-square)

</div>

<div align="right">
  <a href="README.md">🇺🇸 English</a> | <a href="README_CN.md">🇨🇳 中文</a> | <a href="README_RU.md">🇷🇺 Русский</a>
</div>

<br>

> [!CAUTION]
> **⚠️ 호환성 주의 (Compatibility Warning)**<br>
> 현재 이 프로젝트는 **Windows** 운영체제와 **Antigravity (안티그래비티)** 에이전트 환경만 지원합니다.<br>
> _(Currently, this project ONLY supports **Windows** and **Antigravity**.)_

<br>

## ❓ 왜 `mcpv` 인가요?

AI 에이전트(Antigravity, Cursor)를 쓰다가 이런 경험 없으신가요?
> *"왜 이렇게 무겁지?"*  
> *"또 멈췄네..."*  
> *"토큰 비용이 왜 이렇게 많이 나와?"*

`mcpv`는 단순한 도구가 아닙니다. 당신의 에이전트를 위한 **터보 엔진**입니다.

<br>

### 🏎️ 압도적인 성능 차이

| 구분 | 😫 `mcpv` 없음 (Before) | ⚡ `mcpv` 장착 (After) | 📈 효과 |
| :--- | :--- | :--- | :--- |
| **속도** | GPU 미사용, UI 버벅임 | **GPU 강제 가속, 쾌적함** | **100배** 체감 향상 |
| **로딩** | 매번 수십 초 대기 | **0.1초 즉시 실행** (Lazy Load) | **대기시간 0초** |
| **비용** | 매번 전체 코드 전송 | **중복 자동 차단** (Smart Cache) | **90%** 절감 |

<br>

---

## ✨ 3가지 핵심 무기

### 1️⃣ Booster Injection (물리적 가속)
**"명령어 한 줄로 하드웨어 봉인 해제"**
- **GPU 강제 활성화**: 숨겨진 렌더링 가속 플래그(`--enable-gpu-rasterization`)를 주입합니다.
- **권한 문제 해결**: 관리자 권한을 해제하여 드래그 앤 드롭 및 UI 버그를 수정하고, `RunAsInvoker`로 성가신 권한 요청(Error 740)을 우회합니다.
- **좀비 프로세스 킬**: 포트를 점유하는 유령 프로세스를 자동으로 청소합니다.

### 2️⃣ Smart Valve (비용 방어)
**"알아서 아껴주는 똑똑한 지갑 지킴이"**
- 에이전트가 습관적으로 요청하는 거대한 문맥 데이터(`repomix`)를 감지합니다.
- **첫 번째 요청: 허용** (전체 문맥 제공).
- **이후 요청: 차단** (10 토큰짜리 **"Already cached"** 메시지 반환).
- 실수로 인한 토큰 폭탄을 원천 봉쇄합니다.

### 3️⃣ Gateway Hijacking (안전한 금고)
**"복잡한 설정은 이제 그만"**
- **루트 경로 고정 (Root Path Locking)**: `mcpv install`을 실행한 위치를 기억하여, 에이전트가 어디에 있든 항상 올바른 프로젝트 루트를 바라보게 합니다. 더 이상 "파일을 찾을 수 없음" 오류로 고생하지 마세요.
- 기존의 복잡한 MCP 설정을 안전한 금고(Vault)로 자동 이전합니다.
- 원본 설정은 `mcp_config.original.json`에 안전하게 백업됩니다.

### 4️⃣ Smart Router (스마트 라우터)
**"모든 도구를 하나로 통합"**
- **통합 인터페이스**: 에이전트는 어떤 서버에 어떤 도구가 있는지 알 필요가 없습니다. 그저 `run_tool(name="...")` 하나로 모든 도구를 실행합니다.
- **자동 교정 (Auto-Correction)**: 에이전트가 오타를 냈거나 서버 이름을 불렀나요? `mcpv`가 알아서 찰떡같이 알아듣고 올바른 도구를 찾아 실행하거나 제안합니다.
- **지연 없는 시동**: 실제로 도구가 필요할 때만 상류 서버와 연결하여 부하를 최소화합니다.

<br>

---

## 📦 설치 방법 (Installation)

이 프로젝트는 **Windows** 환경에 최적화되어 있습니다. 빠르고 깔끔한 설치를 위해 `uv` 사용을 권장합니다.

```powershell
# uv를 사용한 설치 (권장)
uv pip install . --system

# 또는 일반 pip 사용
pip install .
```

패키지 설치 후, 반드시 다음 명령어를 실행하여 Vault를 설정해야 합니다:

```powershell
mcpv install
```

<br>

---

## 💻 사용 가능한 명령어 (Commands)

| 명령어 | 설명 |
| :--- | :--- |
| `mcpv install` | **(필수)** `mcpv`를 설치하고 설정을 이전하며, **현재 디렉토리를 프로젝트 루트로 고정**합니다. |
| `mcpv install --force` | 이미 `mcpv`가 설치되어 있어도 강제로 덮어쓰고 재설치합니다. |
| `mcpv start` | **(내부용)** 서버를 시작합니다. (사용자가 직접 실행할 일은 거의 없습니다) |

<br>

---

## 🛠️ 검증된 추천 세팅 (Verified Setup)

개발자가 직접 사용 중인 검증된 MCP 서버 구성입니다. `mcpv`와 함께 사용했을 때 최고의 시너지를 냅니다.

```json
{
  "mcpServers": {
    "rube": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://rube.app/mcp"]
    },
    "open-aware": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://open-aware.qodo.ai/mcp"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", "PUT_IN_YOUR_API_KEY_HERE"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "mcp-server-neon": {
      "disabled": false,
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.neon.tech/sse"],
      "env": {
        "NEON_API_KEY": "NEVERCHANGE_DONT_PUT_IN_ANYTHING_ELSE_THAN_ME_HERE"
      }
    }
  }
}
