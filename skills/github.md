# 🛠️ GitHub 자동화 반영 스킬 지침 및 기술 비교서 (MCP vs Skills)

이 문서는 에이전트가 로컬 프로젝트의 소스 코드 변경 사항을 감지하여 깃허브(GitHub) 원격 저장소에 자동으로 커밋 및 푸시하는 자동화 프로세스 가이드입니다. 
더불어, **모델 컨텍스트 프로토콜(MCP)** 기반 호출 방식과 **스킬(Skills)** 기반 에이전트 제어 방식의 차이점을 소스 코드 예시와 함께 비교 분석합니다.

---

## 1. MCP(Model Context Protocol) vs Skills(스킬) 기술 비교

개발자나 에이전트가 외부 도구(예: Git, Database, Web API)를 조작할 때, 아키텍처 관점에서 두 가지 접근법을 선택할 수 있습니다.

| 비교 항목 | MCP (Model Context Protocol) 방식 | Skills (스킬/에이전트 지침) 방식 |
| :--- | :--- | :--- |
| **개념** | 클라이언트-서버 구조의 표준 API 규격(JSON-RPC 기반)을 통해 모델이 백엔드에 정의된 툴(Tool)을 호출하는 방식 | 에이전트의 프롬프트 지침서(Markdown)에 행동 규칙을 명시하고, 에이전트가 쉘 명령 도구를 활용해 자율적으로 단계를 조율하는 방식 |
| **동작 위치** | 백엔드 API 서버 (로컬/원격 호스트 환경) | 에이전트 내부 오케스트레이션 루프 |
| **확장성** | 새로운 도구를 쓸 때마다 백엔드 코드와 JSON 스펙을 매번 고쳐야 함 | 백엔드 코드 수정 없이 Markdown 지침 파일만 추가/편집하면 즉시 확장됨 |
| **안전성** | API 샌드박스 내부에서 허용된 파이썬 함수만 수행하므로 매우 안전함 | 에이전트가 직접 터미널 명령어를 실행하므로 유연하나 검증되지 않은 명령이 실행될 위험이 존재함 |
| **적합한 상황** | 정형화된 데이터 조작, 권한 제한이 엄격한 환경, 다중 에이전트 표준 툴셋 구성 | 개발 환경 빌드/배포, 임시 자동화 파이프라인 구축, 유연한 CLI 도구 조율 |

---

## 2. [구현 A] MCP 기반 전체 자동 반영 도구 소스
FastAPI 백엔드(`main.py`)에 도구 스펙을 등록하고 직접 `subprocess`를 호출하여 원스톱으로 처리하는 소스 구현 방식입니다. 
현재 `mcpExample` 프로젝트의 `push_all_changes` 도구 구현에 적용된 메커니즘입니다.

```python
import os
import subprocess
from fastapi import HTTPException

def push_all_changes_mcp(commit_message: str = None) -> str:
    """
    [MCP 백엔드 전용 소스]
    로컬 Git 상태를 추적하고, 스테이징, 커밋 및 푸시 과정을 원스톱으로 처리한 후 
    상세 결과 메시지를 마크다운 형태로 반환합니다.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # 1. 변경된 파일 상태 감지 (git status --porcelain)
    status_res = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    if status_res.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Git 상태 확인 실패: {status_res.stderr}")
        
    status_output = status_res.stdout.strip()
    if not status_output:
        return "### ℹ️ 알림\n로컬 저장소에 반영할 변경 사항이 없습니다."

    # 변경 파일 파싱
    added, modified, deleted = [], [], []
    for line in status_output.split("\n"):
        flag = line[:2]
        file_path = line[2:].strip()
        if "A" in flag or "??" in flag:
            added.append(file_path)
        elif "M" in flag:
            modified.append(file_path)
        elif "D" in flag:
            deleted.append(file_path)
            
    # 2. 커밋 메시지 자동화 수립
    if not commit_message:
        summary = []
        if added: summary.append(f"Add {added[0]}" + ("..." if len(added) > 1 else ""))
        if modified: summary.append(f"Update {modified[0]}" + ("..." if len(modified) > 1 else ""))
        if deleted: summary.append(f"Delete {deleted[0]}" + ("..." if len(deleted) > 1 else ""))
        commit_message = "feat/style: " + " | ".join(summary)

    # 3. Git 순차 명령어 실행
    try:
        # git add .
        subprocess.run(["git", "add", "."], cwd=project_root, check=True)
        # git commit -m
        subprocess.run(["git", "commit", "-m", commit_message], cwd=project_root, check=True)
        # git push
        subprocess.run(["git", "push"], cwd=project_root, check=True)
        
        # 최신 커밋 해시 가져오기
        sha_res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=project_root, capture_output=True, text=True)
        commit_sha = sha_res.stdout.strip()
    except subprocess.CalledProcessError as err:
        raise HTTPException(status_code=500, detail=f"Git 반영 실패: {err}")

    # 4. 완료 피드백 메시지 포맷팅
    report = [
        "### 🎉 GitHub 반영 성공 완료 보고서 (MCP 방식)",
        f"- **커밋 메시지**: `{commit_message}`",
        f"- **커밋 SHA**: `{commit_sha}`",
        f"- **대상 브랜치**: `main` (origin)",
        "\n#### 📂 변경 파일 내역",
        "| 상태 | 파일 경로 |",
        "| :--- | :--- |"
    ]
    for f in added: report.append(f"| 🟢 Added | `{f}` |")
    for f in modified: report.append(f"| 🟡 Modified | `{f}` |")
    for f in deleted: report.append(f"| 🔴 Deleted | `{f}` |")
    
    return "\n".join(report)
```

---

## 3. [구현 B] Skills 기반 에이전트 자율 수행 지침
스킬(Skills) 방식은 백엔드 서버 코드를 수정하지 않고, 에이전트가 지침에 따라 로컬 쉘 명령 도구(`run_command`)를 결합해서 자율적으로 깃허브 반영 프로세스를 밟도록 유도하는 지침서 설계입니다.

### 에이전트 전용 행동 지침 규격 (System Prompt Instruction)
```markdown
[ROLE: GIT_REFLECT_SKILL]
사용자가 "깃허브에 코드를 반영해줘" 또는 "커밋해줘"라고 요청하면, 백엔드 API를 경유하지 않고 아래의 스킬 지침을 기반으로 로컬 터미널 명령 도구를 직접 실행하여 처리한다.

[ACTION STEPS]
1. 로컬 저장소 상태 확인: `git status --porcelain` 명령을 실행한다.
2. 결과 분석:
   - 출력 결과가 비어있다면, 사용자에게 "반영할 변경 내용이 없습니다."라고 안내하고 즉시 작업을 종료한다.
   - 변경 내용이 있다면 추가, 수정, 삭제된 파일들을 분류한다.
3. 소스 코드 스테이징: `git add .`를 수행한다.
4. 커밋 메시지 결정:
   - 사용자가 구체적인 커밋 메시지를 적어준 경우 해당 메시지를 사용한다.
   - 메시지가 없다면, 변경 파일 분류를 토대로 "refactor: Update [파일명]" 형태의 직관적인 메시지를 자동 생성한다.
5. 로컬 커밋 수행: `git commit -m "[결정된 메시지]"`를 수행한다.
6. 원격지 푸시: `git push origin main` (또는 활성화된 현재 브랜치)을 수행한다.
7. 완료 보고 메시지 작성:
   - 완료 후, 다음 양식으로 포맷팅하여 사용자에게 최종 보고한다.

[완료 보고서 양식]
### 🚀 깃허브 반영 완료 보고 (Skills 자율 제어 방식)
* **생성된 커밋**: `[커밋 메시지]`
* **수행 환경**: Local Workspace -> Remote Repository
* **수정 내역 요약**:
  - `[+] 추가된 파일 목록...`
  - `[-] 변경/삭제된 파일 목록...`
* **푸시 완료 브랜치**: `main`
```

---

## 4. 대표님을 위한 활용 및 비교 가이드
- **속도가 중요하고 로컬에서 에이전트를 주로 활용할 때**: **Skills 방식**이 유용합니다. 지침 문서 하나만 추가하면 별도의 파이썬 웹 개발 없이 바로 복잡한 빌드/커밋 프로세스를 태울 수 있습니다.
- **여러 협업자가 챗봇 웹 UI를 이용해 서버에 배포된 깃허브 도구를 쓸 때**: **MCP 방식**이 필수적입니다. 서버 내부에 깃허브 토큰과 파이썬 프로세스를 격리시켜 웹 API 엔드포인트 형태로만 제어하기 때문에 보안성이 탁월합니다.
