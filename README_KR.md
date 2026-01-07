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
  <a href="README.md">🇺🇸 English</a> | <a href="README_CN.md">🇨🇳 中文</a>
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
- **권한 문제 해결**: 귀찮은 관리자 권한 요구(Error 740)를 `RunAsInvoker`로 우회합니다.
- **좀비 프로세스 킬**: 포트를 점유하는 유령 프로세스를 자동으로 청소합니다.

### 2️⃣ Smart Valve (비용 방어)
**"알아서 아껴주는 똑똑한 지갑 지킴이"**
- 에이전트가 습관적으로 요청하는 거대한 문맥 데이터(`repomix`)를 감지합니다.
- **첫 번째만 전송**, 두 번째부터는 **"이미 가지고 있음"** 이라는 10 토큰짜리 메시지로 퉁칩니다.
- 실수로 인한 토큰 폭탄을 원천 봉쇄합니다.

### 2️⃣ Gateway Hijacking (안전한 금고)
**"복잡한 설정은 이제 그만"**
- 기존의 복잡한 MCP 설정을 안전한 금고(Vault)로 자동 이전합니다.
- 에이전트는 아무것도 모른 채 `mcpv`와 대화하지만, 모든 도구는 완벽하게 작동합니다.

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
```

<br>

---

# 🚀 설치 및 실행 가이드 (Windows / uv 기준)

이 프로젝트는 `uv`를 사용하여 **독립적인 가상환경(.venv)** 에서 설치/실행하는 것을 권장합니다.

> ✅ 아래 명령은 **프로젝트 루트 폴더(README가 있는 위치)** 에서 PowerShell로 실행하세요.

---

## 0. 준비물
- Windows 10/11
- PowerShell
- `uv` 설치됨
  - 설치 확인: `uv --version`

---

## 1. 기존 프로세스 정리 (재설치 시)
기존에 실행 중인 프로세스가 있다면 충돌 방지를 위해 종료합니다.

> ⚠️ `python` 프로세스 종료는 다른 작업에도 영향을 줄 수 있으니, 필요할 때만 실행하세요.

```powershell
Stop-Process -Name "mcpv" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
```

---

## 2. 가상환경 생성 및 패키지 설치
`uv`를 이용해 시스템 파이썬과 분리된 깨끗한 환경을 만듭니다.

```powershell
# uv 설치
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 가상환경(.venv) 생성
uv venv

# 가상환경에 mcpv 패키지 설치
uv pip install .
```

---

## 3. 안티그래비티 설정 등록 (핵심)
생성한 가상환경의 Python을 사용하여 설치 명령을 실행합니다.
즉, **이 가상환경을 사용하여 설치를 진행합니다.**

```powershell
# .venv 환경 내의 라이브러리를 사용하여 mcpv를 안티그래비티에 등록합니다.
.venv\Scripts\python -m mcpv install --force
```

---

## 4. 실행
바탕화면에 생성된 **`Antigravity Boost (mcpv)`** 바로가기를 더블 클릭하여 실행하세요.

---

## (선택) 정상 설치 확인
아래 명령으로 `.venv` 내부에서 `mcpv` 모듈이 정상적으로 로드되는지 확인할 수 있습니다.

```powershell
.venv\Scripts\python -m mcpv --help
```

---

☕ **Support**  
이 프로젝트가 토큰비와 시간을 아끼는 데 도움이 되었다면, 커피 한 잔 선물해 주세요!  

[<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="180" />](https://www.buymeacoffee.com/mcpv)

<br>

---

<div align="center">
  <b>⚡ Charged by MCP Vault</b><br>
  <i>Developed for High-Performance AI Agent Operations</i>
</div>