# TRPG RL 실험 가이드

이 문서는 `trpg RL` 폴더에서 실험 코드를 실행하는 방법을 정리합니다.

## 1) 준비

### Python 패키지 설치

```bash
cd "trpg RL"
python -m pip install -r requirements.txt
```

> `experiment_test.py`는 OpenAI 연결 확인을 먼저 수행합니다.
> Windows PowerShell에서는 `py -m pip install -r requirements.txt`도 가능합니다.

### 환경변수 설정

```bash
export OPENAI_API_KEY="<YOUR_API_KEY>"
```

또는 `trpg RL/.env` 파일에 아래처럼 작성해도 자동으로 읽습니다.

```env
OPENAI_API_KEY=<YOUR_API_KEY>
OPENAI_MODEL=gpt-4.1-mini
```

Gemini를 사용하려면 아래처럼 설정하세요.

```env
TRPG_API_PROVIDER=gemini
GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
GEMINI_MODEL=gemini-1.5-flash
```

선택적으로 아래 실험 파라미터를 바꿀 수 있습니다.

```bash
export OPENAI_MODEL="gpt-4.1-mini"
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

1. GPT(OpenAI) 연결 확인
2. 콘솔에서 `!test_start` 입력
3. 연결이 성공한 경우 학습 시작
4. 학습 결과 출력 및 로그 파일 생성

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
- `OPENAI_API_KEY`가 비어 있으면 `experiment_test.py`는 학습을 시작하지 않습니다.
- Gemini 사용 시 `GEMINI_API_KEY`가 비어 있으면 API 연결이 실패합니다.
- `No module named 'openai'`가 뜨면 `python -m pip install -r requirements.txt`로 설치하세요.
- `Error code: 429 ... insufficient_quota`(OpenAI) 또는 `RESOURCE_EXHAUSTED`(Gemini)가 뜨면 API 호출 한도입니다. `experiment.py`는 해당 시점에서 실험을 즉시 종료합니다.
- API 호출 실패 시 키/모델/네트워크 상태를 확인하세요.
