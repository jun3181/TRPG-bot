# TRPG RL 실험 가이드

이 문서는 `trpg RL` 폴더에서 실험 코드를 실행하는 방법을 정리합니다.

## 1) 준비

### Python 패키지 설치

```bash
cd "trpg RL"
python -m pip install -r requirements.txt
```

> `experiment_test.py`는 API 연결 확인을 먼저 수행합니다.
> Windows PowerShell에서는 `py -m pip install -r requirements.txt`도 가능합니다.

### 환경변수 설정

기본(OpenAI) 사용 시:

```bash
export OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"
```

또는 `trpg RL/.env` 파일에 아래처럼 작성해도 자동으로 읽습니다.

```env
TRPG_API_PROVIDER=openai
OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>
OPENAI_MODEL=gpt-4.1-mini
```

Groq를 사용하려면 아래처럼 설정하세요.

```env
TRPG_API_PROVIDER=groq
GROQ_API_KEY=<YOUR_GROQ_API_KEY>
GROQ_MODEL=llama-3.1-8b-instant
```

Gemini를 사용하려면 아래처럼 설정하세요.

```env
TRPG_API_PROVIDER=gemini
GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
GEMINI_MODEL=gemini-1.5-flash
```

선택적으로 아래 실험 파라미터를 바꿀 수 있습니다.

```bash
export TRPG_EPISODES="1000"
export TRPG_LEARNING_RATE="0.1"
export TRPG_EPSILON_START="0.30"
export TRPG_EPSILON_END="0.05"
export TRPG_USE_OPENAI_FOR_TRAINING="false"
export TRPG_USE_OPENAI_FOR_FINAL_TEST="false"
```

## 2) 빠른 실행 (권장)

`trpg RL` 폴더로 이동한 뒤 실행합니다.

```bash
cd "trpg RL"
python experiment_test.py
```

실행 흐름:

1. API 연결 확인 (`TRPG_API_PROVIDER` 기준)
2. 일반 문장을 입력해 챗봇과 직접 대화하며 응답 품질/연결 상태 확인
3. 준비되면 `!test_start` 입력
4. 에포크/에피소드/학습률/epsilon/로그 주기를 입력
5. 학습 시작 후 결과 출력 및 로그 파일 생성

## 3) 기존 메인 스크립트 실행

아래 스크립트는 학습 후 최종 테스트(닉네임/입력)를 이어서 실행합니다.

```bash
cd "trpg RL"
python trpg_prompt_rl_experiment.py
```

## 4) 결과 파일

학습이 완료되면 아래 파일이 생성됩니다.

- `trpg RL/outputs/latest_prompt_pack.json`: 마지막 프롬프트 팩
- `trpg RL/outputs/prompt_packs.json`: 에피소드별 프롬프트 기록
- `trpg RL/outputs/episode_dialogues.csv`: 에피소드 대화 로그

## 5) 문제 해결

- `can't open file ... experiment_test.py`가 뜨면 현재 경로가 `trpg RL` 폴더인지 먼저 확인하세요.
- 파일명 오타(`experiemtn_test.py`, `experiement_test.py`)가 있으면 실행되지 않습니다.
- OpenAI 사용 시 `OPENAI_API_KEY`가 비어 있으면 연결이 실패합니다.
- Groq 사용 시 `GROQ_API_KEY`가 비어 있으면 연결이 실패합니다.
- Gemini 사용 시 `GEMINI_API_KEY`가 비어 있으면 연결이 실패합니다.
- `No module named 'openai'`가 뜨면 `python -m pip install -r requirements.txt`로 설치하세요.
- `Error code: 429 ... insufficient_quota`(OpenAI/Groq) 또는 `RESOURCE_EXHAUSTED`(Gemini)가 뜨면 API 호출 한도일 수 있습니다.
- API 호출 실패 시 키/모델/네트워크 상태를 확인하세요.
