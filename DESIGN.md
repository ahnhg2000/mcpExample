# DESIGN.md — getdesign.md 스타일의 UI/UX 디자인 가이드

본 문서는 AI 코딩 에이전트(김과장 및 서브에이전트)가 본 프로젝트의 프론트엔드를 신규 개발하거나 확장할 때 일관되게 따라야 할 디자인 시스템 규격 및 비주얼 가이드입니다.

---

## 🎨 디자인 정체성 및 무드 (Visual Identity & Mood)
- **컨셉**: 전문적이고 현대적인 고기능성 AI 개발자 대시보드.
- **주요 테마**: Pure Dark Theme (어둡고 차분한 계열의 다크 모드).
- **디자인 포인트**: 글래스모피즘(Glassmorphism), 미세한 테두리 강조(Subtle Border), 네온 빛의 액센트 활용을 통한 깊이감과 가시성 확보.

---

## 🎨 색상 시스템 (Color Palette)

모든 CSS 색상값은 다음 토큰을 필수로 사용해야 하며, ad-hoc(임의) 컬러 지정을 금지합니다.

| 분류 | Tailwind 클래스 | Hex 코드 | 설명 |
| :--- | :--- | :--- | :--- |
| **Canvas Background** | `bg-zinc-950` | `#09090b` | 전체 화면의 최하단 기본 배경색 |
| **Panel Background** | `bg-zinc-900` | `#18181b` | 카드, 사이드바, 다이얼로그 등 정보 컨테이너 |
| **Subtle Border** | `border-zinc-800` | `#27272a` | 요소 간 경계선 및 그리드 선 |
| **Primary Accent** | `text-emerald-400` / `bg-emerald-600` | `#34d399` / `#059669` | 성공 상태, 주 버튼, 메인 액센트 컬러 |
| **Secondary Accent**| `text-indigo-400` / `bg-indigo-600` | `#818cf8` / `#4f46e5` | 모델 정보, 부가 통계, 기능 전환 버튼 |
| **Tertiary Accent** | `text-amber-500` / `bg-amber-600` | `#f59e0b` / `#d97706` | 로컬 Fallback 모델 상태, 경고 및 알림 |
| **Text Primary** | `text-zinc-100` | `#f4f4f5` | 가독성이 높은 주요 본문 텍스트 |
| **Text Secondary** | `text-zinc-400` | `#a1a1aa` | 레이블, 설명, 타임스탬프 등 부가 정보 |

---

## font-sans (Typography)

- **기본 본문 서체**: `Inter`, `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto` (샌스세리프 계열)
- **코드 및 터미널 서체**: `Geist Mono`, `Fira Code`, `JetBrains Mono` (고정폭 서체)

### 타이포그래피 계층 (Hierarchy)
1. **대제목 (Header Title)**: `text-lg` ~ `text-xl` (font-semibold, tracking-wide)
2. **중제목 (Section Header)**: `text-sm` (font-semibold, tracking-wider)
3. **본문 (Body)**: `text-sm` (font-normal, leading-relaxed)
4. **부가설명/메타데이터 (Caption/Meta)**: `text-[11px]` ~ `text-xs` (font-mono, text-zinc-500)

---

## 📐 Spacing & Layout (간격 및 레이아웃 규칙)

- **사이드바 너비**: `w-80` (320px) 고정. 화면이 작을 경우(`md` 미만) 자동 숨김 처리.
- **채팅 내용 공간**: 최대 너비 `max-w-4xl`로 억제하여 텍스트의 가독성 한계를 확보.
- **패딩 및 마진**:
  - 패널 내부 여백: `p-4` (16px) 또는 `p-5` (20px)
  - 요소 간 간격: `space-y-4` (16px) 또는 `space-y-6` (24px)
  - 둥글기 규칙: 버튼 및 패널은 `rounded-xl` (12px) 또는 `rounded-2xl` (16px)을 사용하여 유려한 모서리 유지.

---

## 🧩 컴포넌트 표준 스타일 명세

### 1. 채팅 메시지 버블 (Message Bubbles)
- **사용자(User)**: 
  - 스타일: `bg-emerald-600/90`, `text-white`, `rounded-2xl` (우측 상단 둥글기 생략하여 말풍선 느낌 극대화)
- **에이전트(Assistant)**: 
  - 스타일: `bg-zinc-900`, `border border-zinc-800`, `text-zinc-200`, `rounded-2xl` (좌측 상단 둥글기 생략)
- **시스템 메시지(System)**:
  - 스타일: `bg-zinc-900/50`, `border border-zinc-800`, `text-zinc-400`, `font-mono`, `text-[11px]`

### 2. 에이전트 실행 상태 바 (Execution Logs Card)
- 에이전트의 내부 실행 흐름을 시각적으로 나타내는 영역입니다.
  - 패널 내부: `bg-zinc-950/60`, `border border-zinc-900`
  - 아규먼트 상자: `text-[10px] bg-zinc-950/80 p-1.5 font-mono border border-zinc-900/50`
  - 성공/실패 뱃지: 둥근 알약 스타일(`rounded-full`)에 초록/빨강 계열의 연한 보더 적용.

### 3. 상태 표시등 및 뱃지 (Indicators & Badges)
- **온라인 상태**: 초록색 원형 점(`bg-emerald-500`)과 미세한 `animate-pulse` 애니메이션을 추가하여 활성 상태임을 사용자에게 인식시킵니다.
- **모델 정보 뱃지**: 기계적이고 미래적인 느낌을 주기 위해 톱니바퀴(⚙️) 아이콘과 펜(✍️) 아이콘을 결합한 폰트 모노 뱃지 형태로 표기합니다.

---

## 🎬 애니메이션 및 마이크로 인터랙션 (Micro-interactions)

1. **로딩 피드백 (Loader)**:
   - 태스크 계획 및 API 호출 진행 상황을 표시할 때 `RefreshCw` 아이콘에 `animate-spin`을 적용하여 대기 중임을 보장합니다.
2. **트랜지션 효과 (Transitions)**:
   - 탭 버튼 호버, 칩 호버, 전송 버튼 활성화 시 `transition-all duration-200`을 적용하여 색상이 부드럽게 변환되도록 유도합니다.
3. **포커스 링 (Focus State)**:
   - 입력 필드(`input`) 포커스 시 `focus:border-emerald-500`을 지정하여 입력 활성화 상태를 명확히 보여줍니다.
