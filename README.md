# GitHub MCP 에이전트 학습용 예제 프로젝트 (FastAPI + React)

본 프로젝트는 최신 **Model Context Protocol (MCP)** 표준 규격을 준수하고, **LangChain**의 강력한 Fallback 메커니즘을 기반으로 설계된 지능형 GitHub 관리 에이전트 시스템입니다.

---

## 🚀 주요 기술 스택

- **Backend**: FastAPI, PyGithub, Python-Dotenv, LangChain (Core, Google GenAI, Groq, Community Ollama)
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide React, Axios
- **LLM Pipeline**: Google Gemini 2.5 Flash ➔ Groq Llama 3.3 70B ➔ Local Ollama gemma4:e2b (3단계 Fallback)

---

## 🛠️ 개발 환경 및 사전 준비 사항

1. **상위 폴더 가상환경 및 의존성**:
   - 본 프로젝트는 상위 폴더(`c:\aiproject`)의 `.venv` 가상환경에 이미 설치된 `fastapi`, `langchain`, `ollama` 등의 패키지를 공유하여 실행할 수 있도록 최적화되어 있습니다.
   
2. **로컬 Ollama 및 모델 구동**:
   - 3순위 Fallback 작동을 위해 로컬 환경에 Ollama가 설치되어 실행 중이어야 합니다.
   - Ollama에 `gemma4:e2b` 모델이 다운로드되어 있어야 합니다. (미설치 시 `ollama pull gemma4:e2b` 명령 수행 필요)

3. **환경 변수 (.env) 설정**:
   - `mcpExample/.env` 파일에 아래의 변수들이 설정되어 있는지 확인합니다:
     ```env
     GITHUB_TOKEN=your_github_personal_access_token
     GOOGLE_API_KEY=your_gemini_api_key
     GROQ_API_KEY=your_groq_api_key
     ```

---

## 🏃 실행 가이드

### 1. 백엔드 (FastAPI) 실행
상위 폴더의 가상환경을 사용하여 백엔드 서버를 8000번 포트로 실행합니다.

```powershell
# 프로젝트 루트(mcpExample) 디렉토리에서 시작
cd backend

# 상위 폴더의 가상환경을 사용하여 백엔드 직접 실행
..\..\.venv\Scripts\python.exe main.py
```
- 서버가 정상 작동하면 `http://localhost:8000/docs`에서 API 명세서를 확인할 수 있습니다.

### 2. 프론트엔드 (React + Vite) 실행
프론트엔드 디렉토리로 이동하여 의존성 패키지를 설치한 후 개발 서버를 3000번 포트로 구동합니다.

```powershell
# 프로젝트 루트(mcpExample) 디렉토리에서 시작
cd frontend

# 패키지 의존성 설치
npm install

# React Vite 개발 서버 구동 (포트 3000)
npm run dev
```
- 실행 후 브라우저에서 `http://localhost:3000`에 접속하여 챗봇 UI를 사용할 수 있습니다.

---

## 🧪 학습 및 테스트 시나리오

1. **저장소 정보 조회 테스트**:
   - 챗봇 채팅창의 하단 칩 목록에서 **"내 레포 목록 조회"**를 클릭하거나 *"현재 내 GitHub 저장소 목록을 조회해서 요약해줘."*를 입력합니다.
   - 에이전트가 어떤 순서로 계획(Plan)을 짰는지 확인하고, 최종 답변이 정중한 한국어로 출력되는지 검증합니다.

2. **3단계 Fallback 동작 검증**:
   - **시나리오**: `GOOGLE_API_KEY` 값을 `.env` 파일에서 가짜 값으로 일시 변경한 뒤 다시 요청을 보냅니다.
   - **결과**: 백엔드 콘솔에 Gemini API 오류 로그가 발생하며 자동으로 2순위인 **Groq Llama 3.3** 모델이 실행되고, 말풍선 상단의 `Planner / Reporter` 뱃지 모델명이 업데이트됩니다.
   - **최종 Fallback**: `GROQ_API_KEY` 마저 가짜 값으로 교체할 시, 로컬에서 대기 중이던 **Ollama gemma4:e2b** 모델이 정상 가동하며 3단계 예비망이 성공적으로 가동되는 것을 관찰할 수 있습니다.
