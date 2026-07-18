import os
from typing import Dict, Any, Tuple
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

# .env 파일 위치 로드 (backend 기준 상위 디렉토리에 .env가 있으므로 ../.env)
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=dotenv_path)

class LLMRouter:
    def __init__(self):
        # API 키 설정 로드
        google_api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        # 1순위: Google Gemini 2.5 Flash
        # langchain-google-genai 사용
        self.gemini = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0
        )
        
        # 2순위: Groq Llama 3.3 70B
        # langchain-groq 사용
        self.groq_llama = ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=groq_api_key,
            temperature=0
        )
        
        # 3순위: Local Ollama Gemma 4:e2b
        # langchain-community ChatOllama 사용
        self.ollama_gemma = ChatOllama(
            model="gemma4:e2b",
            base_url="http://localhost:11434",
            temperature=0
        )
        
        # LangChain with_fallbacks 체인 생성
        # 1순위 Gemini 실패 시 -> 2순위 Groq Llama -> 3순위 Ollama 순서로 자동 복구(failover)
        self.fallback_chain = self.gemini.with_fallbacks([self.groq_llama, self.ollama_gemma])

    async def generate(self, system_prompt: str, user_prompt: str) -> Tuple[str, str]:
        """
        주어진 시스템 프롬프트와 사용자 프롬프트를 사용하여 LLM 체인을 실행합니다.
        자동 Fallback이 작동하며, 최종 생성 결과와 실제로 구동된 모델명을 튜플(결과, 모델명)로 반환합니다.
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        # LangChain 비동기 호출
        response = await self.fallback_chain.ainvoke(messages)
        
        # 어떤 모델이 최종적으로 사용되었는지 메타데이터를 기반으로 확인
        resolved_model = "알 수 없음 (Fallback 작동)"
        metadata = response.response_metadata
        
        # 각 공급자별 메타데이터 특징을 분석하여 모델명 식별
        if "model_name" in metadata:  # Gemini 또는 Groq의 일반적인 패턴
            resolved_model = metadata["model_name"]
        elif "model" in metadata:     # Ollama 등의 패턴
            resolved_model = metadata["model"]
        else:
            # 메타데이터가 비어있거나 특정 정보가 없는 경우 응답의 성격이나 클래스로 유추
            # LangChain 내부 구조 상 ChatOllama 응답 시 metadata에 정보가 유동적일 수 있어 기본값 처리
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                # Groq 이나 Gemini 는 대게 usage_metadata가 포함됨
                resolved_model = "Gemini 2.5 Flash / Groq Llama"
            else:
                resolved_model = "Local Ollama (gemma4:e2b)"

        # 직관적으로 알 수 있는 이름으로 매핑
        if "gemini" in resolved_model.lower():
            model_display = "Gemini 2.5 Flash (Primary)"
        elif "llama" in resolved_model.lower():
            model_display = "Groq Llama-3.3-70b (Fallback 1)"
        elif "gemma" in resolved_model.lower():
            model_display = "Local Ollama gemma4:e2b (Fallback 2)"
        else:
            model_display = f"{resolved_model} (구동됨)"

        return response.content, model_display
