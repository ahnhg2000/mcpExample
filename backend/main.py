import os
import json
import re
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from github import Github, GithubException

# LLMRouter 로드
from llm_router import LLMRouter

# FastAPI 애플리케이션 초기화
app = FastAPI(
    title="GitHub MCP 학습용 에이전트 API",
    description="MCP 표준 규격을 준수하고 LangChain 3단계 Fallback을 지원하는 깃허브 도구 연동 에이전트",
    version="1.2.0"
)

# CORS 설정 (프론트엔드 연동을 위해 모든 오리진 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM Router 및 GitHub 클라이언트 초기화
llm_router = LLMRouter()
github_token = os.getenv("GITHUB_TOKEN")

if not github_token:
    print("⚠️ Warning: GITHUB_TOKEN 환경 변수가 설정되지 않았습니다. GitHub 도구 호출이 실패할 수 있습니다.")

github_client = Github(github_token) if github_token else None

# MCP 도구 정의 파일 로드
MCP_TOOLS_PATH = os.path.join(os.path.dirname(__file__), "mcp", "github.json")
try:
    with open(MCP_TOOLS_PATH, "r", encoding="utf-8") as f:
        MCP_TOOLS = json.load(f)
except Exception as e:
    print(f"⚠️ Warning: MCP 도구 스펙 파일을 읽는 중 오류가 발생했습니다: {e}")
    MCP_TOOLS = []


# --------------------------------------------------
# 헬퍼 함수 정의
# --------------------------------------------------
def get_user_repo(repo_name: str):
    """
    저장소명을 기반으로 PyGithub Repository 객체를 획득하는 헬퍼 함수.
    'owner/repo' 형태와 일반 'repo' 형태를 모두 지원합니다.
    """
    if not github_client:
        raise HTTPException(status_code=500, detail="GitHub 클라이언트가 초기화되지 않았습니다. GITHUB_TOKEN을 확인해 주십시오.")
    
    try:
        if "/" in repo_name:
            return github_client.get_repo(repo_name)
        else:
            # 로그인된 유저의 정보 획득 후 저장소 로드
            user = github_client.get_user()
            return user.get_repo(repo_name)
    except GithubException as e:
        raise HTTPException(
            status_code=e.status,
            detail=f"GitHub 저장소 '{repo_name}'를 찾을 수 없거나 접근 권한이 없습니다. (원인: {e.data.get('message', str(e))})"
        )


def extract_json_array(text: str) -> List[Dict[str, Any]]:
    """
    LLM 응답 텍스트 내에서 JSON 배열(시퀀스 플랜)을 찾아 안전하게 파싱합니다.
    ```json ... ``` 마크다운 블록이 있어도 동작합니다.
    """
    try:
        # JSON 배열 블록만 정규표현식으로 추출 시도
        match = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        # 순수 JSON 텍스트 파싱 시도
        return json.loads(text.strip())
    except Exception as e:
        print(f"JSON 파싱 실패 원본 텍스트:\n{text}")
        raise ValueError(f"LLM이 반환한 응답에서 유효한 JSON 실행 계획을 생성하거나 파싱하지 못했습니다. (에러: {e})")


# --------------------------------------------------
# FastAPI API 엔드포인트 정의
# --------------------------------------------------

class TaskRequest(BaseModel):
    description: str


@app.get("/tools")
async def list_tools():
    """
    1. MCP 표준 규격 엔드포인트: 가용한 도구들의 카탈로그를 반환합니다.
    """
    return {"tools": MCP_TOOLS}


@app.post("/tools/call")
async def call_tool(request: Dict[str, Any]):
    """
    2. MCP 표준 규격 엔드포인트: 이름과 파라미터를 기반으로 특정 도구를 실행합니다.
    결과는 {"content": [{"type": "text", "text": "실행결과..."}]} 규격을 반드시 준수합니다.
    """
    tool_name = request.get("name")
    arguments = request.get("arguments", {})
    
    if not tool_name:
        raise HTTPException(status_code=400, detail="요청에 도구 이름('name')이 누락되었습니다.")

    try:
        # 1. 저장소 목록 조회
        if tool_name == "list_repositories":
            if not github_client:
                raise Exception("GITHUB_TOKEN이 존재하지 않습니다.")
            repos = github_client.get_user().get_repos()
            repo_list = [{"name": r.name, "full_name": r.full_name, "private": r.private} for r in repos[:10]]
            result_text = json.dumps(repo_list, ensure_ascii=False, indent=2)
            
        # 2. 저장소 상세 조회
        elif tool_name == "get_repository_details":
            repo_name = arguments.get("repo_name")
            repo = get_user_repo(repo_name)
            details = {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "stars": repo.stargazers_count,
                "language": repo.language,
                "forks": repo.forks_count,
                "owner": repo.owner.login
            }
            result_text = json.dumps(details, ensure_ascii=False, indent=2)

        # 3. 파일 읽기
        elif tool_name == "read_file_content":
            repo_name = arguments.get("repo_name")
            path = arguments.get("path")
            repo = get_user_repo(repo_name)
            file_content = repo.get_contents(path)
            # 바이너리 또는 텍스트 디코딩 처리
            result_text = file_content.decoded_content.decode("utf-8")

        # 4. 파일 생성 및 수정 (커밋 & 푸시)
        elif tool_name == "create_or_update_file":
            repo_name = arguments.get("repo_name")
            path = arguments.get("path")
            content = arguments.get("content")
            commit_message = arguments.get("commit_message", "Updated via MCP Agent")
            
            repo = get_user_repo(repo_name)
            
            try:
                # 기존 파일이 존재하면 업데이트 수행
                file_info = repo.get_contents(path)
                res = repo.update_file(path, commit_message, content, file_info.sha)
                result_text = f"성공적으로 '{path}' 파일을 수정(업데이트)했습니다. 커밋 SHA: {res['commit'].sha}"
            except GithubException as ge:
                # 404 에러일 경우 파일이 없는 것이므로 새로 작성
                if ge.status == 404:
                    res = repo.create_file(path, commit_message, content)
                    result_text = f"성공적으로 '{path}' 파일을 신규 생성했습니다. 커밋 SHA: {res['commit'].sha}"
                else:
                    raise ge

        # 5. 커밋 목록 조회
        elif tool_name == "list_commits":
            repo_name = arguments.get("repo_name")
            limit = int(arguments.get("limit", 5))
            repo = get_user_repo(repo_name)
            commits = repo.get_commits()
            commit_list = []
            for c in commits[:limit]:
                commit_list.append({
                    "sha": c.sha[:8],
                    "author": c.commit.author.name,
                    "message": c.commit.message,
                    "date": c.commit.author.date.isoformat()
                })
            result_text = json.dumps(commit_list, ensure_ascii=False, indent=2)

        else:
            raise HTTPException(status_code=404, detail=f"정의되지 않은 MCP 도구입니다: '{tool_name}'")

        # MCP 표준 응답 규격 준수
        return {
            "content": [
                {
                    "type": "text",
                    "text": result_text
                }
            ]
        }

    except GithubException as ge:
        # 깃허브 에러 시 원인 상세 출력
        err_msg = f"GitHub API 호출 중 실패 발생 (상태코드: {ge.status}): {ge.data.get('message', str(ge))}"
        return {
            "content": [{"type": "text", "text": err_msg}],
            "isError": True
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"도구 실행 에러: {str(e)}"}],
            "isError": True
        }


@app.post("/agent/task")
async def handle_natural_language_task(task: TaskRequest):
    """
    3. 에이전트 코어 엔드포인트: 사용자의 자연어 명령을 해석하여 도구들을 순차적으로 실행하고 결과를 도출합니다.
    """
    description = task.description

    # 1단계: 에이전트의 도구 호출 계획 수립을 위한 시스템 프롬프트 작성
    planner_system_prompt = """당신은 사용자의 요청을 분석하고, 아래 제공된 GitHub MCP Tools들을 활용하여 어떤 순서로 작업을 실행할지 계획하는 전문 에이전트 코디네이터입니다.

[요청 사항]
1. 사용 가능한 도구 목록(JSON)을 자세히 분석하여, 사용자의 명령을 수행하기 위한 최적의 실행 흐름(시퀀스)을 수립하세요.
2. 결과는 무조건 실행할 순서대로 정렬된 JSON 배열 포맷 하나만 반환해야 합니다. 설명이나 다른 텍스트는 절대 덧붙이지 마십시오.

[출력 포맷 규격]
[
  {"tool": "도구이름", "arguments": {"인자1": "값1"}}
]

[가용한 MCP 도구 리스트]
""" + json.dumps(MCP_TOOLS, ensure_ascii=False, indent=2)

    planner_user_prompt = f"사용자의 명령: '{description}'\n위 명령을 수행하기 위한 도구 실행 계획 JSON 배열을 반환하십시오."

    try:
        # LLM Router를 통해 첫 번째 실행 플랜 수립
        plan_text, planner_model = await llm_router.generate(planner_system_prompt, planner_user_prompt)
        print(f"🤖 [Planner Model: {planner_model}] 수립된 계획:\n{plan_text}")
        
        # JSON 플랜 파싱
        tool_calls = extract_json_array(plan_text)
        
        # 2단계: 도구 실행 계획 순차 수행
        execution_logs = []
        for i, call in enumerate(tool_calls):
            tool_name = call.get("tool")
            args = call.get("arguments", {})
            
            print(f"➡️ [Step {i+1}] 실행 도구: {tool_name} | 인자: {args}")
            
            # call_tool 내부 직접 호출
            tool_response = await call_tool({"name": tool_name, "arguments": args})
            
            # 실행 결과 추출
            is_error = tool_response.get("isError", False)
            content_list = tool_response.get("content", [])
            response_text = content_list[0].get("text", "") if content_list else "결과 없음"
            
            execution_logs.append({
                "step": i + 1,
                "tool": tool_name,
                "arguments": args,
                "success": not is_error,
                "result": response_text
            })

            # 에러 발생 시 진행 중단 후 사용자에게 오류 보고
            if is_error:
                print(f"❌ [Step {i+1}] 실행 에러로 인해 시퀀스가 중단되었습니다.")
                break

        # 3단계: 실행 로그를 기반으로 최종 자연어 피드백 생성
        synthesis_system_prompt = """당신은 GitHub MCP 에이전트의 결과를 사용자에게 종합하여 보고하는 비서입니다.
사용자의 원래 명령과 실행된 도구들의 단계별 상세 실행 로그를 토대로, 어떤 작업이 수행되었는지 최종 결과를 한국어로 정중하게 설명해 주십시오. 
만약 실행 중 실패한 단계가 있다면 그 원인을 기술 규격에 맞게 친절히 진단해 주십시오."""

        synthesis_user_prompt = f"""[사용자 명령]
{description}

[도구 실행 기록 로그]
{json.dumps(execution_logs, ensure_ascii=False, indent=2)}

위 실행 내역을 기반으로 최종 결과를 리포트 양식으로 간결하고 전문적인 한국어로 작성해 주십시오."""

        final_answer, synthesizer_model = await llm_router.generate(synthesis_system_prompt, synthesis_user_prompt)

        return {
            "status": "success",
            "plan": tool_calls,
            "execution_logs": execution_logs,
            "result": final_answer,
            "planner_model": planner_model,
            "synthesizer_model": synthesizer_model
        }

    except Exception as e:
        # 예외가 발생할 경우 오류의 구체적 내용과 함께 HTTP 500 에러 리턴
        raise HTTPException(
            status_code=500,
            detail=f"태스크 수행 중 오류가 발생했습니다. (원인: {str(e)})"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
