import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, Github, Bot, Terminal, Shield, Cpu, RefreshCw, 
  CheckCircle2, XCircle, ChevronRight, Play, AlertCircle 
} from 'lucide-react';
import axios from 'axios';

// 백엔드 API 기본 주소
const API_BASE_URL = 'http://localhost:8000';

interface ToolSpec {
  name: string;
  description: string;
  inputSchema: any;
}

interface ExecutionLog {
  step: number;
  tool: string;
  arguments: any;
  success: boolean;
  result: string;
}

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  isError?: boolean;
  plannerModel?: string;
  synthesizerModel?: string;
  plan?: Array<{ tool: string; arguments: any }>;
  logs?: ExecutionLog[];
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([
    { 
      role: 'system', 
      content: 'LangChain 기반 3단계 Fallback 체인이 작동 중입니다. (1순위: Gemini 2.5 Flash ➔ 2순위: Groq Llama ➔ 3순위: 로컬 Ollama gemma4:e2b)\n원하시는 GitHub 작업을 자연어로 작성해 주세요.' 
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [tools, setTools] = useState<ToolSpec[]>([]);
  const [activeTab, setActiveTab] = useState<'chat' | 'tools'>('chat');
  const chatEndRef = useRef<HTMLDivElement>(null);

  // 학습용 퀵 스타트 예제 칩
  const quickPrompts = [
    { label: "내 레포 목록 조회", prompt: "현재 내 GitHub 저장소 목록을 조회해서 요약해줘." },
    { label: "README.md 파일 수정", prompt: "mcpExample 저장소의 README.md 파일 내용을 읽어보고 끝에 '김과장 완료'라고 덧붙여서 업데이트해줘." },
    { label: "최근 커밋 확인", prompt: "mcpExample 저장소의 최근 커밋 목록 3개만 조회해줘." },
    { label: "깃허브 반영해줘", prompt: "현재 로컬의 변경 사항을 깃허브에 반영해줘." }
  ];

  // 컴포넌트 마운트 시 백엔드의 MCP 툴 스펙 로드
  useEffect(() => {
    const fetchTools = async () => {
      try {
        const res = await axios.get(`${API_BASE_URL}/tools`);
        setTools(res.data.tools || []);
      } catch (err) {
        console.error("MCP 도구 스펙 로드 실패:", err);
      }
    };
    fetchTools();
  }, []);

  // 메시지 전송 시 아래로 자동 스크롤
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (textToSend: string) => {
    if (!textToSend.trim() || isLoading) return;

    const userMessage: Message = { role: 'user', content: textToSend };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await axios.post(`${API_BASE_URL}/agent/task`, {
        description: textToSend
      });

      const data = res.data;
      if (data.status === 'success') {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.result,
          plannerModel: data.planner_model,
          synthesizerModel: data.synthesizer_model,
          plan: data.plan,
          logs: data.execution_logs
        }]);
      }
    } catch (err: any) {
      console.error(err);
      const errMsg = err.response?.data?.detail || '백엔드 서버와 통신할 수 없거나 예기치 못한 에러가 발생했습니다.';
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `🚨 오류 발생:\n${errMsg}`,
        isError: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-1 h-full w-full bg-zinc-950 text-zinc-100 font-sans overflow-hidden">
      {/* 1. 사이드바 (MCP 툴 정보 및 로컬 모델 정보) */}
      <div className="hidden md:flex flex-col w-80 border-r border-zinc-800 bg-zinc-900/50 backdrop-blur-md">
        <div className="p-5 border-b border-zinc-800 flex items-center gap-3">
          <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-400">
            <Github className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-semibold text-sm tracking-wide">GitHub MCP Agent</h1>
            <p className="text-[10px] text-emerald-400 font-mono">LangChain Fallback Engine</p>
          </div>
        </div>

        {/* 탭 네비게이션 */}
        <div className="flex border-b border-zinc-800 text-xs text-center font-medium">
          <button 
            onClick={() => setActiveTab('chat')}
            className={`flex-1 py-3 border-b-2 transition-colors ${activeTab === 'chat' ? 'border-emerald-500 text-emerald-400 bg-zinc-800/30' : 'border-transparent text-zinc-400 hover:text-zinc-200'}`}
          >
            대화 모드
          </button>
          <button 
            onClick={() => setActiveTab('tools')}
            className={`flex-1 py-3 border-b-2 transition-colors ${activeTab === 'tools' ? 'border-emerald-500 text-emerald-400 bg-zinc-800/30' : 'border-transparent text-zinc-400 hover:text-zinc-200'}`}
          >
            MCP 스펙 ({tools.length})
          </button>
        </div>

        {/* 탭 컨텐츠 */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'chat' ? (
            <div className="space-y-4">
              <div className="p-3 bg-zinc-900 rounded-lg border border-zinc-800 text-xs space-y-2">
                <div className="flex items-center gap-1.5 text-zinc-300 font-semibold mb-1">
                  <Cpu className="w-3.5 h-3.5 text-emerald-400" />
                  <span>3단계 Fallback 체인 사양</span>
                </div>
                <div className="space-y-1.5 font-mono text-[11px] text-zinc-400">
                  <div className="flex justify-between items-center bg-zinc-950 p-1.5 rounded">
                    <span className="text-emerald-400 font-semibold">1. Primary</span>
                    <span>gemini-2.5-flash</span>
                  </div>
                  <div className="flex justify-between items-center bg-zinc-950 p-1.5 rounded">
                    <span className="text-indigo-400">2. Secondary</span>
                    <span>llama-3.3-70b</span>
                  </div>
                  <div className="flex justify-between items-center bg-zinc-950 p-1.5 rounded">
                    <span className="text-amber-500">3. Tertiary</span>
                    <span>gemma4:e2b (Ollama)</span>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-zinc-900 rounded-lg border border-zinc-800 text-xs">
                <div className="flex items-center gap-1.5 text-zinc-300 font-semibold mb-2">
                  <Shield className="w-3.5 h-3.5 text-emerald-400" />
                  <span>연동 인증 상태</span>
                </div>
                <ul className="space-y-1 text-zinc-400 text-[11px]">
                  <li className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
                    GITHUB_TOKEN: <span className="text-emerald-400">설정됨</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
                    GOOGLE_API_KEY: <span className="text-emerald-400">설정됨</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
                    GROQ_API_KEY: <span className="text-emerald-400">설정됨</span>
                  </li>
                </ul>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {tools.map((t, idx) => (
                <div key={idx} className="p-3 bg-zinc-900 rounded-lg border border-zinc-800 text-xs space-y-1">
                  <div className="flex items-center gap-1.5 text-emerald-400 font-mono font-semibold">
                    <Terminal className="w-3.5 h-3.5" />
                    <span>{t.name}</span>
                  </div>
                  <p className="text-zinc-400 text-[11px] leading-relaxed">{t.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 2. 메인 채팅 영역 */}
      <div className="flex-1 flex flex-col h-full bg-zinc-950 overflow-hidden relative">
        {/* 상단 헤더 */}
        <div className="p-4 border-b border-zinc-900 bg-zinc-900/30 flex items-center justify-between z-10">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-emerald-400" />
            <span className="font-semibold text-sm">GitHub MCP Intelligent Agent</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse"></span>
            <span className="text-xs text-zinc-400 font-mono">Local Host Connected</span>
          </div>
        </div>

        {/* 메시지 출력 영역 */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-2xl p-4 transition-all duration-300 ${
                msg.role === 'user' 
                  ? 'bg-emerald-600/90 text-white shadow-lg shadow-emerald-950/20' 
                  : msg.role === 'system'
                    ? 'bg-zinc-900/80 border border-zinc-800 text-zinc-400 font-mono text-[11px]'
                    : 'bg-zinc-900 border border-zinc-800 text-zinc-200'
              } ${msg.isError ? 'border-red-500/50 bg-red-950/20 text-red-200' : ''}`}>
                
                {/* 1. AI 응답일 때 모델 명칭 표시 */}
                {msg.role === 'assistant' && (msg.plannerModel || msg.synthesizerModel) && (
                  <div className="flex flex-wrap items-center gap-1.5 mb-2 pb-2 border-b border-zinc-800 text-[10px] text-zinc-400">
                    <span className="px-1.5 py-0.5 rounded bg-zinc-800 text-emerald-400 font-mono font-semibold">
                      ⚙️ Planner: {msg.plannerModel}
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-zinc-800 text-indigo-400 font-mono font-semibold">
                      ✍️ Reporter: {msg.synthesizerModel}
                    </span>
                  </div>
                )}

                <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>

                {/* 2. 도구 실행 계획 및 로그 시각화 (학습용) */}
                {msg.role === 'assistant' && msg.logs && msg.logs.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-zinc-800 space-y-2">
                    <div className="flex items-center gap-1.5 text-xs text-zinc-400 font-semibold font-mono">
                      <Play className="w-3.5 h-3.5 text-emerald-400" />
                      <span>도구 실행 기록 (MCP Tool Execution Logs)</span>
                    </div>
                    
                    <div className="space-y-2">
                      {msg.logs.map((log) => (
                        <div key={log.step} className="bg-zinc-950/60 p-2.5 rounded-lg border border-zinc-900 text-xs">
                          <div className="flex justify-between items-center mb-1">
                            <span className="font-mono text-zinc-400 font-semibold">
                              Step {log.step}: <span className="text-emerald-400">{log.tool}</span>
                            </span>
                            <span className={`flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full ${log.success ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-800/40' : 'bg-red-950/40 text-red-400 border border-red-800/40'}`}>
                              {log.success ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                              {log.success ? 'Success' : 'Failed'}
                            </span>
                          </div>
                          
                          {/* 파라미터 정보 */}
                          <div className="text-[10px] text-zinc-500 font-mono bg-zinc-950/80 p-1.5 rounded border border-zinc-900/50 mb-1 overflow-x-auto">
                            Args: {JSON.stringify(log.arguments)}
                          </div>
                          
                          {/* 결과값 텍스트 */}
                          <div className="text-[11px] text-zinc-400 font-mono max-h-24 overflow-y-auto whitespace-pre-wrap leading-tight mt-1">
                            {log.result}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* 로딩 대기 상태 UI */}
          {isLoading && (
            <div className="flex justify-start items-center gap-3">
              <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 flex items-center gap-3 text-emerald-400 text-sm">
                <RefreshCw className="w-4 h-4 animate-spin text-emerald-400" />
                <span>LangChain Fallback Engine이 최선의 실행 계획을 수립하고 툴을 호출하는 중...</span>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* 퀵 가이드 예제 칩 영역 */}
        <div className="px-4 py-2 bg-zinc-900/10 border-t border-zinc-900 z-10">
          <div className="flex flex-wrap gap-2 items-center">
            <span className="text-[11px] text-zinc-500 font-semibold uppercase tracking-wider mr-1">연습용 예시:</span>
            {quickPrompts.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => setInput(chip.prompt)}
                className="text-[11px] px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 rounded-full text-zinc-300 hover:text-emerald-400 transition-all duration-200"
              >
                {chip.label}
              </button>
            ))}
          </div>
        </div>

        {/* 사용자 메시지 입력 및 전송 영역 */}
        <div className="p-4 border-t border-zinc-900 bg-zinc-950 z-10">
          <div className="flex gap-3 max-w-4xl mx-auto">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend(input)}
              placeholder="예: mcpExample 저장소의 최근 커밋 5개 조회해줘..."
              className="flex-1 bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3 focus:outline-none focus:border-emerald-500 text-sm placeholder:text-zinc-600"
            />
            <button
              onClick={() => handleSend(input)}
              disabled={isLoading || !input.trim()}
              className="bg-emerald-600 hover:bg-emerald-500 px-5 rounded-xl flex items-center justify-center text-white font-medium transition-colors duration-200 disabled:opacity-40 disabled:hover:bg-emerald-600 shadow-md shadow-emerald-950/20"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
