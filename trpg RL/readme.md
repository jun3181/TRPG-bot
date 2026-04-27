# TRPG RL 실험 가이드

이 문서는 `trpg RL` 폴더에서 실험 코드를 실행하는 방법을 정리합니다.

## 1) 준비

### Python 패키지 설치

```bash
pip install openai
```

> `experiment_test.py`는 OpenAI 연결 확인을 먼저 수행합니다.

### 환경변수 설정

```bash
export OPENAI_API_KEY="<YOUR_API_KEY>"
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
- OpenAI 패키지가 없으면 `pip install openai`로 설치하세요.
- API 호출 실패 시 키/모델/네트워크 상태를 확인하세요.
